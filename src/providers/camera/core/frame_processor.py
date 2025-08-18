"""帧处理模块"""

import cv2
import numpy as np

from src.core.config.setting import LOGGER
from .exceptions import FrameProcessingError


class FrameProcessor:
    """帧处理工具类"""

    @staticmethod
    def enhance_frame_quality(frame: np.ndarray) -> np.ndarray:
        """轻量级帧质量增强"""
        try:
            # 双边滤波器降噪同时保留边缘
            enhanced = cv2.bilateralFilter(frame, 5, 50, 50)

            # 轻微锐化增强细节
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]], dtype=np.float32)
            sharpening_kernel = kernel * 0.1 + np.eye(3, dtype=np.float32) * 0.9
            enhanced = cv2.filter2D(enhanced, -1, sharpening_kernel)

            return enhanced.astype(np.uint8)
        except Exception as e:
            LOGGER.warning("帧增强失败，使用原始帧: %s", e)
            return frame

    @staticmethod
    def apply_brightness_contrast(frame: np.ndarray, brightness: int = 0, contrast: float = 1.0) -> np.ndarray:
        """应用亮度和对比度调整"""
        try:
            # 应用亮度和对比度调整
            adjusted = cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness)
            return adjusted
        except Exception as e:
            raise FrameProcessingError(f"亮度对比度调整失败: {e}")

    @staticmethod
    def apply_histogram_equalization(frame: np.ndarray) -> np.ndarray:
        """应用直方图均衡化"""
        try:
            # 转换为YUV色彩空间
            yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
            # 对Y通道进行直方图均衡化
            yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
            # 转换回BGR
            return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        except Exception as e:
            raise FrameProcessingError(f"直方图均衡化失败: {e}")