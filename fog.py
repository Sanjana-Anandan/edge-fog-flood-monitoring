from collections import defaultdict
import time

def fog_node(edge_queue, cloud_queue):

    city_resources = {
        "Manila": 5,
        "Pasig": 3,
        "Marikina": 4,
        "Quezon City": 6
    }

    buffer = {}

    while True:

        data = edge_queue.get()

        date = data["date"]

        if date not in buffer:
            buffer[date] = []

        buffer[date].append(data)

        if len(buffer[date]) == 4:

            start_time = time.time()

            entries = buffer[date]

            city_status = {e["city"]: e["prediction"] for e in entries}
            actual_status = {e["city"]: e["actual"] for e in entries}

            flood_cities = [c for c, v in city_status.items() if v == 1]

            # Regional Risk
            if len(flood_cities) == 0:
                risk = "LOW"
            elif len(flood_cities) == 1:
                risk = "MODERATE"
            else:
                risk = "HIGH"

            # AER LOGIC
            resource_transfer = {c: 0 for c in city_resources}
            total_transfer = 0

            for city in flood_cities:
                needed = 2
                for donor in city_resources:
                    if donor != city and city_resources[donor] > 1:
                        city_resources[donor] -= 1
                        city_resources[city] += 1

                        resource_transfer[city] += 1
                        resource_transfer[donor] -= 1

                        total_transfer += 1

                        needed -= 1
                        if needed == 0:
                            break

            fog_latency = time.time() - start_time

            # -------- LOGGING --------
            print("\n================ FOG LAYER =================")
            print(f"[FOG] Processing Date: {date}")

            print("[FOG] City Predictions:")
            for c, v in city_status.items():
                print(f"   {c}: {'FLOOD' if v == 1 else 'SAFE'}")

            print(f"[FOG] Regional Risk: {risk}")

            print("[FOG] Resource State:")
            print(city_resources)

            print("[FOG] Resource Transfers:")
            print(resource_transfer)

            print(f"[FOG] ⏱ Fog Latency: {round(fog_latency,4)} sec")
            print("===========================================\n")

            # Send to cloud
            cloud_queue.put({
                "date": str(date),
                "predictions": city_status,
                "actual": actual_status,
                "risk": risk,
                "resources": dict(city_resources),
                "transfers": resource_transfer,
                "edge_latencies": [e["edge_latency"] for e in entries],
                "fog_latency": fog_latency,
                "total_transfer": total_transfer
            })

            del buffer[date]

        time.sleep(0.1)