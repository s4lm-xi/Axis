import RPi.GPIO as GPIO
import time
import mpu6050
import lightgbm as lgb
import numpy as np
import json

# --- CONFIGURATION ---
FLEX_PINS = [4, 17, 27, 22, 23]
BUTTON_GPIO = 26
SAMPLE_INTERVAL = 0.1  # seconds
WINDOW_DURATION = 3  # seconds
TARGET_SAMPLES = int(WINDOW_DURATION / SAMPLE_INTERVAL)  # e.g. 30
MODEL_PATH = "model_lightgbm.txt"
LABEL_MAP_PATH = "class_labels.json"

# --- LOAD LABEL MAPPING ---
try:
    with open(LABEL_MAP_PATH, 'r') as f:
        label_map = json.load(f)
    # Ensure keys are sorted and build a list
    LABEL_NAMES = [label_map[str(i)] for i in range(len(label_map))]
    print(f"Loaded {len(LABEL_NAMES)} label names from '{LABEL_MAP_PATH}'")
except Exception as e:
    raise RuntimeError(f"Failed to load label mapping: {e}")

# --- SETUP GPIO & SENSORS ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLEX_PINS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
mpu = mpu6050.mpu6050(0x68)

# --- LOAD MODEL ---
model = lgb.Booster(model_file=MODEL_PATH)
print(f"Loaded LightGBM model from {MODEL_PATH}")


def read_sensors():
    """Return (flex: list[int], accel: dict, gyro: dict)."""
    flex = [GPIO.input(pin) for pin in FLEX_PINS]
    accel = mpu.get_accel_data()
    gyro = mpu.get_gyro_data()
    return flex, accel, gyro


def record_window():
    """Record ~3 s of data at SAMPLE_INTERVAL; return list of samples."""
    samples = []
    start = time.time()
    while len(samples) < TARGET_SAMPLES:
        t, (flex, accel, gyro) = time.time() - start, read_sensors()
        samples.append({
            "timestamp": t,
            "flex": flex,
            "acc": accel,
            "gyro": gyro
        })
        time.sleep(SAMPLE_INTERVAL)
    return samples


def flatten_samples(samples):
    """
    samples: list of sample dicts as recorded by record_window()
    Each sample has keys: "flex" (list), "acc" (dict), "gyro" (dict)

    Returns: np.array of shape (1, 7) with summed features:
        [flex_sum, acc_x_sum, acc_y_sum, acc_z_sum,
         gyro_x_sum, gyro_y_sum, gyro_z_sum]
    """
    # Initialize sums
    flex_sum = 0
    acc_x_sum = 0
    acc_y_sum = 0
    acc_z_sum = 0
    gyro_x_sum = 0
    gyro_y_sum = 0
    gyro_z_sum = 0

    for s in samples:
        flex_sum += sum(s["flex"])
        acc_x_sum += s["acc"].get("x", 0)
        acc_y_sum += s["acc"].get("y", 0)
        acc_z_sum += s["acc"].get("z", 0)
        gyro_x_sum += s["gyro"].get("x", 0)
        gyro_y_sum += s["gyro"].get("y", 0)
        gyro_z_sum += s["gyro"].get("z", 0)

    features = np.array([[
        flex_sum,
        acc_x_sum, acc_y_sum, acc_z_sum,
        gyro_x_sum, gyro_y_sum, gyro_z_sum
    ]])
    return features


def predict_label(arr):
    """
    feature_vector: list or np.array of length 7
    returns: predicted class index (int), optionally name if LABEL_NAMES set
    """
    probs = model.predict(arr)[0]
    idx = int(np.argmax(probs))
    name = LABEL_NAMES[idx] if LABEL_NAMES else None
    return idx, name, probs[idx]


def wait_for_button_press():
    """Block until button goes LOW (pressed)."""
    print("Waiting for button press to start recording…")
    while True:
        if GPIO.input(BUTTON_GPIO) == GPIO.LOW:
            time.sleep(0.05)  # debounce
            if GPIO.input(BUTTON_GPIO) == GPIO.LOW:
                print("Button pressed! Recording…")
                return
        time.sleep(0.01)


def main():
    try:
        while True:
            # 1) Wait for button press
            wait_for_button_press()

            # 2) Record 3s window
            samples = record_window()
            features = flatten_samples(samples)

            # 3) Predict
            idx, name, conf = predict_label(features)
            if name:
                print(f"Predicted label: {name} (class {idx}, confidence {conf:.2f})")
            else:
                print(f"Predicted class index: {idx} (confidence {conf:.2f})")

            print("\n--- Ready for next gesture ---\n")

    except KeyboardInterrupt:
        print("Interrupted by user – exiting.")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
