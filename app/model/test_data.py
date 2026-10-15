"""
    The schema for the data package
"""

from pydantic import BaseModel

class TestData(BaseModel):
    test_url : str
    test_service_instance_id: str
    certificate : str
    private_key : str
    root_certificate : str
    open_api_spec: str