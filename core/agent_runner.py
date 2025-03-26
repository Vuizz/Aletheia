from abc import ABC, abstractmethod

class AgentRunner(ABC):
    def __init__(self, prompt):
        self.prompt = prompt

    @abstractmethod
    def run(self, belief_state: dict, input_data: str = None) -> dict:
        pass