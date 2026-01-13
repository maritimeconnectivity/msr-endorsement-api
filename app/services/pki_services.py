"""
    Service used to generate signatures and certificate hashes
"""
import base64
from datetime import datetime
import logging
from hashlib import sha3_384, sha384
from collections.abc import Callable
import tempfile
from tempfile import TemporaryDirectory

from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.hashes import SHA256
import cryptography.hazmat.primitives.hashes as hashes

import ecdsa
from ecdsa import BadSignatureError
from ecdsa.util import sigencode_der, sigdecode_der

from app.model.exceptions.signature_validation_exception import SignatureValidationException
from app.model.secom.v2.secom_envelope import SecomEnvelope


class PKIServices:
    """
        Class providing methods to sign and generate certificate hashes
    """

    root_ca_cert : bytes
    root_ca_fingerprint : str
    root_ca_fingerprint_hash_algorithm : str
    public_key : str
    private_key : str
    private_key_password : str | None
    digital_signature_reference : hashes.HashAlgorithm = sha3_384
    protection_scheme = "SECOM"

    # Private variables
    __temp_folder__ : TemporaryDirectory

    def __init__(self, public_cert : str, private_cert : str, root_cert : str) -> None:
        """
        Create a new instance of PKIServices
        :param public_cert: The public certificate string
        :param private_cert: The private certificate string
        :param root_cert: The root certificate string
        """

        self.__tempfolder__ = tempfile.TemporaryDirectory(delete=False)

        self.public_key = self.__tempfolder__.name + "/public_cert.pem"
        with open(self.public_key, "wb") as f:
            f.write(base64.b64decode(public_cert))

        self.private_key = self.__tempfolder__.name + "/private_cert.pem"
        with open(self.private_key, "wb") as f:
            f.write(base64.b64decode(private_cert))

        self.root_ca_cert = base64.b64decode(root_cert)
        self.root_ca_fingerprint, self.root_ca_fingerprint_hash_algorithm = self.calculate_ca_certificate_fingerprint()

        logging.info(f"Temp folder: {self.__tempfolder__.name}")


    def calculate_ca_certificate_fingerprint(self,
                                             hash_algorithm : hashes.HashAlgorithm = SHA256()) -> tuple[str, str]:
        """
            Opens the file provided and stores the content in 
            root_ca. Also calculates the fingerprint of the certificate using SHA256

        """

        x509_certificate = load_pem_x509_certificate(self.root_ca_cert)
        root_ca_fingerprint = x509_certificate.fingerprint(algorithm=hash_algorithm).hex()
        root_ca_fingerprint_hash_algorithm = hash_algorithm.name
        logging.info("Root CA fingerprint: %s", root_ca_fingerprint)
        return root_ca_fingerprint, root_ca_fingerprint_hash_algorithm


    def get_data_signature(self, data : bytes) -> str:
        """
            Generate a signature from the private key using the given hash function

            :param data: The data to sign
            :return: The signature as a hex string
        """
        with open(self.private_key, encoding='utf-8') as private_key_file:
            signing_key = ecdsa.SigningKey.from_pem(private_key_file.read(), hashfunc=self.digital_signature_reference)
            signature = signing_key.sign(data, sigencode=sigencode_der)

        return signature.hex()


    def sign_envelope_object(self, envelope : SecomEnvelope) -> tuple[SecomEnvelope, str]:
        """
        Sign the envelope object using the private key
        :param envelope: The object to sign
        :return: A signed envelope object and the signature
        """
        # Populate the envelope
        envelope.envelope_root_certificate_thumbprint = self.root_ca_fingerprint
        logging.info("Root CA fingerprint: %s", self.root_ca_fingerprint)
        envelope.envelope_signature_certificate = []
        with open(self.public_key, "r") as f:
            envelope.envelope_signature_certificate.append(f.read().replace("\n", "")
                                                           .replace("-----BEGIN CERTIFICATE-----", "")
                                                           .replace("-----END CERTIFICATE-----", ""))

        envelope.envelope_signature_time = datetime.now()
        envelope.envelope_signature_reference = self.digital_signature_reference().name

        # Get the signature and the signature reference
        signature = self.get_data_signature(envelope.payload_to_bytes())
        logging.info("Signature: %s", signature)
        return envelope, signature

    def verify_ecdsa_384_sha3_data_signature(self, data : bytes,
                              certificates : list[bytes] | bytes,
                              signature : str) -> bool:
        """
            Verify the data with the public key
        """

        try:
            if isinstance(certificates, bytes):
                certificates = [certificates]

            for certificate in certificates:

                if "-----BEGIN CERTIFICATE-----"  not in certificate.decode(): # type: ignore
                    x509_cert = load_pem_x509_certificate(b"-----BEGIN CERTIFICATE-----" +
                                                        certificate + # type: ignore
                                                        b"-----END CERTIFICATE-----")
                else:
                    x509_cert = load_pem_x509_certificate(certificate) # type: ignore

                public_key = x509_cert.public_key()

                verify_key = ecdsa.VerifyingKey.from_pem(
                                            public_key.public_bytes(serialization.Encoding.PEM,
                                            serialization.PublicFormat.SubjectPublicKeyInfo)
                                            )

                logging.info("Signature in hex: %s", signature)

                if isinstance(data, str):
                    data = data.encode()

                valid = verify_key.verify(signature=bytes.fromhex(signature),
                                          data=data,
                                          hashfunc=sha3_384,
                                          sigdecode=sigdecode_der)

                if not valid:
                    logging.error("Data could not be validated")
                else:
                    logging.info("Data signature is valid")
                    return valid

        except BadSignatureError as e:
            logging.error("Exception: %s", str(e))
            raise SignatureValidationException from e

        return False


    def verify_ecdsa_384_sha2_data_signature(self, data : bytes,
                              certificates : list[bytes] | bytes,
                              signature : str) -> bool:
        """
            Verify the data with the public key using a SHA2 384 bit
            signature
        """
        try:
            if isinstance(certificates, bytes):
                certificates = [certificates]

            for certificate in certificates:

                if "-----BEGIN CERTIFICATE-----"  not in certificate.decode(): # type: ignore
                    x509_cert = load_pem_x509_certificate(b"-----BEGIN CERTIFICATE-----" +
                                                        certificate + # type: ignore
                                                        b"-----END CERTIFICATE-----")
                else:
                    x509_cert = load_pem_x509_certificate(certificate) # type: ignore

                public_key = x509_cert.public_key()

                verify_key = ecdsa.VerifyingKey.from_pem(
                                            public_key.public_bytes(serialization.Encoding.PEM,
                                            serialization.PublicFormat.SubjectPublicKeyInfo)
                                            )

                logging.info("Signature in hex: %s", signature)

                if isinstance(data, str):
                    data = data.encode()

                valid = verify_key.verify(signature=bytes.fromhex(signature),
                                          data=data,
                                          hashfunc=sha384,
                                          sigdecode=sigdecode_der)

                if not valid:
                    logging.error("Data could not be validated")
                else:
                    logging.info("Data signature is valid")
                    return valid

        except BadSignatureError as e:
            logging.error("Exception: %s", str(e))
            raise SignatureValidationException from e

        return False


    def get_validate_function(self, encryption_scheme : str) ->\
                    Callable[[bytes, list[bytes], str], bool]:
        """
            Factory method to return the default validation method 
            for the given encryption_scheme
        """
        match encryption_scheme:
            case "ecdsa-384-sha3":
                return self.verify_ecdsa_384_sha3_data_signature
            case "ecdsa-384-sha2":
                return self.verify_ecdsa_384_sha2_data_signature
            case _:
                return self.verify_ecdsa_384_sha3_data_signature


    def get_client_certificate(self) -> tuple[str, str]:
        """
            Returns the certificate as a tuple containing the 
            paths for the public and private key. Used for authentication
            using the requests library
        """
        return (self.public_key, self.private_key)


    def set_client_certificate(self, public_key : str, private_key : str,
                               private_key_password : str | None = None) -> None:
        """
            Sets the paths for the public and private keys
        """
        self.public_key = public_key
        self.private_key = private_key
        self.private_key_password = private_key_password

    def cleanup(self):
        """
        Remove the temporary folder
        :return: None
        """
        self.__tempfolder__.cleanup()