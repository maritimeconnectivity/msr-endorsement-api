"""
    Secom Envelope object
"""
from datetime import datetime


class SecomEnvelope:

    envelope_signature_certificate : list[str] = [""]
    envelope_root_certificate_thumbprint : str = "asd"
    envelope_signature_time : datetime = datetime.now()
    envelope_signature_reference : str = "asdf"

