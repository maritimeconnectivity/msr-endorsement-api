"""
    Store the individual test result
"""
from pydantic import BaseModel


class TestResult(BaseModel):
    """
        Store a single test result
    """

    test_name : str
    test_success : bool
    full_response : dict
    failure_reason : str = ""

    def to_dict(self) -> dict:
        return vars(self)