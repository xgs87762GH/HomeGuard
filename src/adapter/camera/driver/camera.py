from typing import Tuple, Optional

import cv2

from src.adapter.camera.schemas.camera_schemas import CameraConfig


class AbstractCamera:
    def open(self) -> None: ...

    def close(self) -> None: ...

    def read(self) -> Tuple[bool, cv2.Mat]: ...

    def set_params(self, cfg: CameraConfig) -> None: ...


class Cv2Camera(AbstractCamera):
    def __init__(self, cfg: CameraConfig):
        self.cfg = cfg
        self._cap: Optional[cv2.VideoCapture] = None

    def open(self) -> None:
        if self._cap and self._cap.isOpened():
            return
        self._cap = cv2.VideoCapture(self.cfg.camera_id)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera {self.cfg.camera_id}")
        self._apply_params()

    def close(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None

    def read(self) -> Tuple[bool, cv2.Mat]:
        return self._cap.read()

    def _apply_params(self) -> None:
        cap = self._cap
        w, h = self.cfg.resolution or (1920, 1080)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        cap.set(cv2.CAP_PROP_CONTRAST, self.cfg.contrast)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, self.cfg.brightness)
        cap.set(cv2.CAP_PROP_SATURATION, self.cfg.saturation)
        cap.set(cv2.CAP_PROP_SHARPNESS, self.cfg.sharpness)
        cap.set(cv2.CAP_PROP_ISO_SPEED, self.cfg.iso)
        cap.set(cv2.CAP_PROP_EXPOSURE, self.cfg.exposure)

    def update_params(self, cfg: CameraConfig) -> None:
        """在相机已打开的情况下刷新参数"""
        if not self._cap or not self._cap.isOpened():
            return
        w, h = cfg.resolution or (1920, 1080)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self._cap.set(cv2.CAP_PROP_CONTRAST, cfg.contrast)
        self._cap.set(cv2.CAP_PROP_BRIGHTNESS, cfg.brightness)
        self._cap.set(cv2.CAP_PROP_SATURATION, cfg.saturation)
        self._cap.set(cv2.CAP_PROP_SHARPNESS, cfg.sharpness)
        self._cap.set(cv2.CAP_PROP_ISO_SPEED, cfg.iso)
        self._cap.set(cv2.CAP_PROP_EXPOSURE, cfg.exposure)

