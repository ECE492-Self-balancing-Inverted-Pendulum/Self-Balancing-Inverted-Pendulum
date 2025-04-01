import threading
import time
from IMU_reader import IMUReader

class IMUReaderThreaded(IMUReader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = False
        self.latest_data = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def _update_loop(self):
        while self.running:
            self.latest_data = self.get_imu_data()
            time.sleep(1 / self.SAMPLE_RATE)

    def get_latest_data(self):
        return self.latest_data