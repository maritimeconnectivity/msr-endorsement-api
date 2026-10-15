# MSR Endorsement API

This is the first implementation of the Maritime Service Registry (MSR) endorsement system. The API is intended to run 
several tests to ensure an implementation confirms to the specification provided as well as the functional requirements 
specified in the [G1191 IALA Guideline](https://www.iala.int/product/g1191/).

## Background

Each MSR implementation should be capable of performing a global search by linking to other MSR implementations. In order 
to ensure interoperability, the MSR endorsement API should be used to perform a number of tests to check the compliance 
of the implementation.

## Usage

The validator is a Python desktop application with a PyQt6 GUI. To run it, clone the repository to a local folder,
then run the following commands:

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python gui.py

## Windows Installer

A conventient way of packaging the application as an executable is to use the
Python [pyinstaller](https://pypi.org/project/pyinstaller/) facility. This will
 gather all the required libraries and resources and package them alongside the
 code so that it can all be used as a single executable file. The 
 *`msr-endorser.spec`* specification file that controls how the installer 
 will generate this executable file is also available.

To run package a new version of the application using *pyinstaller* just run the 
following command:

```bash
pyinstaller.exe ./msr-endorser.spec   # For Windows
pyinstaller ./msr-endorser.spec       # For Linux
```

Once the operation is complete you can find the generated executable file under
the *`dist`* directory. Note that if you run the build in a Windows environment
you will get a Windows executable, while in a Linux environment you will get a
Linux executable and so on...

## Running the tests

1. In the **MSR URL** field, enter the URL of the MSR implementation you want to test (e.g. `https://example.com`).

2. In the **Test instance ID** field, enter the instance ID (MRN) of a provisional service
   instance registered in the MSR under test. This is required: for security reasons an empty
   search no longer returns all instances, so the tests use this known instance as the basis
   for the remaining checks.

3. Use the **Browse…** buttons to select the certificate files:
   - **Public certificate** — the public certificate used to sign the SECOM envelopes.
   - **Private key** — the matching private key.
   - **Root CA certificate** — the root certificate of the MSR implementation.
   - **OpenAPI Specification** — the optional OpenAPI specification to test against. If none is provided, then the
     system will use the default one as specified by SEVOM v2.0 and the MSR IALA G1191 specification.

   The files are read and base64 encoded for you, so no manual encoding step is required.

4. Click **Run tests**.

Each test result is displayed in the list as soon as it completes, marked **PASS** (green) or **FAIL** (red). Expand a
result to see the failure reason and the full server response. The status line shows a running total of how many tests
have passed, and a final summary once the run finishes.