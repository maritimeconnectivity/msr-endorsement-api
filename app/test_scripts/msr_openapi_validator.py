import json
from collections.abc import Callable
from time import sleep
from uuid import uuid4

import requests
from openapi_core import OpenAPI
from openapi_core.contrib.requests import RequestsOpenAPIRequest, RequestsOpenAPIResponse
from shapely import wkt

from app.model.secom.v2.secom_envelope_retrieve_result import SecomEnvelopeRetrieveResult
from app.model.secom.v2.secom_envelope_search_filter import SecomEnvelopeSearchFilter
from app.model.secom.v2.secom_retrieve_result import SecomRetrieveResult
from app.model.secom.v2.secom_search_filter import SecomSearchFilter
from app.model.secom.v2.secom_search_parameters import SecomSearchParameters
from app.model.secom.v2.secom_search_result import SecomSearchResult
from app.model.test_data import TestData
from app.model.test_result import TestResult
from app.model.test_results import TestResults
from app.services.pki_services import PKIServices
from urllib.parse import urlsplit

class MsrOpenApiValidator:

    headers : dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    timeout : int = 5
    open_api : OpenAPI
    url : str
    path : str

    # Internal variables
    _pki_services : PKIServices
    _progress_callback : Callable[[TestResult], None] | None

    def __init__(self, test_data : TestData, api_path : str = "./app/schema/MSRv2.json",
                 progress_callback : Callable[[TestResult], None] | None = None):
        self._progress_callback = progress_callback

        # The spec declares paths relative to "/v2/..." while the live service is
        # served under "/api/secom/v2/...". Only the base URL differs, so we inject
        # a matching "servers" entry into the spec *in memory* (the MSRv2.json file
        # is left untouched). A relative server URL keeps this host-independent, so
        # openapi-core strips "/api/secom" before matching "/v2/searchService".
        with open(api_path, encoding="utf-8") as spec_file:
            spec_dict = json.load(spec_file)

        # Split the test URL between the base and the path
        url_parts = urlsplit(test_data.test_url)
        self.url = f"{url_parts.scheme}://{url_parts.netloc}/"
        self.path = url_parts.path

        # If a path has been specified, then add it to the OpenAPI server
        if self.path:
            spec_dict["servers"] = [{"url": self.path}]

        # And load the OpenAPI specification
        self.open_api = OpenAPI.from_dict(spec_dict)

        # Finally load the PKI service
        self._pki_services = PKIServices(public_cert=test_data.certificate,
                                         private_cert=test_data.private_key,
                                         root_cert=test_data.root_certificate)

        # And setup the test service instance
        self.test_service_instance_id = test_data.test_service_instance_id
        print(f"Initiated test_service instances: {self.test_service_instance_id}")


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
                             data=data,
                             headers=self.headers,
                             timeout=self.timeout)

        try:
            print(resp.json())
        except ValueError:
            print("Non-JSON response:")
            print("Status:", resp.status_code)
            print("Content-Type:", resp.headers.get("Content-Type"))
            print("Body:", resp.text)

        try:
            response_body = resp.json()
        except ValueError:
            response_body = {
                "serverResponse": resp.text
            }

        if resp.status_code != expected_code:
            return TestResult(test_name=test_title,
                              test_success=False,
                              full_response=response_body ,
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
                              full_response=response_body,
                              failure_reason="")

        except Exception as e:
            print("Validation failed with exception: " + str(e))
            return TestResult(test_name=test_title,
                              test_success=False,
                              full_response={ "serverResponse" : resp.text },
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
            print("-----Run retrieve test with transaction id: " + transaction_id)
            retrieve_request = SecomRetrieveResult()
            retrieve_request.envelope = SecomEnvelopeRetrieveResult(transaction_id)
            retrieve_request.envelope, signature = self._pki_services.sign_envelope_object(
                retrieve_request.envelope
            )
            retrieve_request.envelope_signature = signature



            print("Contacting URL: ", url)
            resp = requests.post(
                url,
                data=json.dumps(retrieve_request.to_secom_dict()),
                headers=self.headers,
                timeout=self.timeout
            )


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

            parsed_response = resp.json()

            return TestResult(
                test_name=test_title,
                test_success=True,
                full_response=parsed_response if isinstance(parsed_response, dict)
                else {"serverResponse": parsed_response},
                failure_reason=""
            )
        except Exception as e:
            return TestResult(test_name=test_title,
                              test_success=False,
                              full_response={ "serverResponse" : resp.text if resp is not None else "" },
                              failure_reason=str(e))


    def _record(self, test_results: TestResults, result: TestResult) -> TestResult:
        """Append result to the collection and notify the progress callback."""
        list.append(test_results.results, result)
        if self._progress_callback is not None:
            self._progress_callback(result)
        return result


    def validate_msr(self):
        """
        Validate the MSR with test queries
        :return: the test results
        """
        test_results: TestResults = TestResults()

        search_filter = self.get_new_search_filter()

        search_service_url = self.url + "api/secom/v2/searchService"
        retrieve_results_url = self.url + "api/secom/v2/retrieveResult/"

        search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
        search_filter.envelope_signature = signature

        # Test an empty search
        result = self.run_search_test(search_service_url,
                                                 json.dumps(search_filter.to_secom_dict()),
                                                 "Test empty search", 400)

        self._record(test_results, result)


        # Search for a provisional service. This is necessary since for security reasons an empty
        # query shall not return all results (DDOS vulnerability)

        search_filter = self.get_new_search_filter()


        # Test instance defined through the API
        search_filter.envelope.query.instance_id = self.test_service_instance_id

        print(f"RUN TEST FOR INSTANCE: {self.test_service_instance_id}")


        search_filter.envelope, signature = self._pki_services.sign_envelope_object(
            search_filter.envelope)
        search_filter.envelope_signature = signature
        result = self.run_search_test(search_service_url,
                                      json.dumps(search_filter.to_secom_dict()),
                                      "Test search for instance", 200)


        print(f"RESULT: {result}")
        self._record(test_results, result)

        if result.test_success:
            search_result = SecomSearchResult(result.full_response)
            envelope = search_result.envelope

            # If there is a service instance returned, test searching for it by name
            if envelope is not None and len(envelope.service_instance) > 0:

                service_instance = envelope.service_instance[0]


                # Reset the search filter
                search_filter = self.get_new_search_filter()
                search_filter.envelope.query.instance_id = service_instance.instance_id

                # Sign the envelope
                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                test_name = f"Search for {envelope.service_instance[0].name} by instance ID: {
                envelope.service_instance[0].instance_id}"
                instant_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name)

                # Check every result contains the name
                if instant_result.test_success:
                    search_result = SecomSearchResult(instant_result.full_response)

                    envelope = search_result.envelope
                    for result in envelope.service_instance:
                        if service_instance.instance_id not in result.instance_id:
                            instant_result.test_success = False
                            instant_result.failure_reason = f"Test failed: {result.instance_id} not found in {result.instance_id}"
                            break

                self._record(test_results, instant_result)

                # Test searching for a service instance by status and name
                # Reset the search filter
                search_filter = self.get_new_search_filter()

                search_filter.envelope.query.status = service_instance.status
                search_filter.envelope.query.instance_id = service_instance.instance_id
                print("-----USING STATUS ", str(service_instance.status) )


                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                test_name3 = f"Search for {service_instance.name} by status ({service_instance.status})"
                status_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name3)

                if status_result.test_success:
                    search_result = SecomSearchResult(status_result.full_response)
                    envelope = search_result.envelope
                    for result in envelope.service_instance:
                        if result.status != service_instance.status:
                            status_result.test_success = False
                            status_result.failure_reason = f"Test failed: {result.status} not found in {search_result.service_instance}"
                            break

                self._record(test_results, status_result)

                # Test searching for a service instance by geometry
                # Reset the search filter
                search_filter = self.get_new_search_filter()

                # A necessary trick because the SECOMLIB is written to accept only a Geometry and
                # not a collection of 1. An issue has been raised to fix this.
                geom = wkt.loads(service_instance.coverage_area[0])
                cleaned_geo = geom.geoms[0].wkt if geom.geom_type == "GeometryCollection" else (
                    geom.wkt)


                search_filter.envelope.geometry = cleaned_geo

                search_filter.envelope.query.instance_id = service_instance.instance_id

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                test_name = (f"Search for {envelope.service_instance[0].name} by "
                             f"geometry")
                geometry_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name)

                self._record(test_results, geometry_result)

                # Reset the search filter
                search_filter = self.get_new_search_filter()

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                # Test incorrect envelope signature results in a 400
                test_name = "Test incorrect envelope signature generates a 400 response"

                # Reset the search filter
                search_filter = self.get_new_search_filter()

                search_filter.envelope.query.instance_id = service_instance.instance_id

                # Generate the envelope signature
                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                # Change the signature such that it becomes malformed
                search_filter.envelope_signature = search_filter.envelope_signature[:-1]

                bad_signature_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name, 400)

                self._record(test_results, bad_signature_result)

                # Test failure in authentication when conducting a search yields 401 response
                test_name = "Test unauthorised search generates a 401 response"

                # Reset the search filter
                search_filter = self.get_new_search_filter()

                search_filter.envelope.query.instance_id = service_instance.instance_id

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                # Now alter the envelope so signature validation should fail on server side
                search_filter.envelope.query.instance_id = "GIBBERISH"

                # A

                auth_fail_result = self.run_search_test(search_service_url, json.dumps(
                    search_filter.to_secom_dict()), test_name, 401)
                
                self._record(test_results, auth_fail_result)

                # Reset the search filter
                search_filter = self.get_new_search_filter()

                # Test invalid status search result in a 400
                test_name = "Test invalid status search generates a 400 response"
                search_filter.envelope.query.status = 5
                search_filter.envelope.local_only = False

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                invalid_search_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name, 400)

                self._record(test_results, invalid_search_result)

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

                self._record(test_results, empty_search_result)

                # Reset the search filter
                # Test searching for a service instance by imo number alone results in a 400
                search_filter = self.get_new_search_filter()
                search_filter.envelope.query.imo = "9999999"

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                test_name = "Test search by imo number alone results in a 400 response"
                imo_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name, 400)
                self._record(test_results, imo_result)

                # Reset the search filter
                # Test searching for a service instance by mmsi number alone results in a 400
                search_filter = self.get_new_search_filter()
                search_filter.envelope.query.mmsi = "999999999"

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                test_name = "Test search by mmsi number alone results in a 400 response"
                mmsi_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()),
                                                  test_name, 400)
                self._record(test_results, mmsi_result)

                # Start a global search
                # Reset the search filter
                search_filter = self.get_new_search_filter()
                search_filter.envelope.local_only = False
                search_filter.envelope.query.instance_id = self.test_service_instance_id

                search_filter.envelope, signature = self._pki_services.sign_envelope_object(search_filter.envelope)
                search_filter.envelope_signature = signature

                test_name = "Test a global search"

                global_search_test_result = self.run_search_test(search_service_url, json.dumps(search_filter.to_secom_dict()), test_name)

                self._record(test_results, global_search_test_result)

                global_search_result = SecomSearchResult(global_search_test_result.full_response)
                envelope = global_search_result.envelope

                test_name = f"Wait 3 seconds then retrieve results for transaction id"

                if global_search_result is not None:
                    transaction_id = envelope.transaction_id
                    test_name = test_name + f": {transaction_id}"

                    # First attempt to retrieve the result
                    sleep(3)
                    retrieve_result_3s = self.run_retrieve_test(retrieve_results_url + transaction_id,
                                                                str(transaction_id), test_name, 200)
                    self._record(test_results, retrieve_result_3s)

                    # Second attempt to retrieve the result
                    sleep(3)
                    test_name = f"Wait 6 seconds then retrieve results for transaction id: {transaction_id}"
                    retrieve_result_6s = self.run_retrieve_test(retrieve_results_url  + transaction_id, str(transaction_id), test_name, 200)
                    self._record(test_results, retrieve_result_6s)

                    # Final attempt to retrieve the result
                    sleep(4)
                    test_name = f"Wait 10 seconds then retrieve results for transaction id: {transaction_id}"
                    retrieve_result_10s = self.run_retrieve_test(retrieve_results_url  + transaction_id, str(transaction_id), test_name, 200)
                    self._record(test_results, retrieve_result_10s)

                else:
                    retrieve_result_3s = TestResult(
                        test_name=test_name,
                        test_success=False,
                        full_response={ "test_skipped" : "No transaction id found in global search result" },
                        failure_reason="No transaction id found in global search result"
                    )
                    self._record(test_results, retrieve_result_3s)

                test_name = "Test retrieve results for random transaction id generates a 404 response"
                uuid = uuid4()
                invalid_transation_id_result = self.run_retrieve_test(retrieve_results_url + str(uuid),
                                                                      str(uuid), test_name, 404)

                self._record(test_results, invalid_transation_id_result)

            # Return an error that is visible in Postman, when the MSR has zero instances
            else:
                err_no_instance = (
                    TestResult(test_name="ERR NO INSTANCE",
                                  full_response={ "test_skipped" : "No service instances found in MSR, unable to test searching by instance ID, status and geometry" },
                                  test_success=False,
                                  failure_reason=f"Provide at least one instance to the MSR to "
                                                 f"test full functionality",))
                self._record(test_results, err_no_instance)

        else:
            print(f"Failed to validate MSR against test instance {self.test_service_instance_id}:")
            failRes = TestResult(
                test_name="PROVISIONAL INSTANCE SEARCH",
                test_success=False,
                full_response={
                    "test_skipped": "No provisional instance found"
                },
                failure_reason=(
                    "CANNOT VALIDATE MSR WHEN A VALID RESULT FROM A PROVISIONAL INSTANCE COULD "
                    "NOT BE PARSED"
                )
            )
            self._record(test_results, failRes)

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
