"""
    Helpers for building the SECOM envelope signature payload (IEC 63173-2, 7.3.4, Table 82)
"""
import base64


def encode_array(values: list[str] | None, already_base64: bool = False) -> str:
    """
    Convert an array to its signature payload representation: each element is
    Base64-encoded (unless it already is) and the elements are joined by a comma.
    :param values: The array values (None is treated as an empty value)
    :param already_base64: Whether the elements are already Base64-encoded
    :return: The payload string for the array
    """
    if not values:
        return ""

    if already_base64:
        return ",".join(values)

    return ",".join(base64.b64encode(value.encode("utf-8")).decode("ascii") for value in values)
