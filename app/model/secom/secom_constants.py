"""
    Holds the defaults for Secom connections
"""
class SecomConstants:
    """
        Default values for Secom
    """

    DATETIME_FORMAT_v2 : str = "%Y-%m-%dT%H:%M:%SZ"
    DATETIME_FORMAT_v1 : str = "%Y%m%dT%H%M%SZ"

    SECOM_VERSION_1 : str = "/v1"
    SECOM_VERSION_2 : str = "/v2"
    ACKNOWLEDGEMENT_URL : str = "/acknowledgement"
    OBJECT_URL : str = "/object"
    OBJECT_SUMMARY_URL : str = "/object/summary"
    OBJECT_BY_LINK_URL : str = "/object/link"
    PING_URL : str = "/ping"
    CAPABILITY_URL : str = "/capability"
    SUBSCRIPTION_URL : str = "/subscription"
    # SEARCH_SERVICE_URL : str = "https://msr.maritimeconnectivity.net/api/secom"
    SEARCH_SERVICE_URL : str = "https://rnavlab.gla-rad.org/mcp/msr/api/secom"
    SEARCH_SERVICE_SECOM_VERSION : str = "/v2"


class QueryStrings:
    """
        Defaults for the common query string parameters
    """

    CONTAINER_TYPE : str = "containerType"
    DATA_PRODUCT_TYPE : str = "dataProductType"
    DATA_REFERENCE : str = "dataReference"
    PRODUCT_VERSION : str = "productVersion"
    GEOMERTY : str = "geometry"
    UNLOCODE : str = "unlocode"
    CALLBACK_ENDPOINT : str = "callbackEndpoint"
    SUBSCRIPTION_PERIOD_START : str = "subscriptionPeriodStart"
    SUBSCRIPTION_PERIOD_END: str  = "subscriptionPeriodEnd"
