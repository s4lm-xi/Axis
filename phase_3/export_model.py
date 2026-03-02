from xgboost import XGBClassifier
from micromlgen import port

model = XGBClassifier()
model.load_model("xgb_model.json")

classmap = {
  0: "assalamualaikum",
  1: "kayf_haluk",
  2: "mahowa_asmk"
}

c_code = port(model, classmap=classmap)

with open("model.h", "w") as f:
  f.write(c_code)

print("Wrote model.h")