from abc import ABC, abstractmethod

from simpleruleengine.rule.rule import Rule


class SimpleRuleEngineAdapter(ABC):
    def __init__(self):
        """instance members are defined in concrete implementations"""
        pass

    @abstractmethod
    def get_rule(self) -> Rule:
        pass
