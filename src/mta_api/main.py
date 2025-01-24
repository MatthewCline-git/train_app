from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Dict, List
from mta_api.data.station_parser import get_stops_dict, process_subway_data
from mta_api.services.train_service import process_gtfs_data, URL_DICT
from mta_api.api.routes import LINE_TO_STOPS
from mta_api.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="NYC Subway Times API")

# TODO: specify this later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Initializing subway data...")
process_subway_data()
logger.info("Subway data loaded successfully")


class StationResponse(BaseModel):
    downtowns: str
    uptowns: str


class RouteStopsResponse(BaseModel):
    stops: List[str]


class ErrorResponse(BaseModel):
    detail: str


@app.get("/")
async def root():
    logger.debug("Redirecting to docs")
    return RedirectResponse(url="/docs")


@app.get("/api/v1/routes", response_model=Dict[str, List[str]])
async def get_routes():
    """
    Get all available subway routes and their stops.
    Returns a dictionary mapping route names to lists of station names.
    """
    logger.info("Fetching all routes and stops")
    return LINE_TO_STOPS


@app.get("/api/v1/routes/{route}", response_model=RouteStopsResponse)
async def get_route_stops(route: str):
    """
    Get all stops for a specific subway route.
    """
    route = route.upper()
    logger.info(f"Fetching stops for route {route}")

    if route not in LINE_TO_STOPS:
        logger.warning(f"Route not found: {route}")
        raise HTTPException(status_code=404, detail=f"Route {route} not found")

    return RouteStopsResponse(stops=LINE_TO_STOPS[route])


@app.get("/api/v1/arrivals/{route}/{station}", response_model=StationResponse)
async def get_arrivals(route: str, station: str):
    """
    Get upcoming train arrivals for a specific station and route.
    Returns lists of upcoming downtown and uptown trains.
    Parameters:
    - route: Subway route (e.g., "4", "A", "Q")
    - station: Station name (e.g., "Times Sq-42 St")
    """
    route = route.upper()
    logger.info(f"Fetching arrivals for route {route} at station {station}")

    # Verify route exists
    if route not in URL_DICT:
        logger.warning(f"Unsupported route requested: {route}")
        raise HTTPException(
            status_code=404, detail=f"Route {route} not found or not supported"
        )

    # Get GTFS stop ID
    stops_dict = get_stops_dict()
    stop_key = (station, route)

    if stop_key not in stops_dict:
        logger.warning(f"Invalid station/route combination: {station} on {route}")
        raise HTTPException(
            status_code=404, detail=f"Station '{station}' not found on route {route}"
        )

    gtfs_stop_id = stops_dict[stop_key]
    logger.debug(f"Found GTFS stop ID: {gtfs_stop_id}")

    # Get arrival times
    try:
        arrivals = process_gtfs_data(route, gtfs_stop_id)
        if not arrivals:
            logger.info(f"No arrival data available for {station} on route {route}")
            return StationResponse(downtowns="No data", uptowns="No data")
        logger.debug(f"Arrivals found: {arrivals}")
        return StationResponse(**arrivals)
    except Exception as e:
        logger.error(f"Error fetching arrival times: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error fetching arrival times: {str(e)}"
        )


@app.get("/api/v1/health")
async def health_check():
    """
    Simple health check endpoint
    """
    logger.debug("Health check requested")
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting MTA API server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
