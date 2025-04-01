  import time
  import board
  import adafruit_icm20x
  import numpy as np
  import imufusion
  import csv
  import json
  import sys
  
  class IMUFusion:
      def __init__(self, sample_rate=100, calibration_file="calibration.json", log_file="imu_log.csv"):
          self.sample_rate = sample_rate
          self.calibration_file = calibration_file
          self.log_file = log_file
          self.prev_time = time.time()
          
          self._load_calibration()
          self._initialize_imu()
          self._initialize_fusion()
          self._initialize_logging()
  
      def _load_calibration(self):
          try:
              with open(self.calibration_file, "r") as f:
                  calibration_data = json.load(f)
              print("Loaded calibration values from calibration.json.")
          except FileNotFoundError:
              print("Calibration file not found! Using default offsets.")
              calibration_data = {
                  "gyro_offset": [0, 0, 0],
                  "accel_offset": [0, 0, 0],
                  "mag_offset": [0, 0, 0]
              }
          
          self.gyro_offset = np.array(calibration_data["gyro_offset"])
          self.accel_offset = np.array(calibration_data["accel_offset"])
          self.mag_offset = np.array(calibration_data["mag_offset"])
  
      def _initialize_imu(self):
          self.i2c = board.I2C()
          self.icm = adafruit_icm20x.ICM20948(self.i2c)
  
      def _initialize_fusion(self):
          self.offset = imufusion.Offset(self.sample_rate)
          self.ahrs = imufusion.Ahrs()
          self.ahrs.settings = imufusion.Settings(
              imufusion.CONVENTION_NWU,
              0.8,
              2000,
              10,
              10,
              1 * self.sample_rate,
          )
      
      def _initialize_logging(self):
          self.log_file_handle = open(self.log_file, "w", newline="")
          self.csv_writer = csv.writer(self.log_file_handle)
          self.csv_writer.writerow(["Timestamp", "Roll", "Pitch", "Yaw"])
  
      def read_sensors(self):
          accel = np.array(self.icm.acceleration) - self.accel_offset
          gyro = np.array(self.icm.gyro) * (180 / np.pi) - self.gyro_offset
          mag = np.array(self.icm.magnetic) - self.mag_offset
  
          accel = np.clip(accel, -9.81, 9.81)
          alpha = 0.8
          gyro = alpha * gyro + (1 - alpha) * self.offset.update(gyro)
  
          curr_time = time.time()
          dt = max(curr_time - self.prev_time, 1e-3)
          self.prev_time = curr_time
  
          self.ahrs.update_no_magnetometer(gyro, accel, dt)
          euler = np.clip(self.ahrs.quaternion.to_euler(), -180, 180)
          
          return curr_time, euler
  
      def log_data(self, timestamp, euler):
          self.csv_writer.writerow([timestamp, euler[0], euler[1], euler[2]])
          self.log_file_handle.flush()
      
      def get_angles(self):
          """Returns the latest roll, pitch, and yaw angles."""
          _, euler = self.read_sensors()
          return euler
  
      def run(self):
          print("IMU Sensor Fusion Running... Press Ctrl+C to stop.")
          try:
              while True:
                  timestamp, euler = self.read_sensors()
                  self.log_data(timestamp, euler)
                  sys.stdout.write(f"\rRoll: {euler[0]:.2f}° | Pitch: {euler[1]:.2f}° | Yaw: {euler[2]:.2f}°   ")
                  sys.stdout.flush()
                  time.sleep(1 / self.sample_rate)
          except KeyboardInterrupt:
              print("\nExiting IMU Fusion Program...")
              self.log_file_handle.close()
  
  if __name__ == "__main__":
      imu_fusion = IMUFusion()
      imu_fusion.run()
