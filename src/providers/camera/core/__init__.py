"""相机核心模块"""

from .camera_tools import CameraTools
from .codec_manager import CameraCodecManager
from .frame_processor import FrameProcessor
from .async_recorder import AsyncVideoRecorder
from .exceptions import (
    CameraToolsError,
    CodecNotFoundError,
    RecordingError,
    FrameProcessingError
)

__all__ = [
    'CameraTools',
    'CameraCodecManager',
    'FrameProcessor',
    'AsyncVideoRecorder',
    'CameraToolsError',
    'CodecNotFoundError',
    'RecordingError',
    'FrameProcessingError'
]