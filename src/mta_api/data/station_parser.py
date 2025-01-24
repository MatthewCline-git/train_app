import csv
from collections import defaultdict
from functools import cache
from pathlib import Path
from mta_api.utils.logger import get_logger

logger = get_logger(__name__)

CSV_PATH = Path(__file__).parent / "MTA_Subway_Stations_20241024.csv"


def parse_routes(routes_str: str) -> tuple[str, ...]:
    """Convert space-separated route string into sorted tuple of routes"""
    try:
        routes = tuple(sorted(routes_str.strip().split()))
        logger.debug(f"Parsed routes: {routes}")
        return routes
    except Exception as e:
        logger.error(f"Error parsing routes string '{routes_str}': {str(e)}")
        return tuple()


def parse_coordinates(lat_str: str, lon_str: str) -> tuple[float, float]:
    """Convert latitude and longitude strings to tuple of floats"""
    try:
        coords = (float(lon_str), float(lat_str))  # Note: returns as (lon, lat) pair
        logger.debug(f"Parsed coordinates: {coords}")
        return coords
    except (ValueError, TypeError) as e:
        logger.error(
            f"Error parsing coordinates (lat: {lat_str}, lon: {lon_str}): {str(e)}"
        )
        raise


@cache
def process_subway_data() -> tuple[
    dict[tuple[str, str], str],  # stops_dict
    dict[str, tuple[float, float]],  # coords_dict
]:
    """
    Process NYC subway stop data from CSV into three dictionaries:
    1. stops_dict - Key: Tuple of (Stop Name, single route), Value: GTFS Stop ID
    2. coords_dict - Key: GTFS Stop ID, Value: Tuple of (longitude, latitude)
    3. route_stops_dict - Key: Route (e.g., "4"), Value: List of stop names on that route
    """
    logger.info(f"Processing subway data from {CSV_PATH}")

    stops_dict = {}
    coords_dict = {}
    route_stops_dict = defaultdict(set)  # Using set to avoid duplicates

    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row_count = 0
            error_count = 0

            for row in reader:
                row_count += 1
                stop_name = row["Stop Name"]
                stop_id = row["GTFS Stop ID"]
                logger.debug(f"Processing stop: {stop_name} (ID: {stop_id})")

                routes = parse_routes(row["Daytime Routes"])

                # Process routes
                for route in routes:
                    stops_key = (stop_name, route)
                    stops_dict[stops_key] = stop_id

                # Process coordinates
                try:
                    coords = parse_coordinates(
                        row["GTFS Latitude"], row["GTFS Longitude"]
                    )
                    coords_dict[stop_id] = coords
                except (ValueError, KeyError) as e:
                    error_count += 1
                    logger.warning(
                        f"Could not process coordinates for stop {stop_id}: {e}"
                    )

                # Process route stops
                for route in routes:
                    route_stops_dict[route].add(stop_name)

            logger.info(
                f"Processed {row_count} stations with {error_count} coordinate errors"
            )
            logger.info(
                f"Created mappings for {len(stops_dict)} stop-route combinations"
            )
            logger.debug(f"Found {len(coords_dict)} stations with valid coordinates")

            return (
                stops_dict,
                coords_dict,
            )

    except FileNotFoundError:
        logger.error(f"Station data file not found: {CSV_PATH}")
        raise
    except Exception as e:
        logger.error(f"Error processing subway data: {str(e)}", exc_info=True)
        raise


def get_stops_dict() -> dict[tuple[str, str], str]:
    """
    Returns just the stops dictionary mapping (stop_name, route) to GTFS Stop ID
    """
    logger.debug("Retrieving stops dictionary")
    return process_subway_data()[0]


def get_coords_dict() -> dict[str, tuple[float, float]]:
    """
    Returns just the coordinates dictionary mapping GTFS Stop ID to (longitude, latitude)
    """
    logger.debug("Retrieving coordinates dictionary")
    return process_subway_data()[1]


if __name__ == "__main__":
    logger.info("Testing station parser")
    stops_dict, coords_dict = process_subway_data()
    logger.info(f"Successfully loaded {len(stops_dict)} stop-route combinations")
    logger.info(f"Successfully loaded coordinates for {len(coords_dict)} stations")
