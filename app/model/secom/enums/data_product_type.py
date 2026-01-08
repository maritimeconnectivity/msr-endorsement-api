"""
    List of accepted data types for Secom
"""
from enum import Enum

class DataProductType(Enum):
    """
        Current list of supported data types
    """
    S101 = 101
    S102 = 102
    S103 = 103
    S104 = 104
    S111 = 111
    S112 = 112
    S121 = 121
    S122 = 122
    S123 = 123
    S124 = 124
    S125 = 125
    S126 = 126
    S127 = 127
    S128 = 128
    S129 = 129
    S130 = 130
    S131 = 131
    S164 = 164
    S201 = 201
    S210 = 210
    S211 = 211
    S212 = 212
    S230 = 230
    S240 = 240
    S245 = 245
    S246 = 246
    S247 = 247
    S401 = 401
    S402 = 402
    S411 = 411
    S412 = 412
    S413 = 413
    S414 = 414
    S421 = 421
    RTZ = 501
    EPC = 502
    ASM = 503
    OTHER = 999
