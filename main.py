import logging

from fastapi import FastAPI

from app.model.test_results import TestResults
from app.test_scripts.msr_openapi_validator import MsrOpenApiValidator
from app.model.test_data import TestData


description = """

## 
Validate a given URL against the MSR OpenAPI schema

"""

tags_metadata = [
    {
        "name": "testServiceRegistry",
        "description": "Run validation tests against the MSR",
    }
]

app = FastAPI(openapi_tags=tags_metadata, title="MSR Validator", description=description)


@app.post("/api/testServiceRegistry/", tags=["testServiceRegistry"])
async def test_service_registry(data : TestData) -> TestResults:
    """
    Test a given URL against the MSR OpenAPI schema

    :return:
    """

    logging.info(f"Test URL: {data.test_url}")
    validate_msr = MsrOpenApiValidator(data, "./app/schema/MSRv2-dodgy.json")

    return validate_msr.validate_msr()