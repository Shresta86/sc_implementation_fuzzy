"""Fuzzy logic controller for an air conditioner.
Re-implementation of Pagare et al., Energy Reports 14 (2025) 3014-3032.
Mamdani inference: min = AND, min = implication, max = aggregation, centroid defuzzification.
"""
import numpy as np

def tri(x, a, b, c):
    return np.maximum(np.minimum((x - a) / (b - a), (c - x) / (c - b)), 0.0)

# ---- Input membership functions (paper Figs. 5-7) ----
TEMP = {"TooCold": (-20, -10, 0), "Cold": (-10, 0, 10), "Warm": (0, 10, 20),
        "Hot": (10, 20, 30), "TooHot": (20, 30, 40)}
HUM = {"Dry": (-30, 0, 30), "Refreshing": (20, 35, 50), "Comfortable": (40, 55, 70),
       "Humid": (60, 75, 90), "Sticky": (80, 100, 120)}
def volt_mf(v):  # trapezoids (Fig. 5)
    low = float(np.clip((215 - v) / 15, 0, 1))
    reg = float(np.clip((v - 200) / 20, 0, 1))
    return {"Low": low, "Regular": reg}

# ---- Output universes and membership functions (Figs. 8-11) ----
LEVELS = ["Off", "VeryLow", "Low", "Medium", "Fast"]
COMP_X = np.linspace(0, 100, 501)
FAN_X = np.linspace(0, 1400, 701)
MODE_X = np.linspace(0, 1, 201)
DIR_X = np.linspace(0, 100, 501)
def _levels(x, peak):
    return {n: tri(x, (i - 1) * peak / 4, i * peak / 4, (i + 1) * peak / 4) for i, n in enumerate(LEVELS)}
COMP = _levels(COMP_X, 100)
FAN = _levels(FAN_X, 1400)
MODE = {"Dehumidifier": np.clip(1 - MODE_X, 0, 1), "AC": np.clip(MODE_X, 0, 1)}
DIRN = {"Towards": np.clip((80 - DIR_X) / 50, 0, 1), "Away": np.clip((DIR_X - 30) / 50, 0, 1)}

# ---- Rule base: the 50 rules printed in the paper, in order (rules 1-50) ----
# (temp, humidity, voltage) -> (compressor, fan, mode, direction)
_T = ["TooCold", "Cold", "Warm", "Hot", "TooHot"]
_H = ["Dry", "Refreshing", "Comfortable", "Humid", "Sticky"]
_REG = [  # rules 1-25
 ["Off,Off,AC,Away", "Off,Off,AC,Away", "Off,Off,AC,Away", "Off,VeryLow,AC,Away", "VeryLow,Low,Dehumidifier,Towards"],
 ["Off,Off,AC,Away", "Off,Off,AC,Away", "VeryLow,VeryLow,AC,Away", "VeryLow,Low,AC,Towards", "Low,Low,Dehumidifier,Towards"],
 ["VeryLow,VeryLow,AC,Away", "VeryLow,VeryLow,AC,Away", "Low,Low,AC,Away", "Medium,Medium,Dehumidifier,Towards", "Medium,Medium,Dehumidifier,Towards"],
 ["Low,Low,AC,Away", "Medium,Medium,AC,Away", "Medium,Medium,AC,Towards", "Fast,Fast,Dehumidifier,Towards", "Fast,Fast,Dehumidifier,Towards"],
 ["Medium,Medium,AC,Away", "Medium,Medium,AC,Towards", "Fast,Fast,Dehumidifier,Towards", "Fast,Fast,Dehumidifier,Towards", "Fast,Fast,Dehumidifier,Towards"]]
_LOW = [  # rules 26-50
 ["Off,Off,AC,Away", "Off,Off,AC,Away", "Off,Off,AC,Away", "Off,Off,AC,Away", "Off,Off,Dehumidifier,Towards"],
 ["Off,Off,AC,Away", "VeryLow,VeryLow,AC,Towards", "Off,Off,AC,Away", "VeryLow,VeryLow,AC,Towards", "VeryLow,Low,Dehumidifier,Towards"],
 ["VeryLow,VeryLow,AC,Away", "VeryLow,VeryLow,AC,Towards", "VeryLow,VeryLow,AC,Towards", "Low,Low,Dehumidifier,Towards", "Low,Low,Dehumidifier,Towards"],
 ["Low,Low,AC,Away", "Low,Low,AC,Towards", "Medium,Medium,AC,Towards", "Medium,Medium,Dehumidifier,Towards", "Fast,Fast,Dehumidifier,Towards"],
 ["Medium,Medium,AC,Towards", "Medium,Medium,AC,Towards", "Medium,Medium,Dehumidifier,Towards", "Fast,Fast,Dehumidifier,Towards", "Fast,Fast,Dehumidifier,Towards"]]
RULES = []
for volt, table in (("Regular", _REG), ("Low", _LOW)):
    for ti, t in enumerate(_T):
        for hi, h in enumerate(_H):
            RULES.append((t, h, volt, *table[ti][hi].split(",")))

def _centroid(x, agg):
    s = agg.sum()
    return float((x * agg).sum() / s) if s > 0 else float("nan")

def infer(dT, hum, volt):
    """Return outputs dict + firing strength of each rule."""
    mt = {k: float(tri(dT, *v)) for k, v in TEMP.items()}
    mh = {k: float(tri(hum, *v)) for k, v in HUM.items()}
    mv = volt_mf(volt)
    fire = [min(mt[t], mh[h], mv[v]) for t, h, v, *_ in RULES]
    # per output: strongest firing per output set (max aggregation), then clipped MFs
    def agg(idx, mfs, x):
        strength = {k: 0.0 for k in mfs}
        for w, r in zip(fire, RULES):
            strength[r[idx]] = max(strength[r[idx]], w)
        a = np.zeros_like(x)
        for k, s in strength.items():
            a = np.maximum(a, np.minimum(s, mfs[k]))
        return a
    out = {"compressor": _centroid(COMP_X, agg(3, COMP, COMP_X)),
           "fan": _centroid(FAN_X, agg(4, FAN, FAN_X)),
           "mode": _centroid(MODE_X, agg(5, MODE, MODE_X)),
           "direction": _centroid(DIR_X, agg(6, DIRN, DIR_X))}
    return out, fire

def energy_per_min(comp, fan, hum, volt):
    """Energy index from the paper's formula (arbitrary units)."""
    return 0.08 * comp ** 1.1 + 0.05 * fan / 1400 + 0.003 * hum ** 1.05 - 0.002 * (volt - 200)

if __name__ == "__main__":
    o, f = infer(7.16, 97, 220)
    print("Paper example (7.16, 97, 220) -> expected 67 / 938 / 0.352 / 31.7")
    print({k: round(v, 3) for k, v in o.items()}, "rules fired:", sum(w > 0 for w in f), "of", len(RULES))