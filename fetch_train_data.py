import heapq
from datetime import datetime, timedelta

import pytz
import requests
from google.transit import gtfs_realtime_pb2

from parse_csv import get_stops_dict

NYC_TZ = pytz.timezone("America/New_York")

MAX_ARRIVALS = 4

URL_DICT = {
    "A": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "C": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "E": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "B": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "D": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "F": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "M": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "G": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
    "J": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    "Z": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    "N": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "Q": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "R": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "W": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "L": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
    "1": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "2": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "3": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "4": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "5": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "6": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "7": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
}


def fetch_and_parse_gtfs(line: str):
    url = URL_DICT[line]
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    return feed


def format_arrival_time(time):
    return time.astimezone(NYC_TZ).strftime("%I:%M %p")


def process_gtfs_data(line, gtfs_stop_id):
    arrivals = {"north": [], "south": []}
    feed = fetch_and_parse_gtfs(line)
    if not feed.entity:
        print("no entities)")
        return
    now = datetime.now()
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        trip = entity.trip_update
        for stop_time_update in trip.stop_time_update:
            stop_id: str = stop_time_update.stop_id
            # if stop_id.startswith(gtfs_stop_id):
            #     print(stop_time_update)
            if (
                not stop_time_update.HasField("arrival")
                or not stop_id.startswith(gtfs_stop_id)
                or (
                    arrival_time := datetime.fromtimestamp(
                        stop_time_update.arrival.time
                    )
                )
                < now
                or arrival_time - now > timedelta(minutes=30)
            ):
                continue
            time_diff = abs(now - arrival_time)
            formatted_time = format_arrival_time(arrival_time)
            arrival_list = (
                arrivals["north"] if stop_id.endswith("N") else arrivals["south"]
            )
            heapq.heappush(arrival_list, (-time_diff, formatted_time))
            if len(arrival_list) > MAX_ARRIVALS:
                heapq.heappop(arrival_list)

    downtowns = ", ".join(time for _, time in sorted(arrivals["south"], reverse=True))
    uptowns = ", ".join(time for _, time in sorted(arrivals["north"], reverse=True))
    return {"downtowns": downtowns, "uptowns": uptowns}


if __name__ == "__main__":
    stop = "Times Sq-42 St"
    line = "1"
    gtfs_stop_id = get_stops_dict().get((stop, line))
    x = process_gtfs_data(line, gtfs_stop_id)
    print(x)
    # feed = fetch_and_parse_gtfs()
    # process_gtfs_data(feed, "633")
