from pydantic import BaseModel

class ValueTypeNoID(BaseModel):
    type_name : str
    type_unit : str

class ValueType(ValueTypeNoID):
    id : int

class ValueNoID(BaseModel):
    value_type_id: int
    time: int
    value: float 
    device_id: int


class Value(ValueNoID):
    id: int

class ApiDescription(BaseModel):
    description : str = "This is the Api"
    value_type_link : str = "/type"
    value_link : str = "/value"

class DeviceNoID(BaseModel):
    name: str
    description: str
    location_id: int

class Device(DeviceNoID):
    id: int

class LocationNoID(BaseModel):
    name: str

class Location(LocationNoID):
    id: int