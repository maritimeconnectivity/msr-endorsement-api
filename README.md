# MSR Endorsement API

This is the first implementation of the Maritime Service Registry (MSR) endorsement system. The API is intended to run 
several tests to ensure an implementation confirms to the specification provided as well as the functional requirements 
specified in the [G1191 IALA Guideline](https://www.iala.int/product/g1191/).

## Background

Each MSR implementation should be capable of performing a global search by linking to other MSR implementations. In order 
to ensure interoperability, the MSR endorsement API should be used to perform a number of tests to check the compliance 
of the implementation.

## Usage

The API is written in Python using the FastAPI framework. To run the API, clone it to a local folder, then 
run the following commands:

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn main:app

You should see the following output:

    INFO:     Started server process [35164]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

## Tests
### First time setup
The first time you run the tests, you need to configure Postman. Open Postman and import the 
`MSR Endorsement.postman_collection.json` file in the `Postman` folder. To do this, click File > Import then select the 
file. With the tests imported, you need to configure the environment variables. In the list on the left, click on the
`MSR Endorsement` item, then click on `Variables` in the main window. There are four variables pre-defined.

- `MSR_Address`: The URL of the MSR implementation you want to test.
- `Public_Cert`: The public certificate of the MSR implementation.
- `Private_Cert`: The private certificate of the MSR implementation.
- `Root_CA_Cert`: The root certificate of the MSR implementation.

The three certificate variables are base64 encoded strings. On linux, you can use the following command to encode a 
file:

    base64 -w 0 <filename>

Copy and paste the output into the corresponding variable.

### Running the tests
Ensure the correct url has been configured in the variables tab, then click on the `Run` button near the top of the 
window. On the next page, click `Run MSR Endorsement`

When the test has completed, you should see two test results. The first shows if running the tests was successful, 
and the second shows if all tests passed. If any tests failed, you can select the `Console Log` tab to see which ones
failed and the reason for failure.