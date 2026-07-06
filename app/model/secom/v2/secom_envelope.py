"""
    Secom Envelope object
"""
from datetime import datetime, timezone

class SecomEnvelope:

    envelope_signature_certificate : list[str] = [""]
    envelope_root_certificate_thumbprint : str = "asd"
    envelope_signature_time : datetime = datetime.now(timezone.utc).replace(microsecond=0)

    def payload_to_bytes(self) -> bytes:
        """
        Return the envelope as bytes
        :return: The contents of the envelope as bytes
        """
        cert_payload = "[" + ", ".join(self.envelope_signature_certificate) + "]"

        payload = ""
        payload += cert_payload + "."
        payload += self.envelope_root_certificate_thumbprint + "."
        payload += str(int(self.envelope_signature_time.astimezone(timezone.utc).timestamp()))

        return payload.encode("utf-8")