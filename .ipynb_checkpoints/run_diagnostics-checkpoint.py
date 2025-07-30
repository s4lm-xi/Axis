import RPi.GPIO as GPIO
import time
from mpu6050 import mpu6050
import os

# ----------------- Setup -----------------
FLEX_SENSORS = [4, 17, 27, 22, 23]
SENSOR_NAMES = {
    4: "Flex Sensor 1",
    17: "Flex Sensor 2",
    27: "Flex Sensor 3",
    22: "Flex Sensor 4",
    23: "Flex Sensor 5"
}
BUTTON_GPIO = 26
MPU_ADDR = 0x68

GPIO.setmode(GPIO.BCM)
GPIO.setup(FLEX_SENSORS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

sensor = mpu6050(MPU_ADDR)

# ----------------- Helper Functions -----------------

def clear():
    os.system('clear')

def print_title(title):
    print(f"\n{'='*50}")
    print(f"{title.center(50)}")
    print(f"{'='*50}")

def print_result(name, status):
    status_text = "PASS ✅" if status else "FAIL ❌"
    print(f"{name.ljust(30)} --> {status_text}")

# ----------------- Flex Sensor Test -----------------

def test_flex_sensors(duration=5):
    print_title("Testing Flex Sensors")
    start_time = time.time()
    status_tracker = {pin: False for pin in FLEX_SENSORS}

    while time.time() - start_time < duration:
        for sensor in FLEX_SENSORS:
            value = GPIO.input(sensor)
            bent = value == GPIO.LOW
            status_tracker[sensor] |= bent
            state = "BENT   " if bent else "STRAIGHT"
            print(f"{SENSOR_NAMES[sensor]}: {state}")
        print("-" * 30)
        time.sleep(0.5)

    all_passed = all(status_tracker.values())
    for sensor in FLEX_SENSORS:
        print_result(SENSOR_NAMES[sensor], status_tracker[sensor])
    return all_passed

# ----------------- MPU6050 Test -----------------

def test_mpu6050(duration=5):
    print_title("Testing MPU6050 (Accelerometer, Gyroscope, Temp)")
    start_time = time.time()
    success = True

    while time.time() - start_time < duration:
        try:
            accel = sensor.get_accel_data()
            gyro = sensor.get_gyro_data()
            temp = sensor.get_temp()

            print("Accelerometer → X:{:.2f}, Y:{:.2f}, Z:{:.2f}".format(
                accel['x'], accel['y'], accel['z']))
            print("Gyroscope     → X:{:.2f}, Y:{:.2f}, Z:{:.2f}".format(
                gyro['x'], gyro['y'], gyro['z']))
            print(f"Temperature   → {temp:.2f} °C")
            print("-" * 30)
        except Exception as e:
            print(f"Error: {e}")
            success = False
        time.sleep(0.5)

    print_result("MPU6050 Test", success)
    return success

# ----------------- Button Test -----------------

def test_button(duration=5):
    print_title("Testing Button on GPIO 26")
    print("→ Press and release the button within 5 seconds...")

    start_time = time.time()
    pressed = False

    while time.time() - start_time < duration:
        value = GPIO.input(BUTTON_GPIO)
        if value == GPIO.LOW:
            print("Button: PRESSED")
            pressed = True
        else:
            print("Button: Released")
        print("-" * 10)
        time.sleep(0.5)

    print_result("Button Press Test", pressed)
    return pressed

# ----------------- Main Diagnostic Runner -----------------

def run_diagnostics():
    clear()
    print_title("Raspberry Pi Sensor Diagnostic Test")

    tests = {
        "Flex Sensors": test_flex_sensors(),
        "MPU6050": test_mpu6050(),
        "Button Test": test_button()
    }

    print_title("Test Summary")
    for name, result in tests.items():
        print_result(name, result)

    print("\nDone.\n")

# ----------------- Start -----------------

try:
    run_diagnostics()
except KeyboardInterrupt:
    print("\nInterrupted by user.")
finally:
    GPIO.cleanup()
