class ConstructorPreferred(Exception):
    """
    Throw this if it is preferred to use the constructor rather than any other
    auxillary methods to construct a data class.
    """

    def __str__(self):
        return "It is preferred to instantiate this with the constructor"

class InvalidDataClassState(Exception):
    """
    Throw this if a data class is found to be in an invalid state during
    runtime. Keep this for constraints that cannot be encoded as types.
    """

    def __init__(self, state_desc: str):
        self.state_desc = state_desc

    def __str__(self):
        return
