#!/usr/bin/env python3
import os
import time
import json
import subprocess
import numpy as np

import RPi.GPIO as GPIO
import mpu6050
import lightgbm as lgb

# --- CONFIGURATION ---
FLEX_PINS       = [4, 17, 27, 22, 23]
BUTTON_GPIO     = 26
SAMPLE_INTERVAL = 0.1      # seconds
WINDOW_DURATION = 3        # seconds
TARGET_SAMPLES  = int(WINDOW_DURATION / SAMPLE_INTERVAL)  # e.g. 30

MODEL_PATH      = "model_lightgbm.txt"
LABEL_MAP_PATH  = "class_labels.json"

# Put your Bluetooth speaker MAC here (or leave as None to skip BT connect)
# Example: "AA:BB:CC:DD:EE:FF"
BT_MAC_ADDRESS = None

# Audio folder (expects files named exactly like label + .mp3)
AUDIO_FOLDER = "audios"

# Helper: command-line audio player. Uses mpg123 (install with apt if needed).
AUDIO_PLAYER_CMD = "mpg123"  # must be in PATH


# --- Load label mapping (index -> class name) ---
try:
    with open(LABEL_MAP_PATH, 'r') as f:
        label_map = json.load(f)
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


# ---------------- Bluetooth utilities ----------------
def _run_bluetoothctl_commands(commands, timeout=12):
    """
    Run a sequence of commands inside bluetoothctl and return stdout.
    """
    try:
        p = subprocess.Popen(['bluetoothctl'],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             text=True)
        input_data = "\n".join(commands) + "\nquit\n"
        out, err = p.communicate(input=input_data, timeout=timeout)
        return out + "\n" + err
    except subprocess.TimeoutExpired:
        p.kill()
        return "bluetoothctl: timeout expired"


def connect_bluetooth(mac_address, max_attempts=3):
    """
    Try to pair/trust/connect to the bluetooth device with given MAC.
    This is a best-effort wrapper around bluetoothctl.
    Returns True if connected, False otherwise.
    Note: may require root privileges and that the Pi has bluetooth enabled.
    """
    if not mac_address:
        print("No Bluetooth MAC address provided; skipping Bluetooth connection.")
        return False

    print(f"Attempting Bluetooth connection to {mac_address} ... (this may take a few seconds)")
    # Basic sequence: power on, agent on, default-agent, pair, trust, connect
    base_cmds = [
        "power on",
        "agent on",
        "default-agent",
        "scan off"  # ensure scan not interfering
    ]
    _run_bluetoothctl_commands(base_cmds)

    for attempt in range(1, max_attempts + 1):
        print(f"Bluetooth attempt {attempt}/{max_attempts} ...")
        cmds = [
            f"pair {mac_address}",
            f"trust {mac_address}",
            f"connect {mac_address}"
        ]
        out = _run_bluetoothctl_commands(cmds)
        # Look for evidence of success
        if "Connection successful" in out or "succeeded" in out or "Connection already exists" in out:
            print(f"Bluetooth: connected to {mac_address}")
            return True
        # Some devices show "Connection successful" while others show "Connected: yes" in info
        # Query info
        info_out = _run_bluetoothctl_commands([f"info {mac_address}"])
        if "Connected: yes" in info_out:
            print(f"Bluetooth: connected to {mac_address} (verified via info)")
            return True

        print(f"Bluetooth attempt {attempt} failed; output:\n{out}\n{info_out}")
        time.sleep(1.0)

    print(f"Bluetooth: failed to connect to {mac_address} after {max_attempts} attempts.")
    print("You may need to pair manually with bluetoothctl or a GUI and set the audio sink as default.")
    return False


# Optionally set default audio sink to bluetooth device (left as comment because systems vary).
# If you need this, you can call pactl commands after connecting; user-specific and may require
# parsing sink names. Example (not executed automatically here):
# subprocess.run(["pactl", "set-default-sink", "<sink_name>"])


# ---------------- Audio playback ----------------
def play_audio_file(path):
    """
    Play the audio file at `path` using subprocess to call a CLI player.
    Blocks until playback finishes. Uses mpg123 by default.
    """
    if not os.path.exists(path):
        print(f"Audio file does not exist: {path}")
        return False

    # Try to call mpg123 (quiet mode -q)
    try:
        subprocess.run([AUDIO_PLAYER_CMD, "-q", path], check=True)
        return True
    except FileNotFoundError:
        print(f"Audio player '{AUDIO_PLAYER_CMD}' not found. Install mpg123 or change AUDIO_PLAYER_CMD.")
    except subprocess.CalledProcessError as e:
        print(f"Audio player returned error: {e}")
    except Exception as e:
        print(f"Unexpected error while playing audio: {e}")
    return False


def play_audio_for_label(label_name):
    """
    Given a label_name string, look for audios/<label_name>.mp3 and play it.
    """
    # sanitize label_name to simple filename (avoid path traversal)
    safe_name = os.path.basename(label_name)
    mp3_path = os.path.join(AUDIO_FOLDER, f"{safe_name}.mp3")
    print(f"Playing audio for label '{label_name}' -> {mp3_path}")
    ok = play_audio_file(mp3_path)
    if not ok:
        print(f"Failed to play audio for '{label_name}'. Make sure file exists and mpg123 is installed.")


# ---------------- Sensor reading / ML helpers ----------------
def read_sensors():
    """Return (flex: list[int], accel: dict, gyro: dict)."""
    flex  = [GPIO.input(pin) for pin in FLEX_PINS]
    accel = mpu.get_accel_data()
    gyro  = mpu.get_gyro_data()
    return flex, accel, gyro


def record_window():
    """Record ~WINDOW_DURATION seconds of data at SAMPLE_INTERVAL; return list of samples."""
    samples = []
    start   = time.time()
    while len(samples) < TARGET_SAMPLES:
        t = time.time() - start
        flex, accel, gyro = read_sensors()
        samples.append({
            "timestamp": t,
            "flex":      flex,
            "acc":       accel,
            "gyro":      gyro
        })
        time.sleep(SAMPLE_INTERVAL)
    return samples


def flatten_samples(samples):
    """
    samples: list of sample dicts as recorded by record_window()
    Each sample has keys: "flex" (list), "acc" (dict), "gyro" (dict)

    Returns:
        np.array of shape (1,7) with summed features:
        [flex_sum, acc_x_sum, acc_y_sum, acc_z_sum, gyro_x_sum, gyro_y_sum, gyro_z_sum]
    """
    flex_sum = 0
    acc_x_sum = 0.0
    acc_y_sum = 0.0
    acc_z_sum = 0.0
    gyro_x_sum = 0.0
    gyro_y_sum = 0.0
    gyro_z_sum = 0.0

    for s in samples:
        flex_sum += sum(s["flex"])
        acc_x_sum += float(s["acc"].get("x", 0))
        acc_y_sum += float(s["acc"].get("y", 0))
        acc_z_sum += float(s["acc"].get("z", 0))
        gyro_x_sum += float(s["gyro"].get("x", 0))
        gyro_y_sum += float(s["gyro"].get("y", 0))
        gyro_z_sum += float(s["gyro"].get("z", 0))

    features = np.array([[flex_sum, acc_x_sum, acc_y_sum, acc_z_sum, gyro_x_sum, gyro_y_sum, gyro_z_sum]])
    return features


def predict_label(arr):
    """
    arr: np.array shape (1, n_features)
    returns: predicted class index (int), name (str or None), confidence (float)
    """
    # LightGBM multiclass predict returns a matrix: (n_samples, n_classes)
    preds = model.predict(arr)
    # Ensure shape stable
    if preds.ndim == 1:
        # single-dim outputs (unlikely for multiclass), treat as single-prob
        idx = int(np.argmax(preds))
        conf = float(preds[idx]) if len(preds) > idx else float(preds.max())
    else:
        probs = preds[0]
        idx = int(np.argmax(probs))
        conf = float(probs[idx])
    name = LABEL_NAMES[idx] if LABEL_NAMES and 0 <= idx < len(LABEL_NAMES) else None
    return idx, name, conf


def wait_for_button_press():
    """Block until button goes LOW (pressed)."""
    print("Waiting for button press to start recording…")
    try:
        while True:
            if GPIO.input(BUTTON_GPIO) == GPIO.LOW:
                time.sleep(0.05)  # debounce
                if GPIO.input(BUTTON_GPIO) == GPIO.LOW:
                    print("Button pressed! Recording…")
                    return
            time.sleep(0.01)
    except KeyboardInterrupt:
        raise


# ---------------- Main loop ----------------
def main():
    try:
        # Attempt Bluetooth connection at start (best-effort)
        if BT_MAC_ADDRESS:
            connected = connect_bluetooth(BT_MAC_ADDRESS)
            if not connected:
                print("Bluetooth speaker not connected; audio may play on local output instead.")
        else:
            print("No BT MAC set; skipping Bluetooth connect. Set BT_MAC_ADDRESS variable to enable.")

        while True:
            # 1) Wait for your press
            wait_for_button_press()

            # 2) Record WINDOW_DURATION window
            samples = record_window()
            features = flatten_samples(samples)

            # 3) Predict
            idx, name, conf = predict_label(features)
            if name:
                print(f"Predicted label: {name}  (class {idx}, confidence {conf:.2f})")
                # Play audio for this label (non-blocking decision: this call blocks while audio plays)
                play_audio_for_label(name)
            else:
                print(f"Predicted class index: {idx}  (confidence {conf:.2f})")

            print("\n--- Ready for next gesture ---\n")

    except KeyboardInterrupt:
        print("Interrupted by user – exiting.")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()

