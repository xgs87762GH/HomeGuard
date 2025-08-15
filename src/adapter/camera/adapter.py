from typing import Optional, Dict, Any

from pydantic import BaseModel

from src.adapter import BaseAdapter
from src.adapter.camera.tools import CameraTools
from src.adapter.camera.schemas.camera_schemas import CameraConfig



class CameraAdapter(BaseAdapter):
    name = "camera"

    def __init__(self, config: Optional[CameraConfig] = None):
        cfg = config or CameraConfig()
        self.config = cfg
        self.camera_tools = CameraTools(cfg=cfg)

    async def take_photo(self, filename=None):
        """
        Take photo
        """
        self.camera_tools.take_photo(filename=filename)
        # return CameraResp(status="success", message="Photo taken successfully")
        return {"status": "success", "message": "Photo taken successfully"}

    async def record_video(self, filename=None, duration=10):
        """
        Record video
        """
        self.camera_tools.record_video(filename=filename, duration=duration)
        # return CameraResp(status="success", message="Video recorded successfully")
        return {"status": "success", "message": "Video recorded successfully"}

    async def set_camera_parameters(self, **kwargs):
        result = self.camera_tools.set_camera_parameters(**kwargs)
        # return CameraResp(status="success", message="Camera parameters set successfully", data=result["params"])
        return {"status": "success", "message": "Camera parameters set successfully", "data": result["params"]}
