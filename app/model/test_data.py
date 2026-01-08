"""
    The schema for the data package
"""

from pydantic import BaseModel

class TestData(BaseModel):
    test_url : str
    certificate : str
    private_key : str
    root_certificate : str