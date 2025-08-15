from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Optional
from pathlib import Path

from src.core.config.setting import LOGGER, project_root


@dataclass
class CameraConfig:
    camera_id: int = 0
    resolution: Optional[Tuple[int, int]] = None
    contrast: int = 50
    brightness: int = 50
    saturation: int = 80
    sharpness: int = 4
    iso: int = 200
    exposure: int = 0
    output_dir: Path = field(
        default_factory=lambda: project_root() / "output"
    )

    def __post_init__(self) -> None:
        LOGGER.info("CameraConfig initialized: camera_id=%s, resolution=%s, output_dir=%s",
                    self.camera_id, self.resolution, self.output_dir)
