"""
    Implementation of the Secom Search Results
"""
from app.model.secom.v2.secom_envelope_search_result import SecomEnvelopeSearchResult


class SecomSearchResult:
    """
        Secom Search Result class
    """

    envelope: SecomEnvelopeSearchResult
    envelope_signature: str

    def __init__(self, results : dict) -> None:

        self.envelope = SecomEnvelopeSearchResult(results["envelope"])

        self.envelope_signature = results["envelopeSignature"]