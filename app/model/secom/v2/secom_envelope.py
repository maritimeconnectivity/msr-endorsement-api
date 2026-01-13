"""
    Secom Envelope object
"""
from datetime import datetime


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
        dictionary = vars(self)
        return bytes(str(dictionary), encoding='utf-8')