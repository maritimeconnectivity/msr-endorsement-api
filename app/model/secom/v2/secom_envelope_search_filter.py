"""
    Implementation of the Secom Search Filter object
"""
from app.model.secom.v2.secom_envelope import SecomEnvelope
from app.model.secom.v2.secom_search_parameters import SecomSearchParameters
from app.model.secom.secom_constants import SecomConstants as sc

class SecomEnvelopeSearchFilter(SecomEnvelope):
    """
        Secom Search Filter class implementation
    """

    query : SecomSearchParameters | None
    geometry : str | None
    include_xml : bool | None
    local_only : bool = True

    def __init__(self) -> None:
        self.query = None
        self.geometry = None
        self.include_xml = None



    def to_secom_dict(self) -> dict[str, str | dict | int]:
        """
            Convert the object to Secom compatible dict
        """

        dictionary : dict[str, str | dict | int] = {}

        if self.query is not None:
            dictionary["query"] = self.query.to_secom_dict()
        else:
            dictionary["query"] = {}

        if self.geometry is not None:
            dictionary["geometry"] = self.geometry

        if self.include_xml is not None:
            dictionary["includeXml"] = self.include_xml

        dictionary["localOnly"] = self.local_only

        dictionary["envelopeSignatureCertificate"] = self.envelope_signature_certificate

        dictionary["envelopeRootCertificateThumbprint"] = self.envelope_root_certificate_thumbprint

        dictionary["envelopeSignatureTime"] =  self.envelope_signature_time.strftime(sc.DATETIME_FORMAT_v2)

        dictionary["envelopeSignatureReference"] = self.envelope_signature_reference

        return dictionary

    def payload_to_bytes(self) -> bytes:
        """
        Return the envelope as bytes
        :return: The contents of the envelope as bytes
        """
        dictionary = self.to_secom_dict()
        return bytes(str(dictionary).replace(" ",""), encoding='utf-8')