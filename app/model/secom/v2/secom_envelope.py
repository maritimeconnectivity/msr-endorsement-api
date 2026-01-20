"""
    Secom Envelope object
"""
from datetime import datetime
from app.model.secom.secom_constants import SecomConstants as sc

class SecomEnvelope:

    envelope_signature_certificate : list[str] = [""]
    envelope_root_certificate_thumbprint : str = "asd"
    envelope_signature_time : datetime = datetime.now()
    envelope_signature_reference : str = "asdf"

    def payload_to_bytes(self) -> bytes:
        """
        Return the envelope as bytes
        :return: The contents of the envelope as bytes
        """
        payload = ""

        payload += "["
        for certificate in self.envelope_signature_certificate:
            payload += certificate + "."
        payload = payload[:-1] + "]."

        payload += self.envelope_root_certificate_thumbprint + "."
        payload += str(int(self.envelope_signature_time.timestamp())) + "."
        payload += self.envelope_signature_reference.lower()

        return bytes(payload, encoding='utf-8')