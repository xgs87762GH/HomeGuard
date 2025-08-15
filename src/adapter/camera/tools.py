import datetime
from contextlib import contextmanager
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import cv2

from src.adapter.camera.driver.camera import Cv2Camera
from src.adapter.camera.schemas.camera_schemas import CameraConfig
from src.core.config.setting import LOGGER, CFG


class CameraTools:
    """High-level camera utilities built on top of Cv2Camera."""

    CODECS = (
        cv2.VideoWriter_fourcc(*"mp4v"),
        cv2.VideoWriter_fourcc(*"XVID"),
        cv2.VideoWriter_fourcc(*"MJPG"),
    )

    def __init__(self, cfg: CameraConfig):
        self._live_cam = None
        self.cfg = cfg
        self.cfg.output_dir.mkdir(exist_ok=True)
        LOGGER.debug("CameraTools initialized with output_dir=%s", cfg.output_dir)

    @contextmanager
    def camera(self):
        """Acquire and release the camera. Keeps a weak ref for runtime parameter updates."""
        cam = Cv2Camera(self.cfg)
        cam.open()
        self._live_cam = cam
        LOGGER.debug("Camera opened")
        try:
            yield cam
        finally:
            cam.close()
            self._live_cam = None
            LOGGER.debug("Camera closed")

    def _writer(self, path: Path, fps: float, size: Tuple[int, int]) -> cv2.VideoWriter:
        for codec in self.CODECS:
            w = cv2.VideoWriter(str(path), codec, fps, size)
            if w.isOpened():
                LOGGER.debug("Codec %s selected for %s", codec, path.name)
                return w
        raise RuntimeError("No available codec")

    def build_image_path(self, filename: Optional[str] = None, prefix: str = "", ext: str = ".jpg") -> Path:
        """Generate save path for images or videos."""
        now = datetime.datetime.now()
        date_folder = (
                self.cfg.output_dir / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
        )
        date_folder.mkdir(parents=True, exist_ok=True)

        if filename:
            return date_folder / filename

        fname = f"{CFG.app.name}_{now.strftime('%Y%m%d_%H%M%S')}{prefix}{ext}"
        path = date_folder / fname
        LOGGER.debug("Auto-generated file path: %s", path)
        return path

    # ---------- Public API ----------
    def take_photo(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Capture a single frame and save to disk."""
        with self.camera() as cam:
            ok, frame = cam.read()
            if not ok:
                LOGGER.error("Failed to read frame")
                raise RuntimeError("Cannot read frame")

            path = self.build_image_path(filename=filename)
            if not cv2.imwrite(str(path), frame):
                LOGGER.error("Failed to write image to %s", path)
                raise RuntimeError(f"Cannot write image to {path}")

            LOGGER.info("Photo saved to %s", path)
            return {"status": "success", "file": str(path)}

    def record_video(
            self,
            filename: Optional[str] = None,
            duration: int = 10,
            fps: int = 30,
    ) -> Dict[str, Any]:
        """Record video for the specified duration."""
        with self.camera() as cam:
            ok, frame = cam.read()
            if not ok:
                LOGGER.error("Failed to read initial frame")
                raise RuntimeError("Cannot read frame")

            h, w = frame.shape[:2]
            path = self.build_image_path(filename=filename, ext=".mp4")
            out = self._writer(path, fps, (w, h))

            LOGGER.info("Recording %s fps x %d s video to %s", fps, duration, path.name)
            for _ in range(fps * duration):
                ok, frm = cam.read()
                if ok:
                    out.write(frm)
            out.release()

            LOGGER.info("Video saved to %s", path)
            return {"status": "success", "file": str(path)}

    def set_camera_parameters(self, **kwargs) -> Dict[str, Any]:
        """Update configuration and apply changes immediately if the camera is open."""
        for k, v in kwargs.items():
            if v is not None:
                setattr(self.cfg, k, v)
                LOGGER.debug("Updated %s = %s", k, v)

        if self._live_cam:
            self._live_cam.update_params(self.cfg)
            LOGGER.debug("Runtime camera parameters refreshed")

        return {"status": "success", "params": self.cfg.__dict__}
