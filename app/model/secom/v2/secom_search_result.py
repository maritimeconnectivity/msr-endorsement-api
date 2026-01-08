"""
    Implementation of the Secom Search Results
"""
from app.model.secom.v2.secom_service_instance import ServiceInstance


class SecomSearchResult:
    """
        Secom Search Result class
    """

    service_instance : list[ServiceInstance]

    def __init__(self, results : dict) -> None:

        self.service_instance = []

        for result in results["serviceInstance"]:
            self.service_instance.append(ServiceInstance(result))