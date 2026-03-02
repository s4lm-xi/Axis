import os, time, csv
import serial
import time

PORT = "/dev/ttyACM0"   # change if needed
BAUD = 115200

SAMPLE_HZ = 50
DURATION_S = 2.0        # 2 seconds per trial
REST_S = 1.0
TRIALS = 10

LABELS = {
  0: "assalamualaikum",
  1: "kayf_haluk",
  2: "mahowa_asmk"
}

OUT_DIR = "dataset_runs"
os.makedirs(OUT_DIR, exist_ok=True)

# def wait_ready(ser):
#   while True:
#     line = ser.readline().decode(errors="ignore").strip()
#     if line:
#       print(line)
#     if line == "READY":
#       return
def wait_ready(ser, timeout_s=10):
    # Opening the port may reset the board; force a clean reset
    ser.dtr = False
    time.sleep(0.2)
    ser.reset_input_buffer()
    ser.dtr = True

    t0 = time.time()
    while time.time() - t0 < timeout_s:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print("DEV:", line)     # show everything for debugging
        if line == "READY":
            return True
    return False

def record_one_label(label_id: int):
  name = LABELS[label_id]
  out_path = os.path.join(OUT_DIR, f"{label_id}_{name}.csv")

  with serial.Serial(PORT, BAUD, timeout=1) as ser:
    ser.reset_input_buffer()
    wait_ready(ser)

    with open(out_path, "w", newline="") as f:
      w = csv.writer(f)
      w.writerow(["t_ms","label","f1","f2","f3","f4","f5","ax","ay","az","gx","gy","gz"])

      for trial in range(TRIALS):
        print(f"\n[{name}] Trial {trial+1}/{TRIALS} ...")
        ser.write(f"START {label_id}\n".encode())

        # wait for OK
        while True:
          line = ser.readline().decode(errors="ignore").strip()
          if line.startswith("OK START"):
            break

        t_end = time.time() + DURATION_S
        while time.time() < t_end:
          line = ser.readline().decode(errors="ignore").strip()
          if not line or line.startswith("OK") or line.startswith("CSV"):
            continue
          parts = line.split(",")
          if len(parts) == 13:
            w.writerow(parts)

        ser.write(b"STOP\n")
        time.sleep(REST_S)

  print("Saved:", out_path)

if __name__ == "__main__":
  for lab in [0,1,2]:
    record_one_label(lab)