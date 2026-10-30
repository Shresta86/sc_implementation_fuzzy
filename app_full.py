import numpy as np, pandas as pd, streamlit as st
import matplotlib.pyplot as plt
import fuzzy_core as fc

st.set_page_config(page_title="Fuzzy Logic AC Controller", layout="wide")
st.title("Fuzzy Logic AC Controller - Prototype")
st.caption("Re-implementation of Pagare et al., Energy Reports 14 (2025) 3014-3032 | Soft Computing")
tab1, tab2, tab3, tab4 = st.tabs(["Live controller", "Room simulation", "Rule base (50 rules)", "Paper check"])

# ---------------- Tab 1: live controller ----------------
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Inputs")
        dT = st.slider("Temperature difference (room - set-point, C)", -10.0, 30.0, 7.16, 0.1)
        hum = st.slider("Humidity (%)", 0.0, 100.0, 60.0, 1.0)
        volt = st.slider("Supply voltage (V)", 180.0, 240.0, 220.0, 1.0)
        out, fire = fc.infer(dT, hum, volt)
        st.subheader("Outputs")
        if np.isnan(out["compressor"]):
            st.warning("No rule fired for this input. Try values within the model ranges: temperature difference -10 to 30 C, humidity 0 to 100%, and voltage 180 to 240 V.")
        else:
            m1, m2 = st.columns(2)
            m1.metric("Compressor", f"{out['compressor']:.1f} %")
            m2.metric("Fan speed", f"{out['fan']:.0f} rpm")
            m3, m4 = st.columns(2)
            m3.metric("Mode (0=Dehum, 1=AC)", f"{out['mode']:.2f}")
            m4.metric("Fan direction", f"{out['direction']:.1f} deg")
            st.progress(min(max(out["compressor"] / 100, 0), 1.0), text="Compressor load")
            max_fire = max(fire, default=0.0)
            st.caption(f"Rule coverage: {sum(w > 0 for w in fire)} of {len(fire)} rules fire; strongest firing strength {max_fire:.2f}.")
            if max_fire < 0.05:
                st.warning("Only weakly activated rules contribute to this result. Treat it as an edge case.")
    with c2:
        fig, ax = plt.subplots(1, 3, figsize=(11, 3))
        for a, (name, mfs, x, val, lo, hi) in zip(ax, [
            ("Temp. difference", fc.TEMP, np.linspace(-10, 30, 401), dT, -10, 30),
            ("Humidity", fc.HUM, np.linspace(0, 100, 401), hum, 0, 100),
            ("Voltage", None, np.linspace(180, 240, 301), volt, 180, 240)]):
            if mfs:
                for k, p in mfs.items():
                    a.plot(x, fc.tri(x, *p), label=k)
            else:
                a.plot(x, [fc.volt_mf(v)["Low"] for v in x], label="Low")
                a.plot(x, [fc.volt_mf(v)["Regular"] for v in x], label="Regular")
            a.axvline(val, color="red", ls="--")
            a.set_title(name); a.set_xlim(lo, hi); a.legend(fontsize=6)
        plt.tight_layout(); st.pyplot(fig)
        fired = [(i + 1, *r[:3], round(w, 3)) for i, (w, r) in enumerate(zip(fire, fc.RULES)) if w > 0]
        st.markdown("**Rules fired (rule no., temp, humidity, voltage, strength)**")
        st.dataframe(pd.DataFrame(fired, columns=["Rule", "Temp", "Humidity", "Voltage", "Strength"]), hide_index=True)

# ---------------- Tab 2: room simulation ----------------
def simulate(ctrl, set_pt, t_out, t0, hum, volt, minutes, gain, loss=0.02, internal=0.1, cool=0.7):
    t, hist, comp_h, e, on = t0, [], [], 0.0, False
    for _ in range(minutes):
        if ctrl == "On/off thermostat":
            if t > set_pt + 1: on = True
            if t < set_pt - 1: on = False
            comp, fan = (100.0, 1400.0) if on else (0.0, 0.0)
        else:
            o, _ = fc.infer((t - set_pt) * gain, hum, volt)
            comp, fan = (0.0, 0.0) if np.isnan(o["compressor"]) else (o["compressor"], o["fan"])
        t += loss * (t_out - t) + internal - cool * comp / 100
        e += fc.energy_per_min(comp, fan, hum, volt) if comp > 0 else 0.0
        hist.append(t); comp_h.append(comp)
    return np.array(hist), np.array(comp_h), e

with tab2:
    st.subheader("On/off thermostat vs fuzzy controller (simple first-order room model)")
    a, b, c = st.columns(3)
    set_pt = a.slider("Set-point (C)", 18, 28, 24); t_out = a.slider("Outside temp (C)", 28, 45, 35)
    t0 = b.slider("Starting room temp (C)", 24, 38, 30); minutes = b.slider("Duration (min)", 60, 360, 180, 30)
    sim_hum = c.slider("Humidity (%)", 20, 100, 50, key="sh"); sim_volt = c.slider("Voltage (V)", 180, 240, 220, key="sv")
    gain = st.slider("Fuzzy input scaling (x error). 1 = paper's raw ranges", 1.0, 6.0, 5.0, 0.5,
                     help="Above about 7, the scaled error leaves the 40 C input range and no rule fires.")
    res, rows = {}, []
    for name, g in [("On/off thermostat", 1.0), ("Fuzzy (raw ranges)", 1.0), (f"Fuzzy (x{gain:g})", gain)]:
        h_, c_, e_ = simulate(name if name.startswith("On") else "fuzzy", set_pt, t_out, t0, sim_hum, sim_volt, minutes, g)
        res[name] = (h_, c_); s = h_[min(60, len(h_) - 1):]
        rows.append([name, round(e_), round(s.mean(), 2), round(abs(s - set_pt).mean(), 2), round(s.min(), 1), round(s.max(), 1)])
    base = rows[0][1]
    df = pd.DataFrame(rows, columns=["Controller", "Energy index", "Mean temp after 60 min", "Avg offset from set-point", "Min", "Max"])
    df.insert(2, "Energy vs on/off", [f"{100 * r[1] / base:.0f} %" for r in rows])
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.5))
    for n, (h_, c_) in res.items():
        ax[0].plot(h_, label=n); ax[1].plot(c_, label=n)
    ax[0].axhline(set_pt, color="k", ls=":"); ax[0].set_title("Room temperature (C)"); ax[0].set_xlabel("minutes"); ax[0].legend(fontsize=7)
    ax[1].set_title("Compressor speed (%)"); ax[1].set_xlabel("minutes")
    plt.tight_layout(); st.pyplot(fig); st.dataframe(df, hide_index=True)
    st.info("Simplified toy model for comparison only (dT/dt = 0.02(Tout - T) + 0.1 - 0.7 x compressor). "
            "Energy uses the paper's own formula. Not a validated building model.")

# ---------------- Tab 3: rule base ----------------
with tab3:
    st.subheader("All 50 rules from the paper")
    rb = pd.DataFrame([(i + 1, *r) for i, r in enumerate(fc.RULES)],
                      columns=["#", "Temp diff", "Humidity", "Voltage", "Compressor", "Fan", "Mode", "Direction"])
    st.dataframe(rb, hide_index=True, height=600)

# ---------------- Tab 4: validation ----------------
with tab4:
    st.subheader("Validation and edge cases")
    st.markdown("**Paper worked example**")
    o, f = fc.infer(7.16, 97, 220)
    st.table(pd.DataFrame({"Output": ["Compressor (%)", "Fan (rpm)", "Mode (0-1)", "Direction (deg)"],
                           "Paper reference": [67, 938, 0.352, 31.7],
                           "Prototype": [round(o["compressor"], 1), round(o["fan"]), round(o["mode"], 3), round(o["direction"], 1)],
                           "Absolute difference": [round(abs(o["compressor"] - 67), 1), round(abs(o["fan"] - 938), 1), round(abs(o["mode"] - 0.352), 3), round(abs(o["direction"] - 31.7), 1)]}))
    st.caption("Inputs: temperature difference 7.16 C, humidity 97%, voltage 220 V (paper Figs. 18-19). These are reference outputs, not an independent hardware validation.")
    st.markdown("**Boundary checks**")
    checks = [("Cold / dry / low voltage", -10, 0, 180), ("Hot / sticky / high voltage", 30, 100, 240)]
    rows = []
    for label, temp, humidity, voltage in checks:
        result, strengths = fc.infer(temp, humidity, voltage)
        rows.append([label, temp, humidity, voltage, sum(w > 0 for w in strengths), round(max(strengths, default=0), 2),
                     round(result["compressor"], 1), round(result["fan"]), round(result["mode"], 3), round(result["direction"], 1)])
    st.dataframe(pd.DataFrame(rows, columns=["Case", "Temp diff (C)", "Humidity (%)", "Voltage (V)", "Rules fired", "Strongest rule", "Compressor (%)", "Fan (rpm)", "Mode (0-1)", "Direction (deg)"]), hide_index=True)
    st.caption("Boundary checks show whether the model returns a result at the edges of its slider ranges; they are not paper reference cases.")
