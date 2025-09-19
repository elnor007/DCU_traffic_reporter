# Gets all the handler functions from the imports folder
from imports.upload_to_database_historical_helper import *

import sys
import os
from datetime import datetime, timedelta

print(f"\n\n\n\n\n{datetime.now()} : {os.path.basename(__file__)} has been initiated.\n")



# Async main
async def main():
    global last_x_minutes_cycles
    if len(sys.argv) > 1:
        last_x_minutes_cycles = int(sys.argv[1])

    # Connect to DB
    conn = await connection_handler()

    await create_database_if_missing(conn)

    # Fetch historical data
    for bucket in bucket_size_m:
        from_time, to_time = get_latest_x_range(bucket, last_x_minutes)

        params = {
            "countline_ids": "52453,52454,52455",
            "classes": "car,pedestrian,bus,cyclist,motorbike,rigid",
            "time_bucket": f"{bucket}m",
            "from": from_time,
            "to": to_time,
            "fill_zeros": "true"
            }

        for cycle in range(last_x_minutes_cycles):
            response = await response_handler(url, headers, params)

            # The code below shifts the time range back by last_x_minutes at the start of every cycle
            from_time_dt = datetime.fromisoformat(params["from"].replace("Z", "+00:00"))
            from_time_dt -= timedelta(minutes=last_x_minutes)
            params["from"] = from_time_dt.isoformat().replace("+00:00", "Z")
            to_time_dt = datetime.fromisoformat(params["to"].replace("Z", "+00:00"))
            to_time_dt -= timedelta(minutes=last_x_minutes)
            params["to"] = to_time_dt.isoformat().replace("+00:00", "Z")

            try:
                data = response.json()
            except:
                print(f"{datetime.now()} : (Response JSON) Error : {response.text}\n")

            # Countline ID to name mapping
            name_map = {
                "52453": "S1_DCU_road_outbound_smdb002",
                "52454": "S1_DCU_road_inbound_smdb002",
                "52455": "S1_DCU_path_smdb002"
            }

            rows = []
            for countline_id, entries in data.items():
                name = name_map.get(countline_id, "Unknown")
                for entry in entries:
                    clockwise = entry.get("clockwise", {})
                    anticlockwise = entry.get("anti_clockwise", {})
                    
                    car = clockwise.get("car", 0) + anticlockwise.get("car", 0)
                    bus = clockwise.get("bus", 0) + anticlockwise.get("bus", 0)
                    cyclist = clockwise.get("cyclist", 0) + anticlockwise.get("cyclist", 0)
                    motorbike = clockwise.get("motorbike", 0) + anticlockwise.get("motorbike", 0)
                    pedestrian = clockwise.get("pedestrian", 0) + anticlockwise.get("pedestrian", 0)
                    rigid = clockwise.get("rigid", 0) + anticlockwise.get("rigid", 0)
                    total_count = car+bus+cyclist+motorbike+pedestrian+rigid

                    # Anti-clockwise and clockwise indicate the direction at which the object passed the countline.
                    # Both directions are summed to get total amount for each class.

                    record = (
                        iso_parse(entry["from"]),
                        iso_parse(entry["to"]),
                        countline_id,
                        name,
                        car,
                        bus,
                        cyclist,
                        motorbike,
                        pedestrian,
                        rigid,
                        f"{bucket}m",
                        iso_parse(entry["from"]).weekday(),
                        total_count
                    )
                    rows.append(record)

            # Insert batch
            await insert_handler(conn, rows, bucket, cycle)

    print(f"{datetime.now()} : Exiting {os.path.basename(__file__)}...\n\n\n\n\n")
    await conn.close()
    

# Run
asyncio.run(main())

