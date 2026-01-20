import json
from time import sleep
from uuid import uuid4

import requests

from openapi_core import OpenAPI
from openapi_core.contrib.requests import RequestsOpenAPIRequest, RequestsOpenAPIResponse
from openapi_core.validation.response.exceptions import InvalidData
from requests import RequestException

from app.model.secom.v2.secom_envelope_search_filter import SecomEnvelopeSearchFilter
from app.model.secom.v2.secom_search_filter import SecomSearchFilter
from app.model.secom.v2.secom_search_parameters import SecomSearchParameters
from app.model.secom.v2.secom_search_result import SecomSearchResult
from app.model.test_data import TestData
from app.model.test_result import TestResult
from app.model.test_results import TestResults
from app.services.pki_services import PKIServices


class MsrOpenApiValidator:

    headers : dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    timeout : int = 5
    open_api : OpenAPI
    url : str

    # Internal variables
    _pki_services : PKIServices

    def __init__(self, test_data : TestData, api_path : str = "./app/schema/MSRv2.json"):
        self.open_api = OpenAPI.from_file_path(api_path)
        self.url = test_data.test_url
        if self.url[-1] != "/":
            self.url = self.url + "/"

        self._pki_services = PKIServices(public_cert=test_data.certificate,
                                         private_cert=test_data.private_key,
                                         root_cert=test_data.root_certificate)



    def run_search_test(self, url : str, data: str, test_title : str, expected_code : int = 200) -> TestResult:
        """
        Query the MSR with the given data
        :param url: The URL to query
        :param data: Search filter data
        :param test_title: The title of the test
        :param expected_code: The expected HTTP status code
        :return: the result and either the search result or the exceptions
        """
        resp = requests.post(url,
                             cert=self._pki_services.get_client_certificate(),
                             data=data,
                             headers=self.headers,
                             timeout=self.timeout)

        if resp.status_code != expected_code:
            return TestResult(test_name=test_title,
                              test_success=False,
                              full_response=resp.json() ,
                              failure_reason=f"Expected status code {expected_code}, got {resp.status_code}")

        # Wrap the request objects with adapters
        openapi_request = RequestsOpenAPIRequest(resp.request)
        openapi_response = RequestsOpenAPIResponse(resp)

        try:
            # Validate + unmarshal the response against the request
            # self.open_api.validate_request(openapi_request)
            self.open_api.validate_response(openapi_request, openapi_response)
            return TestResult(test_name=test_title,
                              test_success=True,
                              full_response=resp.json(),
                              failure_reason="")

        except Exception as e:
            return TestResult(test_name=test_title,
                              test_success=False,
                              full_response={ "serverResponse" : resp.text },
                              failure_reason=str(e))


    def run_unauthorised_search_test(self, url : str, data : str, test_title : str, expected_code : int) -> TestResult:
        """
        Try a valid query without a certificate
        :param url: The URL to query
        :param data: The faulty data structure to send
        :param test_title: The title of the test
        :param expected_code: The expected HTTP status code
        :return: the result and either the search result or failure text
        """
        try:
            resp = requests.post(url,
                                 data=data,
                                 headers=self.headers,
                                 timeout=self.timeout)

            if resp.status_code != expected_code:
                return TestResult(test_name=test_title,
                                  test_success=False,
                                  full_response=resp.json(),
                                  failure_reason=f"Expected status code {expected_code}, got {resp.status_code}")
            else:
                return TestResult(test_name=test_title,
                                  test_success=resp.status_code == expected_code,
                                  full_response=resp.json(),
                                  failure_reason="")

        except RequestException as e:
            if resp is not None:
                return TestResult(test_name=test_title,
                                  test_success=resp.status_code == expected_code,
                                  full_response={ "serverResponse" :  resp.text },
                                  failure_reason=str(e))
            else:
                return TestResult(test_name=test_title,
                                  test_success=False,
                                  full_response={ "serverResponse" :  "" },
                                  failure_reason=str(e))

    def run_retrieve_test(self, url : str, transaction_id: str, test_title : str, expected_code : int = 200) -> TestResult:
        """
        Try a retrieve result request with the given transaction id and check the response code
        :param url: the url of the retrieve service
        :param transaction_id: the transaction id to retrieve
        :param test_title: The title of the test
        :param expected_code: the expected response code
        :return: the result and either the search result or failure text
        """
        try:
            resp = requests.get(url + f"/{transaction_id}",
                                cert=self._pki_services.get_client_certificate(),
                                headers=self.headers,
                                timeout=self.timeout)

            if resp.status_code != expected_code:
                return TestResult(test_name=test_title,
                                  test_success=False,
                                  full_response={ "serverResponse" :resp.text },
                                  failure_reason=f"Expected status code {expected_code}, got {resp.status_code}")

            # Wrap the request objects with adapters
            openapi_request = RequestsOpenAPIRequest(resp.request)
            openapi_response = RequestsOpenAPIResponse(resp)

            # Validate + unmarshal the response against the request
            # self.open_api.validate_request(openapi_request)
            self.open_api.validate_response(openapi_request, openapi_response)
            return TestResult(test_name=test_title,
                              test_success=True,
                              full_response=resp.json(),
                              failure_reason="")

        except Exception as e:
            return TestResult(test_name=test_title,
                              test_success=False,
                              full_response={ "serverResponse" : resp.text if resp is not None else "" },
                              failure_reason=str(e))


    def validate_msr(self):
        """
        Validate the MSR with test queries
        :return: the test results
        """
        test_results: TestResults = TestResults()

        search_filter = self.get_new_search_filter()

        search_service_url = self.url + "api/secom/v2/searchService"
        retrieve_results_url = self.url + "api/secom/v2/retrieveResults"

        search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
        search_filter.envelope_signature = signature

        # Test an empty search
        result = self.run_search_test(search_service_url,
                                                 json.dumps(search_filter.to_secom_dict()),
                                                 "Test empty search")

        test_results.results.append(result)

        if result.test_success:
            search_result = SecomSearchResult(result.full_response)

            # If there is a service instance returned, test searching for it by name
            if search_result is not None and len(search_result.service_instance) > 0:

                service_instance = search_result.service_instance[0]

                # Reset the search filter
                search_filter = self.get_new_search_filter()
                search_filter.envelope.query.instance_id = service_instance.instance_id

                # Sign the envelope
                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                test_name = f"Search for {search_result.service_instance[0].name} by instance ID: {search_result.service_instance[0].instance_id}"
                instant_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name)

                # Check every result contains the name
                if instant_result.test_success:
                    search_result = SecomSearchResult(instant_result.full_response)
                    for result in search_result.service_instance:
                        if service_instance.instance_id not in result.instance_id:
                            instant_result.test_success = False
                            instant_result.failure_reason = f"Test failed: {result.instance_id} not found in {result.instance_id}"
                            break

                test_results.results.append(instant_result)

                # Test searching for a service instance by status
                # Reset the search filter
                search_filter = self.get_new_search_filter()
                search_filter.envelope.query.status = service_instance.status

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                test_name3 = f"Search for {service_instance.name} by status ({service_instance.status})"
                status_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name3)

                if status_result.test_success:
                    search_result = SecomSearchResult(status_result.full_response)
                    for result in search_result.service_instance:
                        if result.status != service_instance.status:
                            status_result.test_success = False
                            status_result.failure_reason = f"Test failed: {result.status} not found in {search_result.service_instance}"
                            break

                test_results.results.append(status_result)

                # Test searching for a service instance by geometry
                # Reset the search filter
                search_filter = self.get_new_search_filter()
                search_filter.envelope.geometry = service_instance.coverage_area[0]

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                test_name = f"Search for {search_result.service_instance[0].name} by geometry"
                geometry_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name)

                test_results.results.append(geometry_result)

                # Reset the search filter
                search_filter = self.get_new_search_filter()

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                # Test incorrect envelope signature results in a 400
                test_name = "Test incorrect envelope signature generates a 400 response"

                # Reset the search filter
                search_filter = self.get_new_search_filter()

                # Generate the envelope signature
                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                # Change the query so the signature is incorrect
                search_filter.envelope.query.name = search_result.service_instance[0].name

                bad_signature_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name, 400)

                test_results.results.append(bad_signature_result)

                # Test unauthorised access to the search service
                test_name = "Test unauthorised search generates a 401 response"

                # Reset the search filter
                search_filter = self.get_new_search_filter()

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature
                unauth_result = self.run_unauthorised_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name, 401)
                
                test_results.results.append(unauth_result)

                # Reset the search filter
                search_filter = self.get_new_search_filter()

                # Test invalid status search result in a 400
                test_name = "Test invalid status search generates a 400 response"
                search_filter.envelope.query.status = "!!INVALID!!"

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                invalid_search_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name, 400)

                test_results.results.append(invalid_search_result)

                # Reset the search filter
                search_filter = self.get_new_search_filter()

                # Test 404 is returned when no results are found
                test_name = "Test no results found generates a 404 response"

                # Reset the search filter
                search_filter = self.get_new_search_filter()
                search_filter.envelope.query.name = "INVALID SERVICE NAME - SHOULD NOT BE FOUND"

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                empty_search_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name, 404)

                test_results.results.append(empty_search_result)

                # Reset the search filter
                # Test searching for a service instance by imo number alone results in a 400
                search_filter = self.get_new_search_filter()
                search_filter.envelope.query.imo = "9999999"

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                test_name = "Test search by imo number alone results in a 400 response"
                imo_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name, 400)
                test_results.results.append(imo_result)

                # Reset the search filter
                # Test searching for a service instance by mmsi number alone results in a 400
                search_filter = self.get_new_search_filter()
                search_filter.envelope.query.mmsi = "999999999"

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                test_name = "Test search by mmsi number alone results in a 400 response"
                mmsi_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()),
                                                  test_name, 400)
                test_results.results.append(mmsi_result)

                # Start a global search
                # Reset the search filter
                search_filter = self.get_new_search_filter()
                search_filter.envelope.local_only = False

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                test_name = "Test a global search"

                global_search_test_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name)

                test_results.results.append(global_search_test_result)

                global_search_result = SecomSearchResult(global_search_test_result.full_response)

                test_name = f"Wait 3 seconds then retrieve results for transaction id"
                if global_search_result is not None and len(global_search_result.service_instance) > 0 and \
                    hasattr(global_search_result.service_instance[0], "transaction_id"):
                    transaction_id = global_search_result.service_instance[0].transaction_id
                    test_name = test_name + f": {transaction_id}"

                    # First attempt to retrieve the result
                    sleep(3)
                    retrieve_result_3s = self.run_retrieve_test(retrieve_results_url, str(transaction_id), test_name, 200)
                    test_results.results.append(retrieve_result_3s)

                    # Second attempt to retrieve the result
                    sleep(3)
                    test_name = f"Wait 6 seconds then retrieve results for transaction id: {transaction_id}"
                    retrieve_result_6s = self.run_retrieve_test(retrieve_results_url, str(transaction_id), test_name, 200)
                    test_results.results.append(retrieve_result_6s)

                    # Final attempt to retrieve the result
                    sleep(4)
                    test_name = f"Wait 10 seconds then retrieve results for transaction id: {transaction_id}"
                    retrieve_result_10s = self.run_retrieve_test(retrieve_results_url, str(transaction_id), test_name, 200)
                    test_results.results.append(retrieve_result_10s)

                else:
                    retrieve_result_3s = TestResult(
                        test_name=test_name,
                        test_success=False,
                        full_response={ "test_skipped" : "No transaction id found in global search result" },
                        failure_reason="No transaction id found in global search result"
                    )
                    test_results.results.append(retrieve_result_3s)

                test_name = "Test retrieve results for random transaction id generates a 404 response"
                uuid = uuid4()
                invalid_transation_id_result = self.run_retrieve_test(retrieve_results_url, str(uuid), test_name, 404)

                test_results.results.append(invalid_transation_id_result)

        self._pki_services.cleanup()

        return test_results

    @staticmethod
    def get_new_search_filter():
        """
        Get a new search filter with a valid envelope root certificate thumbprint
        :return: a new search filter
        """
        search_filter = SecomSearchFilter()
        search_filter.envelope = SecomEnvelopeSearchFilter()
        search_filter.envelope.query = SecomSearchParameters()
        return search_filter
