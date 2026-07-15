from abc import ABC, abstractmethod


class BaseValidationRule(ABC):

    @abstractmethod
    def validate(
        self,
        schedule,
        hotel,
        year: int,
        month: int,
    ) -> bool:
        pass