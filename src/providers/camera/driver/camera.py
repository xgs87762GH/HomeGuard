from typing import Tuple, Optional

import cv2

from src.providers.camera.schemas.camera_schemas import CameraConfig


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

    def _set_buffer_size(self, buffer_size: int) -> bool:
        """设置相机缓冲区大小以减少延迟和内存使用"""
        if not self._cap or not self._cap.isOpened():
            return False

        try:
            from src.core.config.setting import LOGGER

            # 获取缓冲区属性常量
            buffer_prop = getattr(cv2, 'CAP_PROP_BUFFERSIZE', 38)

            # 设置缓冲区大小
            success = self._cap.set(buffer_prop, buffer_size)

            if success:
                # 验证设置是否生效
                actual_size = self._cap.get(buffer_prop)
                LOGGER.debug("Camera buffer size set to %d (actual: %.0f)", buffer_size, actual_size)
                return True
            else:
                LOGGER.warning("Failed to set camera buffer size to %d", buffer_size)
                return False

        except Exception as e:
            from src.core.config.setting import LOGGER
            LOGGER.warning("Exception while setting buffer size: %s", e)
            return False

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

        self._set_buffer_size(cfg.buffer_size)
        self.cfg = cfg

    def set_property(self, prop: int, value: float) -> bool:
        """设置相机属性的通用方法"""
        if not self._cap or not self._cap.isOpened():
            return False
        try:
            return self._cap.set(prop, value)
        except Exception:
            return False

    def get_property(self, prop: int) -> float:
        """获取相机属性值"""
        if not self._cap or not self._cap.isOpened():
            return -1
        try:
            return self._cap.get(prop)
        except Exception:
            return -1
