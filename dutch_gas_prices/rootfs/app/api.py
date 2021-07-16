"""
Dutch Gas prices API
"""
from fastapi import FastAPI, Query
from gas_prices import gas_prices
from gas_stations import gas_stations
from enum import Enum

app = FastAPI(
    title="Dutch Gas prices API",
    description="Dutch Gas prices API.",
    version="1.0",
)

class FuelName(str, Enum):
    euro95 = "euro95"
    euro98 = "euro98"
    diesel = "diesel"
    lpg = "autogas"
#    cng = "aardgas"

@app.get("/")
async def root():
    """
    Gas prices API Status
    """
    return {"Status": "Online"}


@app.get("/api/v1/gas_prices/{station_id}",
         summary="Query the gas prices from a station",
         description="Returns Euro 95 and Diesel prices from directlease.nl \
             (Note: because it's using OCR technology it's not 100% accurate)",
         )
async def api_gas_prices(station_id: str = Query(None, \
                         description='Provide Station ID (number before .png)')):
    """
    Query the gas prices from a station
    """
    result = gas_prices(station_id)
    return result

@app.get("/api/v1/gas_stations/{fuel}",
         summary="Query fuel specific gas stations in a radius",
         description="Returns stations from directlease.nl based on latitude, longitude and a radius",
         )
async def api_gas_stations(fuel: FuelName, longitude: float, latitude: float, radius: int = Query(default=5, gt=0, le=15)):
    """
    Query fuel specific gas stations in a radius
    """
    result = gas_stations(fuel,longitude,latitude,radius)
    return result
