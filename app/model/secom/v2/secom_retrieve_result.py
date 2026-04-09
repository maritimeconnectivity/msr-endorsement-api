"""
    Implementation of the Retrieve Result Object
"""
from app.model.secom.v2.secom_envelope_retrieve_result import SecomEnvelopeRetrieveResult


class SecomRetrieveResult:
    """
        Class to hold the Envelope Retrieve Result
    """

    envelope : SecomEnvelopeRetrieveResult
    envelope_signature : str = ""

    def to_secom_dict(self) -> dict[str, str | dict | int]:
        """
            Convert the object to Secom compatible dict
        """
        dictionary: dict[str, str | dict ] = {
            "envelope" : self.envelope.to_secom_dict(),
            "envelopeSignature" : self.envelope_signature
        }

        return dictionary

