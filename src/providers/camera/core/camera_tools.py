"""主要的相机工具类"""

import datetime
import gc
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, Any, Generator

import cv2

from src.providers.camera.driver.camera import Cv2Camera
from src.providers.camera.schemas.camera_schemas import CameraConfig
from src.core.config.setting import LOGGER, CFG

from .codec_manager import CameraCodecManager
from .frame_processor import FrameProcessor
from .async_recorder import AsyncVideoRecorder


class CameraTools:
    """高级相机工具，基于Cv2Camera构建，带内存优化"""

    def __init__(self, cfg: CameraConfig):
        self._live_cam: Optional[Cv2Camera] = None
        self.cfg = cfg
        self.cfg.output_dir.mkdir(exist_ok=True)

        # 初始化组件
        self._codec_manager = CameraCodecManager()
        self._frame_processor = FrameProcessor()
        self._recorder = AsyncVideoRecorder(buffer_size=30)

        LOGGER.debug("CameraTools初始化完成，输出目录=%s", cfg.output_dir)

    @contextmanager
    def camera(self):
        """获取和释放相机。保持弱引用以便运行时参数更新"""
        cam = Cv2Camera(self.cfg)
        cam.open()
        self._live_cam = cam

        try:
            self._apply_camera_optimizations(cam)
            yield cam
        finally:
            cam.close()
            self._live_cam = None
            LOGGER.debug("相机已关闭")

    def _apply_camera_optimizations(self, cam: Cv2Camera) -> None:
        """应用相机性能优化设置"""
        try:
            # 验证缓冲区设置
            buffer_prop = getattr(cv2, 'CAP_PROP_BUFFERSIZE', 38)
            current_buffer = cam.get_property(buffer_prop)
            LOGGER.debug("相机打开，配置缓冲区大小: %d (实际: %.0f)",
                         self.cfg.buffer_size, current_buffer)

            # 先获取相机支持的分辨率和帧率
            width = cam.get_property(cv2.CAP_PROP_FRAME_WIDTH)
            height = cam.get_property(cv2.CAP_PROP_FRAME_HEIGHT)
            current_fps = cam.get_property(cv2.CAP_PROP_FPS)

            LOGGER.debug("相机当前设置: %dx%d @ %.1f fps", width, height, current_fps)

            # 保守的优化设置，避免强制不支持的参数
            optimizations = [
                ('CAP_PROP_BUFFERSIZE', 1, '缓冲区大小'),  # 减少缓冲区避免延迟
                ('CAP_PROP_AUTO_EXPOSURE', 1, '自动曝光'),  # 启用自动曝光
            ]

            # 只有当前帧率过低时才尝试设置
            if current_fps < 15:
                optimizations.append(('CAP_PROP_FPS', 25, '帧率'))

            for prop_name, value, description in optimizations:
                try:
                    prop = getattr(cv2, prop_name, None)
                    if prop is not None:
                        if cam.set_property(prop, value):
                            actual = cam.get_property(prop)
                            LOGGER.debug("设置 %s 为 %s (实际: %.1f)", description, value, actual)
                        else:
                            LOGGER.debug("设置 %s 失败", description)
                except Exception as e:
                    LOGGER.debug("设置 %s 时出错: %s", description, e)

        except Exception as e:
            LOGGER.warning("相机优化验证失败: %s", e)


    def _frame_generator(self, cam: Cv2Camera, duration: int, fps: int) -> Generator:
        """内存高效的帧生成器，带精确时间控制"""
        # 获取相机实际帧率，避免强制帧率导致跳帧
        actual_fps = cam.get_property(cv2.CAP_PROP_FPS)
        if actual_fps > 0:
            fps = min(fps, int(actual_fps))  # 使用较小的帧率
            LOGGER.debug("调整帧率为 %d (相机支持: %.1f)", fps, actual_fps)

        frame_interval = 1.0 / fps
        start_time = time.time()
        frame_count = 0
        target_frames = fps * duration
        skip_count = 0

        while frame_count < target_frames:
            current_time = time.time()
            expected_time = start_time + frame_count * frame_interval

            # 适度的帧率控制，避免过于严格
            if current_time < expected_time:
                sleep_time = expected_time - current_time
                if sleep_time > 0.001:  # 只有超过1ms才sleep
                    time.sleep(sleep_time)

            ok, frame = cam.read()
            if not ok or frame is None:
                skip_count += 1
                LOGGER.warning("跳过无效帧 (%d)", skip_count)
                if skip_count > 10:  # 连续失败太多次就退出
                    LOGGER.error("连续帧读取失败，停止录制")
                    break
                continue

            # 重置跳帧计数
            skip_count = 0

            # 应用质量增强
            frame = self._frame_processor.enhance_frame_quality(frame)
            yield frame

            frame_count += 1

            # 定期垃圾回收管理内存
            if frame_count % 30 == 0:
                gc.collect()
                LOGGER.debug("已录制 %d/%d 帧", frame_count, target_frames)



    def build_image_path(self, filename: Optional[str] = None, prefix: str = "", ext: str = ".jpg") -> Path:
        """生成图片或视频的保存路径"""
        now = datetime.datetime.now()
        date_folder = (
                self.cfg.output_dir / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
        )
        date_folder.mkdir(parents=True, exist_ok=True)

        if filename:
            return date_folder / filename

        fname = f"{CFG.app.name}_{now.strftime('%Y%m%d_%H%M%S')}{prefix}{ext}"
        path = date_folder / fname
        LOGGER.debug("自动生成文件路径: %s", path)
        return path

    # ---------- 公共API ----------
    def take_photo(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """捕获单帧并保存到磁盘，带增强质量"""
        with self.camera() as cam:
            # 增加预热时间，让相机稳定
            LOGGER.debug("相机预热中...")
            for i in range(10):  # 增加到10帧
                ok, frame = cam.read()
                if ok:
                    # 检查帧是否为空或异常
                    if frame is not None and frame.size > 0:
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        brightness = cv2.mean(gray)[0]
                        LOGGER.debug("预热帧 %d: 亮度=%.1f", i, brightness)

                        # 如果亮度正常，提前结束预热
                        if 30 < brightness < 200:
                            break
                time.sleep(0.1)  # 给相机更多时间稳定

            ok, frame = cam.read()
            if not ok or frame is None or frame.size == 0:
                LOGGER.error("读取帧失败")
                raise RuntimeError("无法读取帧")

            # 检查帧质量
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = cv2.mean(gray)[0]
            LOGGER.debug("最终帧亮度: %.1f", brightness)

            if brightness < 10 or brightness > 250:
                LOGGER.warning("帧亮度异常: %.1f，可能是白屏或黑屏", brightness)

            # 应用质量增强
            frame = self._frame_processor.enhance_frame_quality(frame)

            path = self.build_image_path(filename=filename)

            # 高质量JPEG编码参数
            encode_params = [
                getattr(cv2, 'IMWRITE_JPEG_QUALITY', 1), 95,
                getattr(cv2, 'IMWRITE_JPEG_OPTIMIZE', 65), 1
            ]

            if not cv2.imwrite(str(path), frame, encode_params):
                LOGGER.error("写入图片到 %s 失败", path)
                raise RuntimeError(f"无法写入图片到 {path}")

            LOGGER.info("照片保存到 %s", path)
            return {"status": "success", "file": str(path), "brightness": brightness}



    def record_video(
            self,
            filename: Optional[str] = None,
            duration: int = 10,
            fps: int = 30,
    ) -> Dict[str, Any]:
        """录制指定时长的视频，带内存优化"""
        with self.camera() as cam:
            # 预热相机
            for _ in range(3):
                cam.read()

            ok, frame = cam.read()
            if not ok:
                LOGGER.error("读取初始帧失败")
                raise RuntimeError("无法读取帧")

            h, w = frame.shape[:2]
            path = self.build_image_path(filename=filename, ext=".mp4")

            try:
                writer = self._codec_manager.create_writer(path, fps, (w, h))
                LOGGER.info("录制 %s fps x %d s 视频到 %s", fps, duration, path.name)

                # 开始异步录制
                self._recorder.start_recording(writer)

                # 生成并缓冲帧
                for frame in self._frame_generator(cam, duration, fps):
                    if not self._recorder.add_frame(frame):
                        LOGGER.warning("帧添加失败，可能缓冲区已满")

            except Exception as e:
                LOGGER.error("录制过程中出错: %s", e)
                raise
            finally:
                # 清理
                self._recorder.stop_recording()
                gc.collect()  # 强制垃圾回收

            LOGGER.info("视频保存到 %s", path)
            return {"status": "success", "file": str(path)}

    def set_camera_parameters(self, **kwargs) -> Dict[str, Any]:
        """更新配置并立即应用更改（如果相机已打开）"""
        buffer_size_changed = False

        for k, v in kwargs.items():
            if v is not None:
                old_value = getattr(self.cfg, k, None)
                setattr(self.cfg, k, v)
                LOGGER.debug("更新 %s = %s (原值: %s)", k, v, old_value)

                if k == 'buffer_size':
                    buffer_size_changed = True

        if self._live_cam:
            self._live_cam.update_params(self.cfg)

            if buffer_size_changed:
                LOGGER.info("运行时缓冲区大小已更新为 %d", self.cfg.buffer_size)

            LOGGER.debug("运行时相机参数已刷新")

        return {"status": "success", "params": self.cfg.__dict__}

    def get_memory_usage(self) -> Dict[str, Any]:
        """获取当前内存使用统计"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "buffer_size": self._recorder._frame_buffer.qsize(),
                "buffer_max": self._recorder.buffer_size
            }
        except ImportError:
            return {"error": "psutil不可用"}

    def __del__(self):
        """析构函数，确保资源清理"""
        try:
            self._recorder.stop_recording()
        except:
            pass