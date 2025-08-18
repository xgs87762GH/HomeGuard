from typing import Optional, Tuple
from pathlib import Path

from pydantic import BaseModel, Field, validator
import logging

LOGGER = logging.getLogger(__name__)


def project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent.parent.parent.parent


class CameraConfig(BaseModel):
    """Camera configuration schema - 进一步降低曝光的优化版本"""

    # 基础设备配置
    camera_id: int = Field(default=0, description="Camera device ID")
    resolution: Optional[Tuple[int, int]] = Field(
        default=None,
        description="Camera resolution (width, height) - None for auto"
    )

    # 曝光控制参数 - 进一步降低曝光
    contrast: int = Field(default=25, description="Contrast level (进一步降低)")
    brightness: int = Field(default=-10, description="Brightness level (负值降低亮度)")
    saturation: int = Field(default=50, description="Saturation level (降低)")
    sharpness: int = Field(default=1, description="Sharpness level (最小值)")
    iso: int = Field(default=80, description="ISO sensitivity (更低ISO)")
    exposure: int = Field(default=-5, description="Exposure compensation (更低曝光)")

    # 性能和质量参数
    buffer_size: int = Field(default=1, description="Frame buffer size")
    quality: int = Field(default=85, description="Image quality (0-100)")
    fps: int = Field(default=25, description="Video frame rate")

    # 曝光控制参数
    auto_exposure: float = Field(default=0.25, description="曝光模式 (0.25=手动)")
    gain: int = Field(default=0, description="增益控制 (0=最小增益)")
    auto_wb: bool = Field(default=True, description="自动白平衡")

    output_dir: Path = Field(
        default_factory=lambda: project_root() / "output",
        description="Output directory for photos and videos"
    )

    @validator('exposure')
    def validate_exposure(cls, v):
        """验证曝光补偿范围"""
        if v > 0:
            LOGGER.warning("曝光补偿为正值 (%d)，可能导致过曝", v)
        elif v < -8:
            LOGGER.warning("曝光补偿过低 (%d)，可能导致过暗", v)
        return v

    @validator('brightness')
    def validate_brightness(cls, v):
        """验证亮度范围"""
        if v > 0:
            LOGGER.warning("亮度设置为正值 (%d)，可能导致过曝", v)
        return v

    @validator('output_dir', pre=True)
    def validate_output_dir(cls, v):
        """Ensure output_dir is a Path object"""
        if isinstance(v, str):
            return Path(v)
        return v

    def model_post_init(self, __context) -> None:
        """Post initialization hook"""
        LOGGER.info(
            "CameraConfig initialized: camera_id=%s, exposure=%s, brightness=%s",
            self.camera_id, self.exposure, self.brightness
        )

    def get_safe_exposure_config(self) -> dict:
        """获取安全的曝光配置字典"""
        return {
            "auto_exposure": self.auto_exposure,
            "exposure": self.exposure,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "gain": self.gain,
            "auto_wb": self.auto_wb,
            "saturation": self.saturation,
            "iso": self.iso
        }

    class Config:
        arbitrary_types_allowed = True