"""
    Implementation of the Secom Search Result
"""
from uuid import UUID

from app.model.secom.enums.data_product_type import DataProductType


class ServiceInstance:
    """
        Secom Search Result class
    """
    transaction_id : UUID
    instance_id : str
    version : str
    name : str
    status : int
    description : str
    data_product_type : list[DataProductType] | None
    organization_id : str
    endpoint_uri : str
    endpoint_type : str
    keywords : list[str]
    unlocode : list[str]
    implements_designs : list[str]
    api_doc : str
    coverage_area : list[str]
    imo : int
    mmsi : int
    certificates : list[str]
    source_msr : str
    unsupported_params : list[str]

    def __init__(self, result : dict) -> None:
        transaction_id = result.get("transactionId", "")
        if transaction_id is not None and transaction_id != "":
            self.transaction_id = UUID(transaction_id)
        self.instance_id = result.get("instanceId", "")
        self.version = result.get("version", "")
        self.name = result.get("name", "")
        self.status = result.get("status", 0)
        self.description = result.get("description", "")

        self.data_product_type = []
        data_product_types = result.get("dataProductType", [])
        for data_product_type in data_product_types:
            # Normalize API value "S-124" -> "S124 to avoid breaking"
            if isinstance(data_product_type, str):
                data_product_type = data_product_type.replace("-", "")

            self.data_product_type.append(DataProductType[data_product_type])
        self.organization_id = result.get("organizationId", "")
        self.endpoint_uri = result.get("endpointUri", "")
        self.endpoint_type = result.get("endpointType", "")
        self.keywords = result.get("keywords", [])
        self.unlocode = result.get("unlocode", [])
        self.implements_designs = result.get("implementsDesigns", "")
        self.api_doc = result.get("apiDoc", "")
        self.coverage_area = result.get("coverageArea", [])
        self.instance_as_xml = result.get("instanceAsXml", "")
        self.imo = result.get("imo", 0)
        self.mmsi = result.get("mmsi", 0)
        self.certificates = result.get("certificates", [])
        self.source_msr = result.get("sourceMSRs", "")
        self.unsupported_params = result.get("unsupportedParams", [])