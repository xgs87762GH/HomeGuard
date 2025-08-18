"""编解码器管理模块"""

import tempfile
from pathlib import Path
from typing import Tuple, Optional, List
import platform

import cv2
import numpy as np

from src.core.config.setting import LOGGER
from .exceptions import CodecNotFoundError


class CameraCodecManager:
    """管理编解码器的单独类"""

    _PLATFORM_CODECS = {
        "windows": [
            ("mp4v", "MP4V"),
            ("MJPG", "Motion JPEG"),
            ("XVID", "XviD"),
            ("WMV2", "Windows Media Video"),
            ("I420", "Raw YUV"),
        ],
        "darwin": [  # macOS
            ("mp4v", "MP4V"),
            ("H264", "H.264"),
            ("MJPG", "Motion JPEG"),
        ],
        "linux": [
            ("XVID", "XviD"),
            ("mp4v", "MP4V"),
            ("MJPG", "Motion JPEG"),
            ("H264", "H.264"),
        ]
    }

    def __init__(self):
        self._system = platform.system().lower()
        self._codecs = self._get_platform_codecs()

    def _get_platform_codecs(self) -> List[Tuple]:
        """获取平台优化的编解码器列表"""
        codec_info = self._PLATFORM_CODECS.get(self._system, self._PLATFORM_CODECS["linux"])
        return [(cv2.VideoWriter.fourcc(*codec), name) for codec, name in codec_info]

    def test_codec(self, codec_fourcc: int, path: Path, fps: float, size: Tuple[int, int]) -> Optional[cv2.VideoWriter]:
        """测试编解码器是否可用"""
        with tempfile.NamedTemporaryFile(suffix=path.suffix, delete=False) as tmp_file:
            temp_path = Path(tmp_file.name)

        try:
            writer = cv2.VideoWriter(str(temp_path), codec_fourcc, fps, size)

            if writer.isOpened():
                # 测试写入虚拟帧
                dummy_frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
                writer.write(dummy_frame)
                writer.release()

                # 创建实际的写入器
                final_writer = cv2.VideoWriter(str(path), codec_fourcc, fps, size)
                if final_writer.isOpened():
                    return final_writer

        except Exception as e:
            LOGGER.debug("编解码器测试失败: %s", e)
        finally:
            # 确保清理临时文件
            if temp_path.exists():
                temp_path.unlink()

        return None

    def create_writer(self, path: Path, fps: float, size: Tuple[int, int]) -> cv2.VideoWriter:
        """创建优化的视频写入器"""
        LOGGER.debug("测试编解码器...")

        for codec_fourcc, codec_name in self._codecs:
            try:
                LOGGER.debug("测试编解码器: %s", codec_name)
                writer = self.test_codec(codec_fourcc, path, fps, size)
                if writer:
                    LOGGER.info("成功初始化编解码器: %s", codec_name)
                    return writer
            except Exception as e:
                LOGGER.debug("编解码器 %s 失败: %s", codec_name, e)
                continue

        # 最后尝试AVI格式
        return self._try_avi_fallback(path, fps, size)

    def _try_avi_fallback(self, path: Path, fps: float, size: Tuple[int, int]) -> cv2.VideoWriter:
        """AVI格式回退"""
        avi_path = path.with_suffix('.avi')
        LOGGER.warning("所有MP4编解码器失败，尝试AVI格式: %s", avi_path)

        avi_codecs = [
            (cv2.VideoWriter.fourcc(*"MJPG"), "Motion JPEG"),
            (cv2.VideoWriter.fourcc(*"XVID"), "XviD"),
            (cv2.VideoWriter.fourcc(*"I420"), "Raw YUV"),
        ]

        for codec_fourcc, codec_name in avi_codecs:
            try:
                writer = self.test_codec(codec_fourcc, avi_path, fps, size)
                if writer:
                    LOGGER.info("回退到AVI格式，编解码器: %s", codec_name)
                    return writer
            except Exception as e:
                LOGGER.debug("AVI编解码器 %s 失败: %s", codec_name, e)
                continue

        raise CodecNotFoundError("没有找到可用的编解码器")