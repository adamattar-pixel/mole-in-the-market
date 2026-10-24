"""R02: the spy is a script. It sends one frozen text to both firms at spy_start."""


class ScriptedSpy:
    def __init__(self, message, spy_start, firm_ids=("0", "1")):
        if int(spy_start) < 1:
            raise ValueError("spy_start is a round number, rounds start at 1")
        self.message = message
        self.spy_start = int(spy_start)
        self.firm_ids = tuple(firm_ids)

    def messages_for_round(self, round_number):
        """Same text object for every firm in round spy_start, nothing otherwise."""
        text = self.message if round_number == self.spy_start else None
        return {f: text for f in self.firm_ids}
