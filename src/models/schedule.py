from dataclasses import dataclass, field
from datetime import date, timedelta
import calendar
from src.models.day_off import DayOff

from src.models.assignment import Assignment

@dataclass(slots=True)
class Schedule:
    """Representa o horário completo de um mês."""

    start_date:date
    end_date:date

    assignments: list[Assignment] = field(default_factory=list)
    day_offs: list[DayOff] = field(default_factory=list)

    weekend_plan: dict[
        tuple[int, int],
        dict[int, tuple[date, date]]
    ] = field(default_factory=dict)

    # ==========================================================
    # Gestão das atribuições
    # ==========================================================

    def add_assignment(self, assignment: Assignment) -> None:
        """Adiciona uma atribuição ao horário."""
        self.assignments.append(assignment)

    # ==========================================================
    # Consultas
    # ==========================================================

    def get_employee_assignments(
        self,
        employee_id: int,
    ) -> list[Assignment]:
        """Devolve todas as atribuições de um colaborador."""

        return [
            assignment
            for assignment in self.assignments
            if assignment.employee_id == employee_id
        ]

    def get_day_assignments(
        self,
        day: date,
    ) -> list[Assignment]:
        """Devolve todas as atribuições de um determinado dia."""

        return [
            assignment
            for assignment in self.assignments
            if assignment.day == day
        ]

    def get_unit_assignments(
        self,
        unit: str,
        day: date,
    ) -> list[Assignment]:
        """Devolve todas as atribuições de uma unidade num dia."""

        return [
            assignment
            for assignment in self.assignments
            if assignment.unit == unit
            and assignment.day == day
        ]

    def is_working(
        self,
        employee_id: int,
        day: date,
    ) -> bool:
        """Indica se o colaborador trabalha nesse dia."""

        return any(
            assignment.employee_id == employee_id
            and assignment.day == day
            for assignment in self.assignments
        )

    # ==========================================================
    # Estatísticas do horário
    # ==========================================================
    

    def count_fridays_off(
        self,
        employee_id: int,
    ) -> int:
        """
        Devolve quantas sextas-feiras o colaborador teve de folga.
        """
        return 0
    
    def count_holidays_worked(
        self,
        employee_id: int,
        hotel,
    ) -> int:
        """
        Conta quantos feriados o colaborador trabalhou.
        """

        worked = 0

        for holiday in hotel.holidays:

            if self.is_working(
                employee_id,
                holiday.data,
            ):
                worked += 1

        return worked
    
    def count_friday_offs(
        self,
        hotel,
        year: int,
        month: int,
    ) -> int:
        """
    Conta o número total de folgas às sextas-feiras
    durante o mês.
    """

        offs = 0

        # Número de dias do mês
        _, last_day = calendar.monthrange(year, month)

        for day in range(1, last_day + 1):

            current_day = date(year, month, day)

            # Apenas interessa se for sexta-feira
            if current_day.weekday() != 4:
                continue

            # Percorre todos os colaboradores
            for employee in hotel.employees.values():

                # Se não trabalha, está de folga
                if not self.is_working(
                    employee.id,
                    current_day,
                ):
                    offs += 1

        return offs
    
    def count_changes(
        self,
        previous_schedule,
    ) -> int:
        """
    Conta quantas atribuições foram alteradas.
    """

        current = {
            (
                assignment.employee_id,
                assignment.day,
                assignment.unit,
            )
            for assignment in self.assignments
        }

        previous = {
            (
                assignment.employee_id,
                assignment.day,
                assignment.unit,
            )
            for assignment in previous_schedule.assignments
        }

        return len(current.symmetric_difference(previous))
    
    def count_working_days(
        self,
        employee_id: int,
    ) -> int:
        """
    Conta quantos dias o colaborador
    já foi escalado.
    """

        return sum(
            1
            for assignment in self.assignments
            if assignment.employee_id == employee_id
        )
    
    def is_day_off(
        self,
        employee_id: int,
        day,
    ) -> bool:

        return any(
            d.employee_id == employee_id
            and d.day == day
            for d in self.day_offs
        )

    def validate_day_offs(self):
        """
    Verifica se existem folgas duplicadas.
    """

        seen = set()

        for day_off in self.day_offs:

            key = (
                day_off.employee_id,
                day_off.day,
            )

            if key in seen:
                raise ValueError(
                    f"Folga duplicada: colaborador "
                    f"{day_off.employee_id} em {day_off.day}"
                )

            seen.add(key)

    def remaining_minutes(
        self,
        employee_id: int,
        day,
        hotel,
    ) -> int:
        """
    Devolve quantos minutos o colaborador
    ainda tem disponíveis nesse dia.
    """

        employee = hotel.employees[
            employee_id
        ]

        total_minutes = (
            employee.horas_por_dia * 60
        )

        assigned_minutes = sum(
            assignment.minutes
            for assignment in self.assignments
            if (
                assignment.employee_id == employee_id
                and assignment.day == day
            )
        )

        return total_minutes - assigned_minutes
    
    def add_day_off(
        self,
        employee_id: int,
        day,
    ):

        if self.is_day_off(
            employee_id,
            day,
        ):
            return

        self.day_offs.append(
            DayOff(
                employee_id=employee_id,
                day=day,
            )
        )

    def add_weekend(
        self,
        employee_id: int,
        saturday: date,
        sunday: date,
    ) -> None:
        """
    Regista o fim de semana mensal
    atribuído a um colaborador.
    """

        key = (
            saturday.year,
            saturday.month,
        )

        self.weekend_plan.setdefault(
            key,
            {},
        )

        self.weekend_plan[key][employee_id] = (
            saturday,
            sunday,
        )

        if self.start_date <= saturday <= self.end_date:
            self.add_day_off(
                employee_id,
                saturday,
            )

        if self.start_date <= sunday <= self.end_date:
            self.add_day_off(
                employee_id,
                sunday,
            )

    def has_weekend_in_month(
        self,
        employee_id: int,
        year: int,
        month: int,
    ) -> bool:
        """
    Indica se o colaborador já tem
    um fim de semana atribuído
    nesse mês.
    """

        return (
            employee_id
            in self.weekend_plan.get(
                (
                    year,
                    month,
            )   ,
                {},
            )
        )
    
    def get_weekend(
        self,
        employee_id: int,
        year: int,
        month: int,
    ) -> tuple[date, date] | None:
        """
    Devolve o fim de semana atribuído
    ao colaborador nesse mês.
    """

        return self.weekend_plan.get(
            (
                year,
                month,
            ),
            {},
        ).get(
            employee_id,
        )
    
    def count_holidays_off(
        self,
        employee_id,
        hotel,
    ):
        """
    Conta quantos feriados o colaborador
    teve de folga.
    """

        offs = 0

        for holiday in hotel.holidays:

            if self.is_day_off(
                employee_id,
                holiday.data,
            ):
                offs += 1

        return offs