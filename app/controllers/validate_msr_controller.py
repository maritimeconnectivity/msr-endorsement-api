"""
    Controller to co-ordinate the MSR tests
"""

class ValidateMsrController:
    """
        Co-ordinate the MSR testing
    """

    test_url : str

    def __init__(self, test_url : str):
        self.test_url = test_url

