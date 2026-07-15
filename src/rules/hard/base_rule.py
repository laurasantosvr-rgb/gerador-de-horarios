from abc import ABC, abstractmethod


class BaseRule(ABC):

    name = ""
    description = ""

    @abstractmethod
    def is_valid(
        self,
        employee,
        unit,
        day,
        hotel,
        schedule,
    ) -> bool:
        pass