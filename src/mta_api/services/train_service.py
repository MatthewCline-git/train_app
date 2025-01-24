import heapq
from datetime import datetime, timedelta

import pytz
import requests
from google.transit import gtfs_realtime_pb2  # type: ignore[import-untyped]

from mta_api.data.station_parser import get_stops_dict
from mta_api.utils.logger import get_logger

logger = get_logger(__name__)

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
    logger.debug(f"Fetching GTFS data for line {line} from {url}")

    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Failed to retrieve data: {response.status_code}")
        return None

    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        feed.ParseFromString(response.content)
        logger.debug(f"Successfully parsed GTFS feed for line {line}")
        return feed
    except Exception as e:
        logger.error(f"Error parsing GTFS feed: {str(e)}", exc_info=True)
        return None


def format_arrival_time(time) -> str:
    return time.astimezone(NYC_TZ).strftime("%I:%M %p")


def process_gtfs_data(line, gtfs_stop_id) -> dict[str, str] | None:
    logger.info(f"Processing GTFS data for line {line}, stop {gtfs_stop_id}")

    arrivals: dict[str, list[tuple[float, str]]] = {"north": [], "south": []}
    feed = fetch_and_parse_gtfs(line)

    if not feed:
        logger.warning("No feed received from fetch_and_parse_gtfs")
        return None

    if not feed.entity:
        logger.warning("Feed contains no entities")
        return None

    now = datetime.now()
    processed_count = 0
    skipped_count = 0

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip = entity.trip_update
        for stop_time_update in trip.stop_time_update:
            stop_id: str = stop_time_update.stop_id

            # Skip updates that don't meet our criteria
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
                skipped_count += 1
                continue

            time_diff = abs(now - arrival_time)
            formatted_time = format_arrival_time(arrival_time)
            direction = "north" if stop_id.endswith("N") else "south"

            arrival_list = arrivals[direction]
            arrival_info: tuple[timedelta, str] = (-time_diff, formatted_time)
            heapq.heappush(arrival_list, arrival_info)  # type: ignore

            if len(arrival_list) > MAX_ARRIVALS:
                heapq.heappop(arrival_list)

            processed_count += 1

    logger.debug(
        f"Processed {processed_count} arrivals, skipped {skipped_count} updates"
    )

    # Format the final results
    downtowns = ", ".join(time for _, time in sorted(arrivals["south"], reverse=True))
    uptowns = ", ".join(time for _, time in sorted(arrivals["north"], reverse=True))

    result = {"downtowns": downtowns, "uptowns": uptowns}
    logger.info(f"Final arrival times for stop {gtfs_stop_id}: {result}")

    return result


if __name__ == "__main__":
    stop = "Times Sq-42 St"
    line = "1"
    logger.info(f"Testing arrival times for {stop} on line {line}")

    gtfs_stop_id = get_stops_dict().get((stop, line))
    if not gtfs_stop_id:
        logger.error(f"Could not find GTFS stop ID for {stop} on line {line}")
    else:
        result = process_gtfs_data(line, gtfs_stop_id)
        logger.info(f"Test result: {result}")
