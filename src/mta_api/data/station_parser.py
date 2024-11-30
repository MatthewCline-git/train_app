import csv
from collections import defaultdict
from functools import cache

from pathlib import Path

project_root = Path(__file__).parents[3]


def parse_routes(routes_str: str) -> tuple[str, ...]:
    """Convert space-separated route string into sorted tuple of routes"""
    return tuple(sorted(routes_str.strip().split()))


def parse_coordinates(lat_str: str, lon_str: str) -> tuple[float, float]:
    """Convert latitude and longitude strings to tuple of floats"""
    return (float(lon_str), float(lat_str))  # Note: returns as (lon, lat) pair


@cache
def process_subway_data() -> (
    tuple[
        dict[tuple[str, str], str],  # stops_dict
        dict[str, tuple[float, float]],  # coords_dict
    ]
):
    """
    Process NYC subway stop data from CSV into three dictionaries:
    1. stops_dict - Key: Tuple of (Stop Name, single route), Value: GTFS Stop ID
    2. coords_dict - Key: GTFS Stop ID, Value: Tuple of (longitude, latitude)
    3. route_stops_dict - Key: Route (e.g., "4"), Value: List of stop names on that route
    """
    stops_dict = {}
    coords_dict = {}
    route_stops_dict = defaultdict(set)  # Using set to avoid duplicates
    csv_path = project_root / "data" / "MTA_Subway_Stations_20241024.csv"

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stop_name = row["Stop Name"]
            stop_id = row["GTFS Stop ID"]
            routes = parse_routes(row["Daytime Routes"])

            for route in routes:
                stops_key = (stop_name, route)
                stops_dict[stops_key] = stop_id

            try:
                coords = parse_coordinates(row["GTFS Latitude"], row["GTFS Longitude"])
                coords_dict[stop_id] = coords
            except (ValueError, KeyError) as e:
                print(f"Warning: Could not process coordinates for stop {stop_id}: {e}")

            for route in routes:
                route_stops_dict[route].add(stop_name)

    return (
        stops_dict,
        coords_dict,
    )


def get_stops_dict() -> dict[tuple[str, str], str]:
    """
    Returns just the stops dictionary mapping (stop_name, route) to GTFS Stop ID
    """
    return process_subway_data()[0]


def get_coords_dict() -> dict[str, tuple[float, float]]:
    """
    Returns just the coordinates dictionary mapping GTFS Stop ID to (longitude, latitude)
    """
    return process_subway_data()[1]


# Example usage:
if __name__ == "__main__":
    # Use individual functions based on which dictionary you need
    stops_dict = get_stops_dict()
    print("\nLooking up a specific stop-route combination:")
    stop_id = stops_dict[("Grand Central-42 St", "4")]
    print(f"Stop ID for Grand Central on 4 train: {stop_id}")

    coords_dict = get_coords_dict()
    print("\nLooking up coordinates for a stop ID:")
    if stop_id in coords_dict:
        lon, lat = coords_dict[stop_id]
        print(f"Coordinates: ({lat}, {lon})")
