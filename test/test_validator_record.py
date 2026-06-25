"""
Tests for MsrOpenApiValidator._record() and progress_callback wiring.
No network calls are made; PKIServices and OpenAPI are mocked.
"""
import base64
from unittest.mock import MagicMock, patch

import pytest

from app.model.test_data import TestData
from app.model.test_result import TestResult
from app.model.test_results import TestResults


def _make_test_data() -> TestData:
    # Minimal base64 placeholder values — PKIServices is mocked so content doesn't matter.
    dummy = base64.b64encode(b"dummy").decode()
    return TestData(
        test_url="https://example.com/",
        certificate=dummy,
        private_key=dummy,
        root_certificate=dummy,
        test_service_instance_id="urn:mrn:mcp:service:test:instance:1",
    )


def _make_validator(callback=None):
    """Build a MsrOpenApiValidator with all I/O mocked out."""
    from app.test_scripts.msr_openapi_validator import MsrOpenApiValidator

    with patch("app.test_scripts.msr_openapi_validator.OpenAPI"), \
         patch("app.test_scripts.msr_openapi_validator.PKIServices"):
        validator = MsrOpenApiValidator(
            _make_test_data(),
            api_path="./app/schema/MSRv2.json",
            progress_callback=callback,
        )
    return validator


class TestRecord:

    def test_record_appends_to_test_results(self):
        validator = _make_validator()
        results = TestResults()
        result = TestResult(test_name="T1", test_success=True, full_response={})
        validator._record(results, result)
        assert len(results.results) == 1
        assert results.results[0] is result

    def test_record_returns_the_result(self):
        validator = _make_validator()
        results = TestResults()
        result = TestResult(test_name="T1", test_success=True, full_response={})
        returned = validator._record(results, result)
        assert returned is result

    def test_record_fires_progress_callback(self):
        received = []
        validator = _make_validator(callback=received.append)
        results = TestResults()
        result = TestResult(test_name="T1", test_success=True, full_response={})
        validator._record(results, result)
        assert received == [result]

    def test_record_fires_callback_for_each_result(self):
        received = []
        validator = _make_validator(callback=received.append)
        results = TestResults()
        r1 = TestResult(test_name="T1", test_success=True, full_response={})
        r2 = TestResult(test_name="T2", test_success=False, full_response={}, failure_reason="oops")
        validator._record(results, r1)
        validator._record(results, r2)
        assert received == [r1, r2]

    def test_record_without_callback_does_not_raise(self):
        validator = _make_validator(callback=None)
        results = TestResults()
        result = TestResult(test_name="T1", test_success=True, full_response={})
        validator._record(results, result)  # should not raise
        assert len(results.results) == 1

    def test_record_multiple_appends_to_same_collection(self):
        validator = _make_validator()
        results = TestResults()
        for i in range(5):
            validator._record(results, TestResult(test_name=f"T{i}", test_success=True, full_response={}))
        assert len(results.results) == 5


class TestValidatorInit:

    def test_url_gains_trailing_slash(self):
        with patch("app.test_scripts.msr_openapi_validator.OpenAPI"), \
             patch("app.test_scripts.msr_openapi_validator.PKIServices"):
            from app.test_scripts.msr_openapi_validator import MsrOpenApiValidator
            data = _make_test_data()
            data = data.model_copy(update={"test_url": "https://example.com"})
            v = MsrOpenApiValidator(data)
        assert v.url.endswith("/")

    def test_url_with_trailing_slash_is_unchanged(self):
        with patch("app.test_scripts.msr_openapi_validator.OpenAPI"), \
             patch("app.test_scripts.msr_openapi_validator.PKIServices"):
            from app.test_scripts.msr_openapi_validator import MsrOpenApiValidator
            v = MsrOpenApiValidator(_make_test_data())
        assert v.url == "https://example.com/"

    def test_progress_callback_stored(self):
        cb = lambda r: None
        validator = _make_validator(callback=cb)
        assert validator._progress_callback is cb

    def test_no_callback_is_none(self):
        validator = _make_validator()
        assert validator._progress_callback is None
