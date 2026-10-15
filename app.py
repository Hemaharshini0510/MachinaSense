
import streamlit as st
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix
)

st.set_page_config(
    page_title="MachinaSense",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ MachinaSense")
st.subheader("Intelligent Industrial Fault Detection")
st.caption(
    "Predictive maintenance using simulated vibration "
    "and temperature telemetry"
)

rng = np.random.default_rng(42)
FEATURES = ["Temperature (C)", "Vibration (mm/s)"]

# Generate normal machine operating data
def normal_data(n, random_state=None):
    r = np.random.default_rng(random_state)
    return pd.DataFrame({
        "Temperature (C)": r.normal(65, 4, n),
        "Vibration (mm/s)": r.normal(2.0, 0.4, n)
    })

# Training data contains only normal operation
train = normal_data(1000, 10)

model = IsolationForest(
    n_estimators=150,
    contamination=0.08,
    random_state=42
)
model.fit(train[FEATURES])

# Independent test set with known fault labels
test_normal = normal_data(150, 20)
test_fault = normal_data(50, 30)

# Inject simulated overheating and vibration faults
test_fault.loc[:24, "Temperature (C)"] += 25
test_fault.loc[25:, "Vibration (mm/s)"] += 3.5

test = pd.concat(
    [test_normal, test_fault], ignore_index=True
)
test["Actual Fault"] = [0] * 150 + [1] * 50

# Add a few missing readings, then interpolate
for col in FEATURES:
    test.loc[[12, 79], col] = np.nan

test[FEATURES] = (
    test[FEATURES].interpolate(limit_direction="both")
)

test["Predicted Fault"] = (
    model.predict(test[FEATURES]) == -1
).astype(int)

# Held-out evaluation
y_true = test["Actual Fault"]
y_pred = test["Predicted Fault"]

st.markdown("### Model evaluation — held-out test data")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Accuracy", f"{accuracy_score(y_true, y_pred):.1%}")
m2.metric("Precision", f"{precision_score(y_true, y_pred, zero_division=0):.1%}")
m3.metric("Recall", f"{recall_score(y_true, y_pred, zero_division=0):.1%}")
m4.metric("F1 score", f"{f1_score(y_true, y_pred, zero_division=0):.1%}")

st.caption(
    "Synthetic benchmark only. Metrics may vary with the "
    "data-generation assumptions and are not industrial validation."
)

st.markdown("### Machine monitoring")

scenario = st.selectbox(
    "Select a simulated operating condition",
    ["Normal operation", "Bearing vibration fault",
     "Overheating fault", "Combined fault"]
)

live = normal_data(60, 100)
live["Minute"] = np.arange(1, 61)

if scenario in ["Bearing vibration fault", "Combined fault"]:
    live.loc[40:, "Vibration (mm/s)"] += 3.5

if scenario in ["Overheating fault", "Combined fault"]:
    live.loc[40:, "Temperature (C)"] += 25

live["Predicted Fault"] = (
    model.predict(live[FEATURES]) == -1
)

latest = live.iloc[-1]
fault = bool(latest["Predicted Fault"])

c1, c2, c3 = st.columns(3)
c1.metric("Temperature", f"{latest['Temperature (C)']:.1f} °C")
c2.metric("Vibration", f"{latest['Vibration (mm/s)']:.2f} mm/s")
c3.metric("Operating status", "CHECK MACHINE" if fault else "NORMAL")

st.markdown("#### Temperature trend")
st.line_chart(
    live.set_index("Minute")[["Temperature (C)"]]
)

st.markdown("#### Vibration trend")
st.line_chart(
    live.set_index("Minute")[["Vibration (mm/s)"]]
)

if fault:
    st.error("Anomaly detected: inspect the machine.")
    reasons = []
    if latest["Temperature (C)"] > 80:
        reasons.append("Elevated temperature")
    if latest["Vibration (mm/s)"] > 3.5:
        reasons.append("Elevated vibration")
    if not reasons:
        reasons.append(
            "Combined sensor pattern differs from normal training data"
        )
    st.write("Evidence:", ", ".join(reasons))
    st.write("Recommended action: inspect the machine and verify readings.")
else:
    st.success("No anomaly detected in the latest simulated reading.")

st.markdown("#### Telemetry and alert history")
display = live.copy()
display["Status"] = np.where(
    display["Predicted Fault"], "Anomaly", "Normal"
)
st.dataframe(display.tail(15), use_container_width=True)

st.download_button(
    "Download telemetry report (CSV)",
    data=display.to_csv(index=False),
    file_name="machinasense_report.csv",
    mime="text/csv"
)
