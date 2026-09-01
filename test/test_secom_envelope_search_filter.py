import pytest
from app.model.secom.v2.secom_envelope_search_filter import SecomEnvelopeSearchFilter
from app.model.secom.v2.secom_search_parameters import SecomSearchParameters


def _make_filter(**query_kwargs) -> SecomEnvelopeSearchFilter:
    f = SecomEnvelopeSearchFilter()
    f.query = SecomSearchParameters(**query_kwargs)
    f.envelope_root_certificate_thumbprint = "abc123"
    f.envelope_signature_certificate = ["CERTDATA"]
    return f


class TestSecomEnvelopeSearchFilterToSecomDict:

    def test_local_only_defaults_to_true(self):
        f = SecomEnvelopeSearchFilter()
        assert f.local_only is True

    def test_local_only_false_is_serialised(self):
        f = _make_filter()
        f.local_only = False
        assert f.to_secom_dict()["localOnly"] is False

    def test_query_is_included_as_dict(self):
        f = _make_filter(name="Test")
        d = f.to_secom_dict()
        assert "query" in d
        assert d["query"]["name"] == "Test"

    def test_empty_query_produces_empty_query_dict(self):
        f = SecomEnvelopeSearchFilter()
        f.envelope_root_certificate_thumbprint = "abc"
        f.envelope_signature_certificate = []
        d = f.to_secom_dict()
        assert d["query"] == {}

    def test_geometry_is_omitted_when_none(self):
        f = _make_filter()
        assert "geometry" not in f.to_secom_dict()

    def test_geometry_is_included_when_set(self):
        f = _make_filter()
        f.geometry = "POINT(0 0)"
        assert f.to_secom_dict()["geometry"] == "POINT(0 0)"

    def test_certificate_thumbprint_is_included(self):
        f = _make_filter()
        assert f.to_secom_dict()["envelopeRootCertificateThumbprint"] == "abc123"

    def test_signature_time_is_formatted_correctly(self):
        f = _make_filter()
        time_str = f.to_secom_dict()["envelopeSignatureTime"]
        # Format: 2024-01-01T12:00:00Z
        assert "T" in time_str
        assert time_str.endswith("Z")


class TestSecomEnvelopeSearchFilterPayloadToBytes:

    def test_payload_is_bytes(self):
        f = _make_filter()
        assert isinstance(f.payload_to_bytes(), bytes)

    def test_geometry_appears_in_payload(self):
        f = _make_filter()
        f.geometry = "POINT(1 2)"
        assert b"POINT(1 2)" in f.payload_to_bytes()

    def test_local_only_appears_as_lowercase(self):
        f = _make_filter()
        f.local_only = True
        assert b"true" in f.payload_to_bytes()

    def test_certificate_thumbprint_appears_in_payload(self):
        f = _make_filter()
        assert b"abc123" in f.payload_to_bytes()
