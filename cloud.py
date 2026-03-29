import sqlite3

def init_db():
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        date TEXT,
        city TEXT,
        prediction INTEGER,
        actual INTEGER,
        risk TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        date TEXT,
        avg_edge_latency REAL,
        fog_latency REAL,
        resource_transfer INTEGER,
        accuracy REAL
    )
    """)

    conn.commit()
    conn.close()


def cloud_node(queue):

    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()

    while True:

        data = queue.get()

        date = data["date"]
        preds = data["predictions"]
        actual = data["actual"]

        correct = 0
        total = len(preds)

        for city in preds:
            cur.execute(
                "INSERT INTO logs VALUES (?, ?, ?, ?, ?)",
                (date, city, preds[city], actual[city], data["risk"])
            )

            if preds[city] == actual[city]:
                correct += 1

        accuracy = correct / total

        avg_edge_latency = sum(data["edge_latencies"]) / len(data["edge_latencies"])

        cur.execute(
            "INSERT INTO metrics VALUES (?, ?, ?, ?, ?)",
            (
                date,
                avg_edge_latency,
                data["fog_latency"],
                data["total_transfer"],
                accuracy
            )
        )

        conn.commit()

        # -------- LOGGING --------
        print("\n************ CLOUD LAYER ************")
        print(f"[CLOUD] Logged data for date: {date}")
        print(f"[CLOUD] Accuracy: {round(accuracy,3)}")
        print(f"[CLOUD] Avg Edge Latency: {round(avg_edge_latency,4)} sec")
        print(f"[CLOUD] Fog Latency: {round(data['fog_latency'],4)} sec")
        print(f"[CLOUD] Resource Transfers: {data['total_transfer']}")
        print("************************************\n")