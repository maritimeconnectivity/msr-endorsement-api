import json
from uuid import uuid4

import requests
import tempfile
import logging
import base64
import os

from tempfile import TemporaryDirectory

from openapi_core import OpenAPI
from openapi_core.contrib.requests import RequestsOpenAPIRequest, RequestsOpenAPIResponse
from openapi_core.validation.response.exceptions import InvalidData
from requests import RequestException

from app.model.secom.secom_constants import SecomConstants
from app.model.secom.v2.secom_envelope_search_filter import SecomEnvelopeSearchFilter
from app.model.secom.v2.secom_search_filter import SecomSearchFilter
from app.model.secom.v2.secom_search_parameters import SecomSearchParameters
from app.model.secom.v2.secom_search_result import SecomSearchResult
from app.model.test_data import TestData
from app.model.test_result import TestResult
from app.model.test_results import TestResults

class MsrOpenApiValidator:


    cert : tuple[str, str]
    root_cert : str
    headers : dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    timeout : int = 30
    open_api : OpenAPI
    url : str

    __temp_folder__ : TemporaryDirectory

    def __init__(self, test_data : TestData, api_path : str = "./app/schema/MSRv2.json"):
        self.open_api = OpenAPI.from_file_path(api_path)
        self.url = test_data.test_url
        if self.url[-1] != "/":
            self.url = self.url + "/"

        self.__tempfolder__ = tempfile.TemporaryDirectory(delete=False)

        with open(self.__tempfolder__.name + "/secom.crt", "wb") as f:
            f.write(base64.b64decode(test_data.certificate))

        with open(self.__tempfolder__.name + "/secom_key.pem", "wb") as f:
            f.write(base64.b64decode(test_data.private_key))

        self.cert = (self.__tempfolder__.name + "/secom.crt", self.__tempfolder__.name + "/secom_key.pem")

        with open(self.__tempfolder__.name + "/root.crt", "wb") as f:
            f.write(base64.b64decode(test_data.root_certificate))

        self.root_cert = self.__tempfolder__.name + "/root.crt"

        logging.info(f"Temp folder: {self.__tempfolder__.name}")


    def run_search_test(self, url : str, data: str, expected_code : int = 200) -> tuple[bool, dict, str]:
        """
        Query the MSR with the given data
        :param url: The URL to query
        :param data: Search filter data
        :param expected_code: The expected HTTP status code
        :return: the result and either the search result or the exception
        """
        resp = requests.post(url,
                             cert=self.cert,
                             data=data,
                             headers=self.headers,
                             timeout=self.timeout)

        if resp.status_code != expected_code:
            return False, resp.json() ,f"Expected status code {expected_code}, got {resp.status_code}"

        # Wrap the request objects with adapters
        openapi_request = RequestsOpenAPIRequest(resp.request)
        openapi_response = RequestsOpenAPIResponse(resp)

        try:
            # Validate + unmarshal the response against the request
            # self.open_api.validate_request(openapi_request)
            self.open_api.validate_response(openapi_request, openapi_response)
            return True, resp.json(), ""

        except Exception as e:
            return False, { "serverResponse" : resp.text }, str(e)


    def run_unauthorised_search_test(self, url : str, data : str, expected_code : int) -> tuple[bool, dict, str]:
        """
        Try a valid query without a certificate
        :param url: The URL to query
        :param data: The faulty data structure to send
        :param expected_code: The expected HTTP status code
        :return: the result and either the search result or failure text
        """
        try:
            resp = requests.post(url,
                                 data=data,
                                 headers=self.headers,
                                 timeout=self.timeout)

            if resp.status_code != expected_code:
                return False, resp.json(), f"Expected status code {expected_code}, got {resp.status_code}"
            else:
                return resp.status_code == expected_code, resp.json(), ""

        except RequestException as e:
            if resp is not None:
                return resp.status_code == expected_code, { "serverResponse" :  resp.text }, str(e)
            else:
                return False, { "serverResponse" :  "" }, str(e)

    def run_retrieve_test(self, url : str, transaction_id: str, expected_code : int) -> tuple[bool, dict, str]:
        """
        Try a retrieve result request with the given transaction id and check the response code
        :param url: the url of the retrieve service
        :param transaction_id: the transaction id to retrieve
        :param expected_code: the expected response code
        :return: the result and either the search result or failure text
        """
        try:
            resp = requests.get(url + f"/{transaction_id}",
                                cert=self.cert,
                                headers=self.headers,
                                timeout=self.timeout)

            if resp.status_code != expected_code:
                return False, resp.json(), f"Expected status code {expected_code}, got {resp.status_code}"

            # Wrap the request objects with adapters
            openapi_request = RequestsOpenAPIRequest(resp.request)
            openapi_response = RequestsOpenAPIResponse(resp)

            # Validate + unmarshal the response against the request
            # self.open_api.validate_request(openapi_request)
            self.open_api.validate_response(openapi_request, openapi_response)
            return True, resp.json(), ""

        except Exception as e:
            if resp is not None:
                return False, { "serverResponse" : resp.text } ,str(e)
            else:
                return False, { "serverResponse" :  "" }, str(e)


    def validate_msr(self):
        """
        Validate the MSR with test queries
        :return: the test results
        """
        test_results: TestResults = TestResults()

        search_filter = self.get_new_search_filter()

        search_service_url = self.url + "api/secom/v2/searchService"
        retrieve_results_url = self.url + "api/secom/v2/retrieveResults"

        # Test an empty search
        (success, response, error) = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()))
        result1 = TestResult(
            test_name="Test empty search",
            test_success=success,
            full_response=response,
            failure_reason=error
        )

        test_results.results.append(result1)

        if result1.test_success:
            search_result = SecomSearchResult(result1.full_response)

            # If there is a service instance returned, test searching for it by name
            if search_result is not None and len(search_result.service_instance) > 0:
                service_instance = search_result.service_instance[0]
                search_filter = self.get_new_search_filter()
                search_filter.envelope.query.name = service_instance.name

                test_name2 = f"Search for {search_result.service_instance[0].name} by name"
                (success2, response2, failure2) = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()))
                
                result2 = TestResult(
                    test_name=test_name2,
                    test_success=success2,
                    full_response=response2,
                    failure_reason=failure2
                )

                # Check every result contains the name
                if result2.test_success:
                    search_result = SecomSearchResult(result2.full_response)
                    for result in search_result.service_instance:
                        if service_instance.name not in result.name:
                            result2.test_success = False
                            result2.failure_reason = f"Test failed: {result.name} not found in {search_result.service_instance}"
                            break

                test_results.results.append(result2)

                # Test searching for a service instance by status
                # Reset the search filter
                search_filter = self.get_new_search_filter()
                search_filter.envelope.query.status = service_instance.status

                test_name3 = f"Search for {service_instance.name} by status ({service_instance.status})"
                (success3, response3, failure3) = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()))
                
                result3 = TestResult(
                    test_name=test_name3,
                    test_success=success3,
                    full_response=response3,
                    failure_reason=failure3
                )
                
                if result3.test_success:
                    search_result = SecomSearchResult(result3.full_response)
                    for result in search_result.service_instance:
                        if result.status != service_instance.status:
                            result3.test_success = False
                            result3.failure_reason = f"Test failed: {result.status} not found in {search_result.service_instance}"
                            break

                test_results.results.append(result3)

                # Test searching for a service instance by geometry
                # Reset the search filter
                search_filter = self.get_new_search_filter()
                search_filter.envelope.geometry = service_instance.coverage_area[0]

                test_name4 = f"Search for {search_result.service_instance[0].name} by geometry"
                (success4, response4, failure4) = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()))
                
                result4 = TestResult(
                    test_name=test_name4,
                    test_success=success4,
                    full_response=response4,
                    failure_reason=failure4
                )
                test_results.results.append(result4)

                # Reset the search filter
                search_filter = self.get_new_search_filter()

                # Test unauthorised access to the search service
                test_name5 = "Test unauthorised search generates a 401 response"
                (success5, response5, failure5) = self.run_unauthorised_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), 401)
                
                result5 = TestResult(
                    test_name=test_name5,
                    test_success=success5,
                    full_response=response5,
                    failure_reason=failure5
                )
                test_results.results.append(result5)

                # Reset the search filter
                search_filter = self.get_new_search_filter()

                # Test invalid status search result in a 400
                test_name6 = "Test invalid status search generates a 400 response"
                search_filter.envelope.query.status = "!!INVALID!!"
                (success6, response6, failure6) = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), 400)
                
                result6 = TestResult(
                    test_name=test_name6,
                    test_success=success6,
                    full_response=response6,
                    failure_reason=failure6
                )
                test_results.results.append(result6)

                # Reset the search filter
                search_filter = self.get_new_search_filter()

                # Test 404 is returned when no results are found
                test_name7 = "Test no results found generates a 404 response"
                search_filter.envelope.query.name = "INVALID SERVICE NAME - SHOULD NOT BE FOUND"
                (success7, response7, failure7) = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), 404)

                result7 = TestResult(
                    test_name=test_name7,
                    test_success=success7,
                    full_response=response7,
                    failure_reason=failure7
                )
                test_results.results.append(result7)

                # Start a global search
                # Reset the search filter
                search_filter = self.get_new_search_filter()
                search_filter.local_only = False

                (success8, response8, failure8) = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()))

                result8 = TestResult(
                    test_name="Test a global search",
                    test_success=success8,
                    full_response=response8,
                    failure_reason=failure8
                )
                test_results.results.append(result8)

                global_search_result = SecomSearchResult(response8)

                test_name9 = f"Test retrieve results for transaction id"
                if global_search_result is not None and len(global_search_result.service_instance) > 0 and \
                    hasattr(global_search_result.service_instance[0], "transaction_id"):
                    transaction_id = global_search_result.service_instance[0].transaction_id
                    test_name9 = test_name9 + f": {transaction_id}"
                    (success9, response9, failure9) = self.run_retrieve_test(retrieve_results_url, str(transaction_id), 200)
                    result9 = TestResult(
                        test_name=test_name9,
                        test_success=success9,
                        full_response=response9,
                        failure_reason=failure9
                    )
                    test_results.results.append(result9)
                else:
                    result9 = TestResult(
                        test_name=test_name9,
                        test_success=False,
                        full_response={ "test_skipped" : "No transaction id found in global search result" },
                        failure_reason="No transaction id found in global search result"
                    )
                    test_results.results.append(result9)

                test_name10 = "Test retrieve results for invalid transaction id generates a 404 response"
                uuid = uuid4()
                (success10, response10, failure10) = self.run_retrieve_test(retrieve_results_url, str(uuid), 404)
                result10 = TestResult(
                    test_name=test_name10,
                    test_success=success10,
                    full_response=response10,
                    failure_reason=failure10
                )
                test_results.results.append(result10)

        self.__tempfolder__.cleanup()

        return test_results

    @staticmethod
    def get_new_search_filter():
        """
        Get a new search filter with a valid envelope root certificate thumbprint
        :return: a new search filter
        """
        search_filter = SecomSearchFilter()
        search_filter.envelope = SecomEnvelopeSearchFilter()
        search_filter.envelope.envelope_root_certificate_thumbprint = "E42BDBD655F88D2686A7F76F558A8C2F835542F3"
        search_filter.envelope.query = SecomSearchParameters()
        search_filter.envelope_signature = "123123123"
        return search_filter
