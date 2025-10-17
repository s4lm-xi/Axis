import os
import csv
import time
import numpy as np
import RPi.GPIO as GPIO
import mpu6050

# --- CONFIGURATION ---
FLEX_PINS       = [4, 17, 27, 22, 23]
BUTTON_GPIO     = 26
SAMPLE_INTERVAL = 0.1      # seconds
WINDOW_DURATION = 3        # seconds
TARGET_SAMPLES  = int(WINDOW_DURATION / SAMPLE_INTERVAL)  # e.g. 30
CSV_FILE        = "data.csv"

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLEX_PINS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# MPU6050 setup
mpu = mpu6050.mpu6050(0x68)

# Ask once per session for the class label
label = input("Enter the label for this class: ").strip()

def read_sensors():
    """Return (flex: list[int], accel: dict, gyro: dict)."""
    flex  = [GPIO.input(pin) for pin in FLEX_PINS]
    accel = mpu.get_accel_data()
    gyro  = mpu.get_gyro_data()
    return flex, accel, gyro

def record_window():
    """Record ~3 s of data at SAMPLE_INTERVAL; return list of samples."""
    print("Recording for 3 seconds...")
    samples = []
    start   = time.time()
    while len(samples) < TARGET_SAMPLES:
        flex, acc, gyro = read_sensors()
        samples.append({"flex": flex, "acc": acc, "gyro": gyro})
        time.sleep(SAMPLE_INTERVAL)
    print("Recording complete.")
    return samples

def flatten_samples(samples):
    """
    From the window samples, compute summed features:
    [flex_sum, acc_x_sum, acc_y_sum, acc_z_sum, gyro_x_sum, gyro_y_sum, gyro_z_sum]
    """
    flex_sum = sum(sum(s["flex"]) for s in samples)
    acc_x_sum = sum(s["acc"].get("x", 0) for s in samples)
    acc_y_sum = sum(s["acc"].get("y", 0) for s in samples)
    acc_z_sum = sum(s["acc"].get("z", 0) for s in samples)
    gyro_x_sum = sum(s["gyro"].get("x", 0) for s in samples)
    gyro_y_sum = sum(s["gyro"].get("y", 0) for s in samples)
    gyro_z_sum = sum(s["gyro"].get("z", 0) for s in samples)
    return [flex_sum, acc_x_sum, acc_y_sum, acc_z_sum, gyro_x_sum, gyro_y_sum, gyro_z_sum]

def append_to_csv(row):
    """Append a single row (label + features) to CSV_FILE, creating it with header if needed."""
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            # write header
            header = ["label",
                      "flex_sum",
                      "acc_x_sum", "acc_y_sum", "acc_z_sum",
                      "gyro_x_sum", "gyro_y_sum", "gyro_z_sum"]
            writer.writerow(header)
        writer.writerow(row)
    print(f"Appended to {CSV_FILE}: {row}")

def button_callback():
    """On button press: record window, sum it, and append to CSV with the session label."""
    samples = record_window()
    features = flatten_samples(samples)
    append_to_csv([label] + features)

print("Ready. Press the button to record a 3‑second window.")

try:
    button_was_pressed = False

    while True:
        if GPIO.input(BUTTON_GPIO) == GPIO.LOW:
            if not button_was_pressed:
                button_callback()
                button_was_pressed = True
        else:
            button_was_pressed = False

        time.sleep(0.01)  # Small delay to prevent CPU overuse

except KeyboardInterrupt:
    print("\nExiting and cleaning up GPIO.")

finally:
    GPIO.cleanup()
    GPIO.cleanup()
