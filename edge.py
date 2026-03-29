import joblib
import os
import time

def edge_node(city_name, df, feature_cols, queue):

    model = joblib.load("edge_flood_model.pkl")
    scaler = joblib.load("edge_scaler.pkl")

    city_df = df[df["Location"] == city_name].sort_values("Date")

    for _, row in city_df.iterrows():

        start_time = time.time()

        features = row[feature_cols].to_frame().T
        scaled = scaler.transform(features)

        prediction = model.predict(scaled)[0]

        latency = time.time() - start_time

        # EDGE ALERT
        if prediction == 1:
            print(f"[EDGE-{city_name} PID: {os.getpid()}] 🚨 FLOOD DETECTED at {row['Date']}")
        else:
            print(f"[EDGE-{city_name} PID: {os.getpid()}] ✅ SAFE at {row['Date']}")

        print(f"[EDGE-{city_name} PID: {os.getpid()}] ⏱ Latency: {round(latency,4)} sec")

        queue.put({
            "city": city_name,
            "date": str(row["Date"]),
            "prediction": int(prediction),
            "actual": int(row["FloodOccurrence"]),
            "edge_latency": latency
        })

        time.sleep(1)