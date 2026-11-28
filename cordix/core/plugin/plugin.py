class Plugin:
    def __init__(self, name: str):

        self._name: str = name

    ################## GETTERS ###################

    @property
    def name(self) -> str:
        return self._name

    ################## SETTERS ###################

    ################ CLASSMETHODS ################
