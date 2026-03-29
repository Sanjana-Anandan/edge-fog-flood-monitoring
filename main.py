from multiprocessing import Process, Queue
import pandas as pd

from edge import edge_node
from fog import fog_node
from cloud import cloud_node, init_db


def main():

    df = pd.read_csv("Flood_Prediction_NCR_Philippines.csv")
    df["Date"] = pd.to_datetime(df["Date"])

    df = df.sort_values(["Location", "Date"])

    # Feature engineering
    df["Rainfall_3day_sum"] = df.groupby("Location")["Rainfall_mm"].rolling(3).sum().reset_index(level=0, drop=True)
    df["Rainfall_7day_sum"] = df.groupby("Location")["Rainfall_mm"].rolling(7).sum().reset_index(level=0, drop=True)
    df["WaterLevel_3day_avg"] = df.groupby("Location")["WaterLevel_m"].rolling(3).mean().reset_index(level=0, drop=True)
    df["Flood_lag1"] = df.groupby("Location")["FloodOccurrence"].shift(1)

    df = df.dropna()
    df = df[df["Date"] >= "2020-01-01"]

    feature_cols = [
        "Rainfall_mm",
        "WaterLevel_m",
        "SoilMoisture_pct",
        "Elevation_m",
        "Rainfall_3day_sum",
        "Rainfall_7day_sum",
        "WaterLevel_3day_avg",
        "Flood_lag1"
    ]

    edge_queue = Queue()
    cloud_queue = Queue()

    init_db()

    cities = ["Manila", "Pasig", "Marikina", "Quezon City"]

    processes = []

    # Edge processes
    for city in cities:
        p = Process(target=edge_node, args=(city, df, feature_cols, edge_queue))
        p.start()
        processes.append(p)

    # Fog process
    fog = Process(target=fog_node, args=(edge_queue, cloud_queue))
    fog.start()

    # Cloud process
    cloud = Process(target=cloud_node, args=(cloud_queue,))
    cloud.start()

    processes.extend([fog, cloud])

    for p in processes:
        p.join()


if __name__ == "__main__":
    main()