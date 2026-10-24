"""R02: the spy is a script. It sends one frozen text to both firms at spy_start."""


class ScriptedSpy:
    def __init__(self, message, spy_start, firm_ids=("0", "1")):
        raise NotImplementedError

    def messages_for_round(self, round_number):
        raise NotImplementedError
