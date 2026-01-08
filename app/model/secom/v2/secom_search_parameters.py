"""
    Implementation of the Secom Search Parameters object
"""
from app.model.secom.enums.data_product_type import DataProductType


class SecomSearchParameters:
    """
        Secom Search Parameters class implementation
    """

    name : str | None
    status : str | None
    version : str | None
    description : str | None
    data_product_type : DataProductType | None
    specification_id : str | None
    design_id : str | None
    instance_id : str | None
    organization_id : str | None
    mmsi : str | None
    imo : str | None
    service_type : str | None
    unlocode : str | None
    endpoint_uri : str | None


    def __init__(self, **filters) -> None:
        self.name = filters.get("name", None)
        self.status = filters.get("status", None)
        self.version = filters.get("version", None)
        self.description = filters.get("description", None)
        self.data_product_type = filters.get("data_product_type", None)
        self.specification_id = filters.get("specification_id", None)
        self.design_id = filters.get("design_id", None)
        self.instance_id = filters.get("instance_id", None)
        self.organization_id = filters.get("organization_id", None)
        self.mmsi = filters.get("mmsi", None)
        self.imo = filters.get("imo", None)
        self.service_type = filters.get("service_type", None)
        self.unlocode = filters.get("unlocode", None)
        self.endpoint_uri =  filters.get("endpoint_uri", None)


    def to_secom_dict(self) -> dict[str, str]:
        """
            Convert object to a Secom capatible dictionary
        """

        dictionary : dict[str, str] = {}

        if self.name is not None:
            dictionary["name"] = self.name

        if self.status is not None:
            dictionary["status"] = self.status

        if self.version is not None:
            dictionary["version"] = self.version

        if self.description is not None:
            dictionary["description"] = self.description

        if self.data_product_type is not None:
            dictionary["dataProductType"] = self.data_product_type.name

        if self.specification_id is not None:
            dictionary["specificationId"] = self.specification_id

        if self.design_id is not None:
            dictionary["designId"] = self.design_id

        if self.instance_id is not None:
            dictionary["instanceId"] = self.instance_id

        if self.organization_id is not None:
            dictionary["organizationId"] = self.organization_id

        if self.mmsi is not None:
            dictionary["mmsi"] = self.mmsi

        if self.imo is not None:
            dictionary["imo"] = self.imo

        if self.service_type is not None:
            dictionary["serviceType"] = self.service_type

        if self.unlocode is not None:
            dictionary["unlocode"] = self.unlocode

        if self.endpoint_uri is not None:
            dictionary["endpointUri"] = self.endpoint_uri

        return dictionary
