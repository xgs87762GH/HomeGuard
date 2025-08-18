"""相机工具主入口文件"""

# 为了保持向后兼容，重新导出主要类
from .core.camera_tools import CameraTools
from .core import (
    CameraCodecManager,
    FrameProcessor,
    AsyncVideoRecorder
)

__all__ = [
    'CameraTools',
    'CameraCodecManager', 
    'FrameProcessor',
    'AsyncVideoRecorder'
]