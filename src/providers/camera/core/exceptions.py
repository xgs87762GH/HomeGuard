"""相机工具相关的自定义异常"""

class CameraToolsError(Exception):
    """相机工具基础异常"""
    pass

class CodecNotFoundError(CameraToolsError):
    """编解码器未找到异常"""
    pass

class RecordingError(CameraToolsError):
    """录制相关异常"""
    pass

class FrameProcessingError(CameraToolsError):
    """帧处理异常"""
    pass