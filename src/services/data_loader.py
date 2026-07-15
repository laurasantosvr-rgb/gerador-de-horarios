from src.models.hotel_data import HotelData
from src.services.loaders.fixed_day_off_loader import FixedDayOffLoader
from src.services.loaders.employee_loader import EmployeeLoader
from src.services.loaders.unit_loader import UnitLoader
from src.services.loaders.vacation_loader import VacationLoader
from src.services.loaders.holiday_loader import HolidayLoader
from src.services.loaders.workload_loader import WorkloadLoader
from src.services.loaders.reinforcement_loader import ReinforcementLoader
from src.services.loaders.substitution_loader import SubstitutionLoader


class DataLoader:
    """Converte os DataFrames lidos do Excel em objetos do sistema."""

    def __init__(self, data):
        self.data = data

    def load(self):

        hotel = HotelData()

        hotel.employees = EmployeeLoader(
            self.data["Funcionarios"]
        ).load()

        hotel.units = UnitLoader(
            self.data["Unidades"]
        ).load()

        hotel.vacations = VacationLoader(
            self.data["Ferias"]
        ).load()

        hotel.holidays = HolidayLoader(
            self.data["Feriados"]
        ).load()

        hotel.daily_workloads = WorkloadLoader(
            self.data["CargaDiaria"]
        ).load()

        hotel.reinforcements = ReinforcementLoader(
            self.data["Reforcos"]
        ).load()

        hotel.substitutions = SubstitutionLoader(
            self.data["Substituicoes"]
        ).load()

        hotel.fixed_days_off = FixedDayOffLoader(
            self.data["FolgasFixas"]
        ).load()

        return hotel