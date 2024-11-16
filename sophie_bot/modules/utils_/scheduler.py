from abc import ABC


class SophieSchedulerABC(ABC):
    def __init__(self):
        pass

    async def handle(self):
        raise NotImplementedError("Subclasses must implement handle method")
