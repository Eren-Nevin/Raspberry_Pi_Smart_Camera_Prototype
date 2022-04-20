from abc import ABC
from pathlib import PosixPath
from typing import Dict

class AbstractCamera(ABC):
    def start(self):
        pass

    def stop(self):
        pass

    def close(self):
        pass

    def capture_still_to_local_file(self, filename: PosixPath):
        pass

    def start_recording_to_local_file(self, filename: PosixPath):
        pass

    def stop_recording(self):
        pass
