from abc import ABC, abstractmethod

from src.models.hotel_data import HotelData
from src.models.schedule import Schedule


class BaseRule(ABC):

    name = ""
    description = ""
    weight = 1

    @abstractmethod
    def penalty(
        self,
        schedule: Schedule,
        hotel: HotelData,
        year: int,
        month: int,
    ) -> int:
        pass