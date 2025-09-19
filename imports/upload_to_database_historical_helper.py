CONNECTION = "postgres://postgres:elnor007@localhost:5432/my_database"

import asyncio
import asyncpg
import requests
from datetime import datetime, timedelta, timezone
import sys

# Vivacity API endpoint
url = "https://api.vivacitylabs.com/countline/counts"


# CHANGE API KEY BELOW
##################################################
headers = {
    "x-vivacity-api-key": "INSERT_API_KEY_HERE",
    "Accept": "application/json"
}
##################################################

max_retries = 10  
retry_delay = 1  #seconds

bucket_size_m = [60, 1440]   # insert the time buckets you want uploaded to the database, set to 1 hour & 24 hours by default (in minutes)

last_x_minutes = 60*24*7     # date range to download traffic data, between now and now-last_x_minutes

last_x_minutes_cycles = 1    # does 1 cycle by default. Cycles > 1 are generally used to bypass the date range limit (set by the API) by using a "sliding window" method 
                             # in order to download historical traffic information, where each cycle moves back in time by last_x_minutes



# Handles errors for most of the functions below
async def error_handler(exception, error_type, retry, conn = 0):
    print(f"{datetime.now()} : ({error_type}) Error : {exception}\n")
    await asyncio.sleep(retry_delay)
    if retry == max_retries - 1:
        print(f"{datetime.now()} : ({error_type}) Error unresolved - exiting program\n\n\n\n\n")
        if conn:
            await conn.close()
        sys.exit(2)
    print(f"{datetime.now()} : ({error_type}) Attempt no.{retry + 1} failed, retrying if possible...\n")



def get_latest_x_range(bucket_size_m, last_x_minutes):
    now = datetime.now(timezone.utc)

    if bucket_size_m >= 60:
        # Align to the top of the current hour or day depending on bucket
        aligned = now.replace(minute=0, second=0, microsecond=0)

        if bucket_size_m % 1440 == 0:  # 1440 minutes = 24 hours
            aligned = aligned.replace(hour=0)
    else:
        minute = (now.minute // bucket_size_m) * bucket_size_m
        aligned = now.replace(minute=minute, second=0, microsecond=0)

    from_time = aligned - timedelta(minutes=last_x_minutes)
    to_time = aligned

    from_time_iso = from_time.isoformat().replace("+00:00", "Z")
    to_time_iso = to_time.isoformat().replace("+00:00", "Z")

    return from_time_iso, to_time_iso



async def create_database_if_missing(conn):
    print("About to start creating database")
    global max_retries, retry_delay
    for retry in range(max_retries):
        print(f"Creation attempt no. {retry}")

        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS vivacity_traffic (
                    time_from TIMESTAMPTZ NOT NULL,
                    time_to TIMESTAMPTZ NOT NULL,
                    countline_id TEXT,
                    name TEXT,
                    car INTEGER,
                    bus INTEGER,
                    cyclist INTEGER,
                    motorbike INTEGER,
                    pedestrian INTEGER,
                    rigid INTEGER,
                    time_bucket TEXT,
                    day INTEGER,
                    total_count INTEGER
                );
            """)
            await conn.execute("""
                SELECT create_hypertable('vivacity_traffic', 'time_from', if_not_exists => TRUE);
            """)
            print("Table created")
            break
        
        except Exception as e:
            await error_handler(e, "Create Table", retry, conn)    
            continue



def iso_parse(iso_str):
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))



async def connection_handler():
    global max_retries, retry_delay
    for retry in range(max_retries):
        try:
            conn = await asyncpg.connect(CONNECTION)
            return conn

        except Exception as e :
            await error_handler(e, "Connection", retry, conn = 0)
            continue



async def response_handler(url, headers, params):
    global max_retries, retry_delay
    for retry in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params)
            return response
        except Exception as e:
            await error_handler(e, "Response", retry, conn = 0)
            continue



async def insert_handler(conn, rows, bucket, cycle):
    global max_retries, retry_delay
    for retry in range(max_retries):
        try:
            await conn.executemany("""
                        INSERT INTO vivacity_traffic (
                            time_from, time_to, countline_id, name,
                            car, bus, cyclist, motorbike, pedestrian, rigid, time_bucket, day, total_count
                        ) VALUES (
                            $1, $2, $3, $4, $5,
                            $6, $7, $8, $9, $10, $11, $12, $13
                        )
                    """, rows)
            print(f"{datetime.now()} : Successful insertion of bucket size = {bucket}m at cycle = {cycle+1}\n")
            break

        except Exception as e:
            await error_handler(e, "Insertion", retry, conn)
            continue



