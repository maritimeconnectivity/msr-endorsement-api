import pytest
from app.model.secom.enums.data_product_type import DataProductType
from app.model.secom.v2.secom_search_parameters import SecomSearchParameters


class TestSecomSearchParametersToSecomDict:

    def test_empty_parameters_produces_empty_dict(self):
        params = SecomSearchParameters()
        assert params.to_secom_dict() == {}

    def test_name_is_included(self):
        params = SecomSearchParameters(name="My Service")
        assert params.to_secom_dict()["name"] == "My Service"

    def test_status_is_included(self):
        params = SecomSearchParameters(status=1)
        assert params.to_secom_dict()["status"] == 1

    def test_instance_id_is_included(self):
        params = SecomSearchParameters(instance_id="urn:mrn:mcp:service:test")
        assert params.to_secom_dict()["instanceId"] == "urn:mrn:mcp:service:test"

    def test_organization_id_is_included(self):
        params = SecomSearchParameters(organization_id="urn:mrn:mcp:org:test")
        assert params.to_secom_dict()["organizationId"] == "urn:mrn:mcp:org:test"

    def test_mmsi_is_included(self):
        params = SecomSearchParameters(mmsi="123456789")
        assert params.to_secom_dict()["mmsi"] == "123456789"

    def test_imo_is_included(self):
        params = SecomSearchParameters(imo="9999999")
        assert params.to_secom_dict()["imo"] == "9999999"

    def test_unlocode_is_included(self):
        params = SecomSearchParameters(unlocode="GBGLW")
        assert params.to_secom_dict()["unlocode"] == "GBGLW"

    def test_data_product_type_uses_enum_name(self):
        params = SecomSearchParameters(data_product_type=DataProductType.S124)
        result = params.to_secom_dict()
        assert "dataProductType" in result
        assert result["dataProductType"] == DataProductType.S124.name

    def test_none_fields_are_omitted(self):
        params = SecomSearchParameters(name="Test")
        d = params.to_secom_dict()
        assert "status" not in d
        assert "instanceId" not in d
        assert "mmsi" not in d

    def test_keywords_are_included(self):
        params = SecomSearchParameters(keywords=["nav", "chart"])
        assert params.to_secom_dict()["keywords"] == ["nav", "chart"]

    def test_multiple_fields(self):
        params = SecomSearchParameters(name="Test", status=1, instance_id="urn:test")
        d = params.to_secom_dict()
        assert d["name"] == "Test"
        assert d["status"] == 1
        assert d["instanceId"] == "urn:test"


class TestSecomSearchParametersPayloadToBytes:

    def test_empty_parameters_returns_bytes(self):
        params = SecomSearchParameters()
        result = params.payload_to_bytes()
        assert isinstance(result, bytes)

    def test_name_appears_in_payload(self):
        params = SecomSearchParameters(name="TestService")
        assert b"TestService" in params.payload_to_bytes()

    def test_instance_id_appears_in_payload(self):
        params = SecomSearchParameters(instance_id="urn:mrn:test")
        assert b"urn:mrn:test" in params.payload_to_bytes()

    def test_payload_is_dot_separated(self):
        params = SecomSearchParameters(name="A", status=1)
        payload = params.payload_to_bytes().decode()
        assert "." in payload

    def test_status_appears_in_payload(self):
        params = SecomSearchParameters(status=2)
        assert b"2" in params.payload_to_bytes()

    def test_data_product_type_appears_in_payload(self):
        params = SecomSearchParameters(data_product_type=DataProductType.S124)
        payload = params.payload_to_bytes().decode().lower()
        assert "s124" in payload
