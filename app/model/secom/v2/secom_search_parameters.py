"""
    Implementation of the Secom Search Parameters object
"""
from app.model.secom.enums.data_product_type import DataProductType
from app.model.secom.secom_signature_utils import encode_array


class SecomSearchParameters:
    """
        Secom Search Parameters class implementation
    """

    name : str | None
    status : int | None
    version : str | None
    keywords : list[str] | None
    description : str | None
    data_product_type : list[DataProductType] | None
    specification_id : str | None
    design_id : str | None
    instance_id : str | None
    mmsi : str | None
    imo : str | None
    service_type : str | None
    unlocode : list[str] | None
    endpoint_uri : str | None


    def __init__(self, **filters) -> None:
        self.name = filters.get("name", None)
        self.status = filters.get("status", None)
        self.version = filters.get("version", None)
        self.keywords = filters.get("keywords", None)
        self.description = filters.get("description", None)
        self.data_product_type = self._as_list(filters.get("data_product_type", None))
        self.specification_id = filters.get("specification_id", None)
        self.design_id = filters.get("design_id", None)
        self.instance_id = filters.get("instance_id", None)
        self.mmsi = filters.get("mmsi", None)
        self.imo = filters.get("imo", None)
        self.service_type = filters.get("service_type", None)
        self.unlocode = self._as_list(filters.get("unlocode", None))
        self.endpoint_uri =  filters.get("endpoint_uri", None)


    @staticmethod
    def _as_list(value):
        """
        The spec defines some parameters as arrays, so wrap single values in a list
        """
        if value is None or isinstance(value, list):
            return value
        return [value]


    def to_secom_dict(self) -> dict[str, str | int | list[str]]:
        """
            Convert object to a Secom capatible dictionary
        """

        dictionary : dict[str, str | int | list[str]] = {}

        if self.name is not None:
            dictionary["name"] = self.name

        if self.status is not None:
            dictionary["status"] = self.status

        if self.version is not None:
            dictionary["version"] = self.version

        if self.keywords is not None:
            dictionary["keywords"] = self.keywords

        if self.description is not None:
            dictionary["description"] = self.description

        if self.data_product_type is not None:
            dictionary["dataProductType"] = [data_product_type.name for data_product_type in self.data_product_type]

        if self.specification_id is not None:
            dictionary["specificationId"] = self.specification_id

        if self.design_id is not None:
            dictionary["designId"] = self.design_id

        if self.instance_id is not None:
            dictionary["instanceId"] = self.instance_id

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


    def payload_to_bytes(self) -> bytes:
        """
        Generate the payload as a string for signature generation, following the
        attribute order of Table 106 and the conversion rules of Table 82
        :return: a byte string
        """
        values = [
            self.name,
            str(self.status) if self.status is not None else None,
            self.version,
            encode_array(self.keywords),
            self.description,
            encode_array([data_product_type.name for data_product_type in self.data_product_type]) if self.data_product_type is not None else None,
            self.specification_id,
            self.design_id,
            self.instance_id,
            self.mmsi,
            self.imo,
            self.service_type,
            encode_array(self.unlocode),
            self.endpoint_uri,
        ]

        payload = ".".join(value if value is not None else "" for value in values)

        return bytes(payload, encoding='utf-8')
