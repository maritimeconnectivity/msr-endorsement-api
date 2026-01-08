"""
    Class to store the list of test results
"""
from pydantic import BaseModel

from app.model.test_result import TestResult


class TestResults(BaseModel):
    """
        Store a list of test results
    """

    results : list[TestResult] = []

    def to_dict(self) -> dict:
        dictionary = { "results" : [result.to_dict() for result in self.results]}
        return dictionary
