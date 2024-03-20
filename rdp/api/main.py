from typing import Union, List, Optional

from fastapi import FastAPI, HTTPException

from rdp.sensor import Reader
from rdp.crud import create_engine, Crud
from . import api_types as ApiTypes
import logging

logger = logging.getLogger("rdp.api")
app = FastAPI()

@app.get("/")
def read_root() -> ApiTypes.ApiDescription:
    """This url returns a simple description of the api

    Returns:
        ApiTypes.ApiDescription: the Api description in json format 
    """    
    return ApiTypes.ApiDescription()

@app.get("/type/")
def read_types() -> List[ApiTypes.ValueType]:
    """Implements the get of all value types

    Returns:
        List[ApiTypes.ValueType]: list of available valuetypes. 
    """    
    global crud
    return crud.get_value_types()

@app.get("/type/{id}/")
def read_type(id: int) -> ApiTypes.ValueType:
    """returns an explicit value type identified by id

    Args:
        id (int): primary key of the desired value type

    Raises:
        HTTPException: Thrown if a value type with the given id cannot be accessed

    Returns:
        ApiTypes.ValueType: the desired value type 
    """
    global crud
    try:
         return crud.get_value_type(id)
    except crud.NoResultFound:
        raise HTTPException(status_code=404, detail="Item not found") 
    return value_type 

@app.put("/type/{id}/")
def put_type(id, value_type: ApiTypes.ValueTypeNoID) -> ApiTypes.ValueType:
    """PUT request to a special valuetype. This api call is used to change a value type object.

    Args:
        id (int): primary key of the requested value type
        value_type (ApiTypes.ValueTypeNoID): json object representing the new state of the value type. 

    Raises:
        HTTPException: Thrown if a value type with the given id cannot be accessed 

    Returns:
        ApiTypes.ValueType: the requested value type after persisted in the database. 
    """
    global crud
    try:
        crud.add_or_update_value_type(id, value_type_name=value_type.type_name, value_type_unit=value_type.type_unit)
        return read_type(id)
    except crud.NoResultFound:
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/value/")
def get_values(type_id:int=None, start:int=None, end:int=None) -> List[ApiTypes.Value]:
    """Get values from the database. The default is to return all available values. This result can be filtered.

    Args:
        type_id (int, optional): If set, only values of this type are returned. Defaults to None.
        start (int, optional): If set, only values at least as new are returned. Defaults to None.
        end (int, optional): If set, only values not newer than this are returned. Defaults to None.

    Raises:
        HTTPException: _description_

    Returns:
        List[ApiTypes.Value]: _description_
    """
    global crud
    try:
        values = crud.get_values(type_id, start, end)
        return values
    except crud.NoResultFound:
        raise HTTPException(status_code=404, deltail="Item not found")

@app.post("/create_device/", response_model=ApiTypes.Device)
def create_device(device_data: ApiTypes.DeviceNoID) -> ApiTypes.Device:
    """Create a new device with the given name and description.

    Args:
        device_data (ApiTypes.DeviceCreate): The name and description of the new device.

    Returns:
        ApiTypes.Device: The created device with its ID, name, and description.
    """
    global crud
    try:
        new_device = crud.add_device(name=device_data.name, description=device_data.description, location_id=device_data.location_id)
        return ApiTypes.Device(id=new_device.id, name=new_device.name, description=new_device.description, location_id=new_device.location_id)
    except crud.IntegrityError as e:
        logger.error(f"Failed to create a new device: {e}")
        raise HTTPException(status_code=400, detail="Failed to create a new device due to a database error.")

@app.get("/get_devices/")
def get_devices():
    return crud.get_devices()

@app.get("/get_values/by_device_id_or_name/", response_model=List[ApiTypes.Value])
def read_values_by_device(device_id: Optional[int] = None, device_name: Optional[str] = None):
    if device_id is None and device_name is None:
        raise HTTPException(status_code=400, detail="Either device_id or device_name must be provided")
    try:
        values = crud.get_values_by_device(device_id=device_id, device_name=device_name)
        return values
    except crud.NoResultFound:
        raise HTTPException(status_code=404, detail="Device not found or no values for this device")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/create_location/", response_model=ApiTypes.Location)
def create_location(location_data: ApiTypes.LocationNoID) -> ApiTypes.Location:
    """Create a new location with the given name.

    Args:
        device_data (ApiTypes.LocationCreate): The name of the new location.

    Returns:
        ApiTypes.Location: The created location with its ID, name.
    """
    global crud
    try:
        new_location = crud.add_location(name=location_data.name)
        return ApiTypes.Location(id=new_location.id, name=new_location.name)
    except crud.IntegrityError as e:
        logger.error(f"Failed to create a new location: {e}")
        raise HTTPException(status_code=400, detail="Failed to create a new location due to a database error.")

@app.get("/get_location/")
def get_location():
    return crud.get_location()

@app.get("/get_device/by_location_id_or_name/", response_model=List[ApiTypes.Device])
def read_device_by_location(location_id: Optional[int] = None, location_name: Optional[str] = None):
    if location_id is None and location_name is None:
        raise HTTPException(status_code=400, detail="Either location_id or location_name must be provided")
    try:
        device = crud.get_devices_by_location(location_id=location_id, location_name=location_name)
        return device
    except crud.NoResultFound:
        raise HTTPException(status_code=404, detail="Location not found or no devices for this location")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.on_event("startup")
async def startup_event() -> None:
    """start the character device reader
    """    
    logger.info("STARTUP: Sensor reader!")
    global reader, crud
    engine = create_engine("sqlite:///rdb.test.db")
    crud = Crud(engine)
    reader = Reader(crud)
    reader.start()
    logger.debug("STARTUP: Sensor reader completed!")

@app.on_event("shutdown")
async def shutdown_event():
    """stop the character device reader
    """    
    global reader
    logger.debug("SHUTDOWN: Sensor reader!")
    reader.stop()
    logger.info("SHUTDOWN: Sensor reader completed!")
