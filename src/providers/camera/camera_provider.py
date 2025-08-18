from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from src.providers.base_provider import BaseProvider
from src.providers.camera.tools import CameraTools
from src.providers.camera.schemas.camera_schemas import CameraConfig
from src.core.config.setting import LOGGER


class CameraProvider(BaseProvider):
    """Camera functionality provider"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Camera Provider

        Args:
            config: Dictionary configuration or None
        """
        super().__init__()

        self.name = "camera"

        # Convert dict config to CameraConfig object
        if config is None:
            config = {}

        try:
            # Handle Path conversion for output_dir if it's a string
            if 'output_dir' in config and isinstance(config['output_dir'], str):
                config['output_dir'] = Path(config['output_dir'])

            # Handle resolution tuple conversion
            if 'resolution' in config and isinstance(config['resolution'], list):
                config['resolution'] = tuple(config['resolution'])

            # Create CameraConfig from dict
            if isinstance(config, dict):
                self.config = CameraConfig(**config)
            elif isinstance(config, CameraConfig):
                self.config = config
            else:
                self.config = CameraConfig()

        except Exception as e:
            LOGGER.error(f"Failed to create CameraConfig: {e}")
            # Fallback to default config
            self.config = CameraConfig()

        # Initialize camera tools
        try:
            self.camera_tools = CameraTools(cfg=self.config)
        except Exception as e:
            LOGGER.error(f"Failed to initialize CameraTools: {e}")
            self.camera_tools = None

    async def take_photo(self, filename: Optional[str] = None):
        """Take photo with current camera settings"""
        if not self.camera_tools:
            return {"status": "error", "message": "Camera tools not initialized"}

        try:
            # Remove await since take_photo is synchronous
            result = self.camera_tools.take_photo(filename=filename)
            return {"status": "success", "message": "Photo taken successfully", "data": result}
        except Exception as e:
            LOGGER.error(f"Failed to take photo: {e}")
            return {"status": "error", "message": f"Failed to take photo: {str(e)}"}

    async def record_video(self, filename: Optional[str] = None, duration: int = 10):
        """Record video with current camera settings"""
        if not self.camera_tools:
            return {"status": "error", "message": "Camera tools not initialized"}

        try:
            params = {
                "filename": filename,
                "duration": duration
            }

            # Remove await since record_video is synchronous
            result = self.camera_tools.record_video(**params)
            return {"status": "success", "message": "Video recorded successfully", "data": result}
        except Exception as e:
            LOGGER.error(f"Failed to record video: {e}")
            return {"status": "error", "message": f"Failed to record video: {str(e)}"}

    async def set_camera_parameters(self, **kwargs):
        """Set camera parameters dynamically"""
        if not self.camera_tools:
            return {"status": "error", "message": "Camera tools not initialized"}

        try:
            # Update config with new parameters
            valid_params = {}
            config_fields = self.config.model_fields.keys()

            for key, value in kwargs.items():
                if key in config_fields:
                    setattr(self.config, key, value)
                    valid_params[key] = value

            # Remove await since set_camera_parameters is synchronous
            result = self.camera_tools.set_camera_parameters(**valid_params)

            return {
                "status": "success",
                "message": "Camera parameters updated successfully",
                "data": {
                    "updated_params": valid_params,
                    "current_config": self.config.model_dump()
                }
            }
        except Exception as e:
            LOGGER.error(f"Failed to set camera parameters: {e}")
            return {"status": "error", "message": f"Failed to set parameters: {str(e)}"}

    async def get_current_config(self):
        """Get current camera configuration"""
        return {
            "status": "success",
            "data": self.config.dict()
        }

    async def get_capabilities(self):
        """Get camera capabilities"""
        return [
            "take_photo",
            "record_video",
            "set_camera_parameters",
            "get_current_config"
        ]

    async def health_check(self) -> bool:
        """Check camera health"""
        if not self.camera_tools:
            return False

        try:
            # Remove await if is_camera_available is also synchronous
            return self.camera_tools.is_camera_available()
        except Exception as e:
            LOGGER.error(f"Camera health check failed: {e}")
            return False
