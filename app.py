import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
import time

st.set_page_config(layout="wide")

st.title("🌊 Distributed Flood Monitoring Dashboard")

# ---------------------------
# SESSION STATE
# ---------------------------
if "running" not in st.session_state:
    st.session_state.running = False

if "index" not in st.session_state:
    st.session_state.index = 0

# ---------------------------
# LOAD DB
# ---------------------------
def get_data():
    conn = sqlite3.connect("db.sqlite3")
    logs = pd.read_sql("SELECT * FROM logs", conn)
    metrics = pd.read_sql("SELECT * FROM metrics", conn)
    conn.close()
    return logs, metrics

logs, metrics = get_data()

if logs.empty:
    st.warning("Run backend first (main.py)")
    st.stop()

logs["date"] = logs["date"].astype(str)
metrics["date"] = metrics["date"].astype(str)

dates = sorted(logs["date"].unique())

# ---------------------------
# ADJACENCY
# ---------------------------
adjacency = {
    "Manila": ["Pasig"],
    "Pasig": ["Manila", "Marikina"],
    "Marikina": ["Pasig", "Quezon City"],
    "Quezon City": ["Marikina"]
}

# ---------------------------
# CONTROLS
# ---------------------------
c1, c2, c3 = st.columns(3)

if c1.button("▶ Start"):
    st.session_state.running = True

if c2.button("⏸ Pause"):
    st.session_state.running = False

if c3.button("🔄 Reset"):
    st.session_state.index = 0
    st.session_state.running = False

# ---------------------------
# PLAYBACK
# ---------------------------
if st.session_state.index < len(dates):

    date = dates[st.session_state.index]

    daily_logs = logs[logs["date"] == date]
    daily_metrics = metrics[metrics["date"] == date]

    city_status = dict(zip(daily_logs["city"], daily_logs["prediction"]))

    # ---------------------------
    # PRE ALERTS
    # ---------------------------
    pre_alerts = set()

    for city, pred in city_status.items():
        if pred == 1:
            for neighbor in adjacency.get(city, []):
                if city_status.get(neighbor, 0) == 0:
                    pre_alerts.add(neighbor)

    # ---------------------------
    # DATE
    # ---------------------------
    st.markdown(f"## 📅 {date}")

    # ---------------------------
    # FULL WIDTH MAP
    # ---------------------------
    st.markdown("### 📍 Flood Map")

    coords = {
        "Manila": (14.5995, 120.9842),
        "Pasig": (14.5764, 121.0851),
        "Marikina": (14.6507, 121.1029),
        "Quezon City": (14.6760, 121.0437)
    }

    m = folium.Map(
        location=[14.623043, 121.061996],
        zoom_start=12,
        tiles="OpenStreetMap"
    )

    css = """
    <style>
    .red {width:25px;height:25px;background:red;border-radius:50%;animation:blink 1s infinite;}
    .yellow {width:25px;height:25px;background:orange;border-radius:50%;animation:blink 1s infinite;}
    .green {width:20px;height:20px;background:green;border-radius:50%;}
    @keyframes blink {50%{opacity:0.3;}}
    </style>
    """
    m.get_root().html.add_child(folium.Element(css))

    for city, pred in city_status.items():
        lat, lon = coords[city]

        if pred == 1:
            icon = '<div class="red"></div>'
        elif city in pre_alerts:
            icon = '<div class="yellow"></div>'
        else:
            icon = '<div class="green"></div>'

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=icon),
            tooltip=city
        ).add_to(m)

    st_folium(m, width=900, height=450)

    # ---------------------------
    # ALERTS (BELOW MAP)
    # ---------------------------
    st.markdown("### 🚨 Alerts")

    col1, col2 = st.columns(2)

    # EDGE
    with col1:
        st.markdown("#### Edge Layer")
        for city, pred in city_status.items():
            if pred == 1:
                st.error(f"{city}: FLOOD")
            elif city in pre_alerts:
                st.warning(f"{city}: PRE-ALERT")
            else:
                st.success(f"{city}: SAFE")

    # FOG
    with col2:
        st.markdown("#### Fog Analysis")

        flood_count = sum(city_status.values())
        pre_alert_count = len(pre_alerts)

        if flood_count == 0 and pre_alert_count == 0:
            risk = "LOW"
        elif flood_count == 1 or pre_alert_count >= 2:
            risk = "MODERATE"
        elif flood_count >= 2 or (flood_count == 1 and pre_alert_count >= 2):
            risk = "HIGH"

        st.info(f"Regional Risk: {risk}")

        if pre_alerts:
            st.warning(f"Pre-alert: {', '.join(pre_alerts)}")

    # ---------------------------
    # METRICS
    # ---------------------------
    st.markdown("### 📊 System Metrics")

    if not daily_metrics.empty:
        m = daily_metrics.iloc[0]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Edge Latency", round(m["avg_edge_latency"], 4))
        m2.metric("Fog Latency", round(m["fog_latency"], 4))
        m3.metric("Transfers", int(m["resource_transfer"]))
        m4.metric("Accuracy", round(m["accuracy"], 2))

    # ---------------------------
    # AUTO PLAY
    # ---------------------------
    if st.session_state.running:
        time.sleep(3)
        st.session_state.index += 1
        st.rerun()

else:
    st.success("Simulation Complete")