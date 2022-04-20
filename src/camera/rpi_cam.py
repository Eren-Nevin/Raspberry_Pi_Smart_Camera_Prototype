from picamera import PiCamera

from pathlib import PosixPath
from time import sleep

from .abs_camera import AbstractCamera

class Camera(AbstractCamera):
    def __init__(self):
        self.camera = PiCamera()

    def start(self):
        self.camera.start_preview()
        self.camera.preview.window = 0, 0, 0, 0
        sleep(2)

    def stop(self):
        self.camera.stop_preview()

    def close(self):
        self.camera.close()

    def capture_still_to_local_file(self, filename: PosixPath):
        return self.camera.capture(filename.as_posix())
