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
        return self.state_desc

class MountpointUnderivable(Exception):
    """
    Throw this if we are asked to index a file path without a clear mountpoint.
    """

    def __init__(self, index_path: str):
        self.index_path = index_path

    def __str__(self):
        return f"Can't figure out mountpoint of {self.index_path}."

class MountpointMisMatch(Exception):

    def __init__(self, mismatched_path: str, mountpoint: str):
        self.mismatched_path = mismatched_path
        self.mountpoint = mountpoint

    def __str__(self):
        return f"Mountpoint mismatch: {self.mountpoint} - {self.mismatched_path}"
