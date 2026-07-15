from dataclasses import dataclass, field
from src.models.reinforcement import Reinforcement
from src.models.substitution import Substitution
from src.models.employee import Employee
from src.models.unit import Unit
from src.models.vacation import Vacation
from src.models.holiday import Holiday
from src.models.daily_workload import DailyWorkload
from src.models.fixed_day_off import FixedDayOff


@dataclass(slots=True)
class HotelData:
    """Contém todos os dados do hotel carregados do Excel."""

    employees: dict[int, Employee] = field(default_factory=dict)
    units: dict[str, Unit] = field(default_factory=dict)
    vacations: list[Vacation] = field(default_factory=list)
    holidays: list[Holiday] = field(default_factory=list)
    daily_workloads: list[DailyWorkload] = field(default_factory=list)
    reinforcements: list[Reinforcement] = field(default_factory=list)
    substitutions: list[Substitution] = field(default_factory=list)
    fixed_days_off: list[FixedDayOff] = field(default_factory=list)