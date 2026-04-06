"""
Implementation of the Secom Retrieve Result envelope object
"""
from app.model.secom.v2.secom_envelope import SecomEnvelope
from app.model.secom.secom_constants import SecomConstants as sc


class SecomEnvelopeRetrieveResult(SecomEnvelope):
    """
    Secom Retrieve Result envelope implementation
    """

    transaction_id: str

    def __init__(self, transactionId) -> None:
        self.transaction_id = transactionId

    def to_secom_dict(self) -> dict[str, str | list[str]]:
        """
        Convert the object to SECOM-compatible dict
        """
        dictionary: dict[str, str | list[str]] = {}

        dictionary["transactionId"] = self.transaction_id

        dictionary["envelopeSignatureCertificate"] = self.envelope_signature_certificate
        dictionary["envelopeRootCertificateThumbprint"] = self.envelope_root_certificate_thumbprint
        dictionary["envelopeSignatureTime"] = self.envelope_signature_time.strftime(sc.DATETIME_FORMAT_v2)

        return dictionary

    def payload_to_bytes(self) -> bytes:
        """
        Return the envelope as bytes for signature generation
        """
        payload = ""
        payload += self.transaction_id
        payload += "."
        payload += super().payload_to_bytes().decode()

        return bytes(payload, encoding="utf-8")