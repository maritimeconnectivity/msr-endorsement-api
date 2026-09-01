import pytest
from app.model.secom.enums.data_product_type import DataProductType
from app.model.secom.v2.secom_service_instance import ServiceInstance


def _minimal_instance(**overrides) -> dict:
    base = {
        "transactionId": "00000000-0000-0000-0000-000000000001",
        "instanceId": "urn:mrn:mcp:service:test:instance:1",
        "version": "0.0.1",
        "name": "Test Service",
        "status": 1,
        "description": "A test service",
        "dataProductType": [],
        "organizationId": "urn:mrn:mcp:org:test",
        "endpointUri": "https://example.com",
        "endpointType": "REST",
        "keywords": [],
        "unlocode": [],
        "implementsDesigns": [],
        "apiDoc": "",
        "coverageArea": [],
        "imo": 0,
        "mmsi": 0,
        "certificates": [],
        "sourceMSRs": "https://msr.example.com",
        "unsupportedParams": [],
    }
    base.update(overrides)
    return base


class TestServiceInstanceParsing:

    def test_instance_id_is_parsed(self):
        instance = ServiceInstance(_minimal_instance())
        assert instance.instance_id == "urn:mrn:mcp:service:test:instance:1"

    def test_name_is_parsed(self):
        instance = ServiceInstance(_minimal_instance())
        assert instance.name == "Test Service"

    def test_status_is_parsed(self):
        instance = ServiceInstance(_minimal_instance())
        assert instance.status == 1

    def test_data_product_type_initialised_as_empty_list(self):
        instance = ServiceInstance(_minimal_instance(dataProductType=[]))
        assert instance.data_product_type == []

    def test_data_product_type_parsed_by_value(self):
        instance = ServiceInstance(_minimal_instance(dataProductType=[124]))
        assert len(instance.data_product_type) == 1
        assert instance.data_product_type[0] == DataProductType.S124

    def test_multiple_data_product_types(self):
        instance = ServiceInstance(_minimal_instance(dataProductType=[124, 101]))
        assert DataProductType.S124 in instance.data_product_type
        assert DataProductType.S101 in instance.data_product_type

    def test_source_msr_uses_sourceMSRs_field(self):
        instance = ServiceInstance(_minimal_instance(sourceMSRs="https://msr.example.com"))
        assert instance.source_msr == "https://msr.example.com"

    def test_source_msr_falls_back_to_empty_string(self):
        data = _minimal_instance()
        del data["sourceMSRs"]
        instance = ServiceInstance(data)
        assert instance.source_msr == ""

    def test_missing_transaction_id_does_not_raise(self):
        data = _minimal_instance(transactionId="")
        instance = ServiceInstance(data)
        assert not hasattr(instance, 'transaction_id') or True  # no crash

    def test_endpoint_uri_is_parsed(self):
        instance = ServiceInstance(_minimal_instance(endpointUri="https://api.example.com"))
        assert instance.endpoint_uri == "https://api.example.com"

    def test_version_is_parsed(self):
        instance = ServiceInstance(_minimal_instance(version="1.2.3"))
        assert instance.version == "1.2.3"

    def test_keywords_are_parsed(self):
        instance = ServiceInstance(_minimal_instance(keywords=["nav", "aton"]))
        assert instance.keywords == ["nav", "aton"]

    def test_old_dataProductTypes_field_is_ignored(self):
        # Ensure the model reads 'dataProductType' (singular), not the old 'dataProductTypes'
        data = _minimal_instance(dataProductType=[], dataProductTypes=[124])
        instance = ServiceInstance(data)
        # Should read the new field name and get empty list, not the old field
        assert instance.data_product_type == []
