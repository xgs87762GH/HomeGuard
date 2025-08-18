"""异步视频录制模块"""

import threading
import queue
from typing import Optional

import cv2
import numpy as np

from src.core.config.setting import LOGGER
from .exceptions import RecordingError


class AsyncVideoRecorder:
    """异步视频录制器"""

    def __init__(self, buffer_size: int = 30):
        self.buffer_size = buffer_size
        self._frame_buffer: queue.Queue = queue.Queue(maxsize=buffer_size)
        self._recording = False
        self._writer_thread: Optional[threading.Thread] = None
        self._writer: Optional[cv2.VideoWriter] = None
        self._lock = threading.Lock()

    def start_recording(self, writer: cv2.VideoWriter):
        """开始异步录制"""
        with self._lock:
            if self._recording:
                raise RecordingError("录制已在进行中")

            self._writer = writer
            self._recording = True
            self._writer_thread = threading.Thread(
                target=self._writer_worker,
                daemon=True
            )
            self._writer_thread.start()

    def add_frame(self, frame: np.ndarray, timeout: float = 1.0) -> bool:
        """添加帧到缓冲区"""
        try:
            self._frame_buffer.put(frame.copy(), timeout=timeout)
            return True
        except queue.Full:
            LOGGER.warning("帧缓冲区已满，丢弃帧")
            return False

    def stop_recording(self, timeout: float = 5.0):
        """停止录制"""
        with self._lock:
            if not self._recording:
                return

            self._recording = False

            # 发送终止信号
            try:
                self._frame_buffer.put(None, timeout=1.0)
            except queue.Full:
                pass

            # 等待线程结束
            if self._writer_thread:
                self._writer_thread.join(timeout=timeout)
                if self._writer_thread.is_alive():
                    LOGGER.warning("录制线程未能及时结束")

            # 释放写入器
            if self._writer:
                try:
                    self._writer.release()
                except Exception as e:
                    LOGGER.error("释放视频写入器失败: %s", e)
                finally:
                    self._writer = None

    def _writer_worker(self):
        """异步写入器工作线程"""
        try:
            while self._recording or not self._frame_buffer.empty():
                try:
                    frame = self._frame_buffer.get(timeout=1.0)
                    if frame is None:  # 终止信号
                        break

                    if self._writer:
                        self._writer.write(frame)

                    self._frame_buffer.task_done()

                except queue.Empty:
                    continue
                except Exception as e:
                    LOGGER.error("写入帧时出错: %s", e)
        except Exception as e:
            LOGGER.error("录制线程异常: %s", e)

    @property
    def is_recording(self) -> bool:
        """检查是否正在录制"""
        return self._recording

    @property
    def buffer_usage(self) -> dict:
        """获取缓冲区使用情况"""
        return {
            "current_size": self._frame_buffer.qsize(),
            "max_size": self.buffer_size,
            "usage_percent": (self._frame_buffer.qsize() / self.buffer_size) * 100
        }
