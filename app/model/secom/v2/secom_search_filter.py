"""
    Implementation of the Search Filter Object
"""
from app.model.secom.v2.secom_envelope_search_filter import SecomEnvelopeSearchFilter


class SecomSearchFilter:
    """
        Class to hold the Envelope Search Filter
    """

    envelope : SecomEnvelopeSearchFilter
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

