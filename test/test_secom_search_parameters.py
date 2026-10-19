import base64

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

    def test_organization_id_is_not_a_search_parameter(self):
        params = SecomSearchParameters(organization_id="urn:mrn:mcp:org:test")
        assert "organizationId" not in params.to_secom_dict()

    def test_mmsi_is_included(self):
        params = SecomSearchParameters(mmsi="123456789")
        assert params.to_secom_dict()["mmsi"] == "123456789"

    def test_imo_is_included(self):
        params = SecomSearchParameters(imo="9999999")
        assert params.to_secom_dict()["imo"] == "9999999"

    def test_unlocode_is_included_as_array(self):
        params = SecomSearchParameters(unlocode="GBGLW")
        assert params.to_secom_dict()["unlocode"] == ["GBGLW"]

    def test_unlocode_list_is_included(self):
        params = SecomSearchParameters(unlocode=["GBGLW", "GBLON"])
        assert params.to_secom_dict()["unlocode"] == ["GBGLW", "GBLON"]

    def test_data_product_type_uses_enum_name(self):
        params = SecomSearchParameters(data_product_type=DataProductType.S124)
        result = params.to_secom_dict()
        assert "dataProductType" in result
        assert result["dataProductType"] == [DataProductType.S124.name]

    def test_data_product_type_list(self):
        params = SecomSearchParameters(data_product_type=[DataProductType.S124, DataProductType.S201])
        assert params.to_secom_dict()["dataProductType"] == ["S124", "S201"]

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
        fields = params.payload_to_bytes().decode().split(".")
        assert fields[5] == base64.b64encode(b"S124").decode()

    def test_empty_parameters_payload_has_one_field_per_attribute(self):
        params = SecomSearchParameters()
        assert params.payload_to_bytes() == b"." * 13

    def test_strings_are_not_lowercased(self):
        params = SecomSearchParameters(version="1.0.0-Beta", instance_id="urn:mrn:Test")
        payload = params.payload_to_bytes().decode()
        assert "1.0.0-Beta" in payload
        assert "urn:mrn:Test" in payload

    def test_keywords_are_base64_encoded_and_comma_separated(self):
        params = SecomSearchParameters(keywords=["nav", "chart"])
        fields = params.payload_to_bytes().decode().split(".")
        assert len(fields) == 14
        assert fields[3] == (base64.b64encode(b"nav").decode() + "," + base64.b64encode(b"chart").decode())

    def test_attribute_order(self):
        params = SecomSearchParameters(name="N", status=1, instance_id="I", unlocode=["GBGLW"], endpoint_uri="E")
        fields = params.payload_to_bytes().decode().split(".")
        assert fields[0] == "N"
        assert fields[1] == "1"
        assert fields[8] == "I"
        assert fields[12] == base64.b64encode(b"GBGLW").decode()
        assert fields[13] == "E"
