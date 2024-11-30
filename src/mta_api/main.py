from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Dict, List

from mta_api.data.station_parser import get_stops_dict, process_subway_data
from mta_api.services.train_service import process_gtfs_data, URL_DICT
from mta_api.api.routes import LINE_TO_STOPS

app = FastAPI(title="NYC Subway Times API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load route data
process_subway_data()


class StationResponse(BaseModel):
    downtowns: str
    uptowns: str


class RouteStopsResponse(BaseModel):
    stops: List[str]


class ErrorResponse(BaseModel):
    detail: str



@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/api/v1/routes", response_model=Dict[str, List[str]])
async def get_routes():
    """
    Get all available subway routes and their stops.
    Returns a dictionary mapping route names to lists of station names.
    """
    return LINE_TO_STOPS


@app.get("/api/v1/routes/{route}", response_model=RouteStopsResponse)
async def get_route_stops(route: str):
    """
    Get all stops for a specific subway route.
    """
    route = route.upper()
    if route not in LINE_TO_STOPS:
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

    # Verify route exists
    if route not in URL_DICT:
        raise HTTPException(
            status_code=404, detail=f"Route {route} not found or not supported"
        )

    # Get GTFS stop ID
    stops_dict = get_stops_dict()
    stop_key = (station, route)

    if stop_key not in stops_dict:
        raise HTTPException(
            status_code=404, detail=f"Station '{station}' not found on route {route}"
        )

    gtfs_stop_id = stops_dict[stop_key]

    # Get arrival times
    try:
        arrivals = process_gtfs_data(route, gtfs_stop_id)
        if not arrivals:
            return StationResponse(downtowns="No data", uptowns="No data")
        return StationResponse(**arrivals)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching arrival times: {str(e)}"
        )


@app.get("/api/v1/health")
async def health_check():
    """
    Simple health check endpoint
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
