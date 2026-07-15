from src.models.schedule import Schedule
from src.services.workload_calculator import WorkloadCalculator
from src.models.assignment import Assignment
from src.services.candidate_scorer import CandidateScorer
from src.rules.hard.fixed_day_off_rule import FixedDayOffRule
from src.scheduler.hard_rule_engine import HardRuleEngine
from src.scheduler.soft_rule_engine import SoftRuleEngine
from src.rules.hard.day_off_rule import DayOffRule
from src.rules.hard.fixed_unit_rule import FixedUnitRule
from src.rules.hard.vacation_rule import VacationRule
from src.rules.hard.weekend_eligibility_rule import WeekendEligibilityRule
from src.rules.hard.holiday_eligibility_rule import HolidayEligibilityRule
from src.services.monthly_weekend_planner import    MonthlyWeekendPlanner
from src.services.weekly_rest_planner import WeeklyRestPlanner
from src.scheduler.candidate_provider import CandidateProvider
from src.services.coverage_repair_engine import CoverageRepairEngine
from src.scheduler.coverage_evaluator import CoverageEvaluator

from datetime import timedelta

from src.rules.soft.substitution_priority_rule import (
    SubstitutionPriorityRule,
)
from src.rules.soft.reinforcement_priority_rule import (
    ReinforcementPriorityRule,
)
from src.rules.soft.holiday_balance_rule import (
    HolidayBalanceRule,
)
from src.rules.soft.friday_balance_rule import (
    FridayBalanceRule,
)

from src.scheduler.schedule_validator import (
    ScheduleValidator,
)

import calendar
from datetime import date

class MonthlyScheduler:
    """Responsável por gerar o horário mensal."""

    def __init__(self):

        self.hard_engine = HardRuleEngine()

        self.soft_engine = SoftRuleEngine()

        self._load_rules()

        self.workload_calculator = WorkloadCalculator()

        self.candidate_scorer = CandidateScorer()

        self.monthly_weekend_planner = MonthlyWeekendPlanner()

        self.coverage_evaluator = CoverageEvaluator(
            self.hard_engine,
        )

        self.weekly_rest_planner = WeeklyRestPlanner(
            self.coverage_evaluator,
        )

        self.candidate_provider = CandidateProvider(
            self.hard_engine
        )

    def _load_rules(self):
        """Regista todas as regras."""

        # Hard Rules
        self.hard_engine.add_rule(FixedUnitRule())
        self.hard_engine.add_rule(VacationRule())
        self.hard_engine.add_rule(WeekendEligibilityRule())
        self.hard_engine.add_rule(HolidayEligibilityRule())

        # Soft Rules
        self.soft_engine.add_rule(
            SubstitutionPriorityRule()
        )

        self.soft_engine.add_rule(
            ReinforcementPriorityRule()
        )

        self.soft_engine.add_rule(
            HolidayBalanceRule()
        )

        self.soft_engine.add_rule(
            FridayBalanceRule()
        )

        self.hard_engine.add_rule(
            FixedDayOffRule()
        )

        self.hard_engine.add_rule(
            DayOffRule()
        )

    def _assign_day(
        self,
        schedule,
        hotel,
        unit,
        current_day,
    ) -> None:
        """
    Processa uma unidade num determinado dia.
    """

        workload = self._get_daily_workload(
            hotel,
            current_day,
            unit.nome,
        )

        minutes = self.workload_calculator.calculate_required_minutes(
            unit,
            workload,
        )

        unit_candidates = self.candidate_provider.unit_candidates(
            schedule,
            hotel,
            unit,
            current_day,
        )

        selected = []

        # --------------------------
        # 1. Equipa da unidade
        # --------------------------

        selected = self._select_candidates(
            schedule,
            hotel,
            unit_candidates,
            unit,
            current_day,
            minutes,
        )

        allocations = self._allocate_minutes(
            schedule,
            hotel,
            selected,
            current_day,
            minutes,
        )

        self._create_assignments(
            schedule,
            allocations,
            unit,
            current_day,
        )

        remaining_minutes = self._remaining_minutes(
            allocations,
            minutes,
        )

        # --------------------------
        # 2. Reforços
        # --------------------------

        if remaining_minutes > 0:

            reinforcement_candidates = (
                self.candidate_provider.reinforcement_candidates(
                    schedule,
                    hotel,
                    unit,
                    current_day,
                )
            )

            # Evita colaboradores já utilizados
            selected_ids = {
                assignment.employee_id
                for assignment in schedule.assignments
                if (
                    assignment.day == current_day
                    and assignment.unit == unit.nome
                )       
            }

            reinforcement_candidates = [
                employee
                for employee in reinforcement_candidates
                if employee.id not in selected_ids
            ]

            reinforcement_selected = self._select_candidates(
                schedule,
                hotel,
                reinforcement_candidates,
                unit,
                current_day,
                remaining_minutes,
            )

            allocations = self._allocate_minutes(
                schedule,
                hotel,
                reinforcement_selected,
                current_day,
                remaining_minutes,
            )

            self._create_assignments(
                schedule,
                allocations,
                unit,
                current_day,
            )

            remaining_minutes = self._remaining_minutes(
                allocations,
                remaining_minutes,
            )       

        # --------------------------
        # 3. Substituição obrigatória
        # --------------------------

        if remaining_minutes > 0:

            mandatory = self.candidate_provider.mandatory_substitute(
                schedule,
                hotel,
                unit,
                current_day,
            )

            selected_ids = {
                assignment.employee_id
                for assignment in schedule.assignments
                if (
                    assignment.day == current_day
                    and assignment.unit == unit.nome
                )
            }

            mandatory = [
                employee
                for employee in mandatory
                if employee.id not in selected_ids
            ]

            allocations = self._allocate_minutes(
                schedule,
                hotel,
                mandatory,
                current_day,
                remaining_minutes,
            )

            self._create_assignments(
                schedule,
                allocations,
                unit,
                current_day,
            )       

            remaining_minutes = self._remaining_minutes(
                allocations,
                remaining_minutes,
            )

        # --------------------------
        # 4. Rotações
        # --------------------------

        if remaining_minutes > 0:

            rotation_candidates = (
                self.candidate_provider.rotation_candidates(
                    schedule,
                    hotel,
                    unit,
                    current_day,
                )
            )

            selected_ids = {
                assignment.employee_id
                for assignment in schedule.assignments
                if (
                    assignment.day == current_day
                    and assignment.unit == unit.nome
                )
            }

            rotation_candidates = [
                employee
                for employee in rotation_candidates
                if employee.id not in selected_ids
            ]

            rotation_selected = self._select_candidates(
                schedule,
                hotel,
                rotation_candidates,
                unit,
                current_day,
                remaining_minutes,
            )

            allocations = self._allocate_minutes(
                schedule,
                hotel,
                rotation_selected,
                current_day,
                remaining_minutes,
            )

            self._create_assignments(
                schedule,
                allocations,
                unit,
                current_day,
            )

            remaining_minutes = self._remaining_minutes(
                allocations,
                remaining_minutes,
            )

        if remaining_minutes > 0:

            print(
                f"""
        ⚠️ Unidade: {unit.nome}
        Data: {current_day}

        Necessários: {minutes} min
        Disponíveis: {minutes - remaining_minutes} min
        Em falta: {remaining_minutes} min
        """
            )

    def _remaining_minutes(
        self,
        allocations,
        required_minutes,
    ) -> int:
        """
    Calcula quantos minutos ainda faltam
    atribuir à unidade.
    """

        assigned = sum(
            minutes
            for _, minutes in allocations
        )

        return max(
            0,
            required_minutes - assigned,
        )

    def generate(
        self,
        hotel,
        history,
        previous_schedule,
        start_date,
        end_date,
    ) -> Schedule:

        schedule = Schedule(
            start_date=start_date,
            end_date=end_date,
        )

        self.monthly_weekend_planner.plan(
            schedule,
            previous_schedule,
            hotel,
            start_date,
            end_date,
        )

        self.weekly_rest_planner.plan(
            schedule,
            previous_schedule,
            history,
            hotel,
            start_date,
            end_date,
        )  

        self._assign_period(
            schedule,
            hotel,
            start_date,
            end_date,
        )


        return schedule
    
    def _assign_period(
        self,
        schedule,
        hotel,
        start_date,
        end_date,
    ):
        
        """
    Gera os assignments para todo o
    período de planeamento.
    """

        current_day = start_date

        while current_day <= end_date:

            for unit in hotel.units.values():

                self._assign_day(
                    schedule,
                    hotel,
                    unit,
                    current_day,
                )

            current_day += timedelta(
                days=1,
            )
    
    def _get_daily_workload(
        self,
        hotel,
        current_day,
        unit_name: str,
    ):
        """
    Devolve a carga diária de uma unidade num determinado dia.
    """

        for workload in hotel.daily_workloads:

            if (
                workload.data == current_day
                and workload.unidade == unit_name
            ):
                return workload

        return None
    
    def _select_candidates(
        self,
        schedule,
        hotel,
        candidates,
        unit,
        day,
        required_minutes: int,
    ):
        """
        Seleciona colaboradores até atingir
        os minutos necessários.

        Dá prioridade aos colaboradores da unidade
        que não podem rodar, preservando os que
        podem rodar para possíveis reforços.
        """

        def score(employee):
            return (
                self.candidate_scorer.score(
                    employee,
                    unit,
                    day,
                    hotel,
                    schedule,
                )
                - schedule.count_working_days(
                    employee.id,
                )
            )

        # ----------------------------------
        # 1. Divide os candidatos
        # ----------------------------------

        fixed_candidates = [
            employee
            for employee in candidates
            if not employee.pode_rodar
        ]

        flexible_candidates = [
            employee
            for employee in candidates
            if employee.pode_rodar
        ]

        # ----------------------------------
        # 2. Ordena cada grupo
        # ----------------------------------

        fixed_candidates.sort(
            key=score,
            reverse=True,
        )

        flexible_candidates.sort(
            key=score,
            reverse=True,
        )

        # Primeiro usa quem não pode rodar
        candidates = (
            fixed_candidates
            + flexible_candidates
        )

        # ----------------------------------
        # 3. Seleciona colaboradores
        # ----------------------------------

        selected = []
        total_minutes = 0

        for employee in candidates:

            selected.append(employee)

            total_minutes += schedule.remaining_minutes(
                employee.id,
                day,
                hotel,
            )

            if (
                total_minutes >= required_minutes
                and len(selected) >= unit.minimo_colaboradores
            ):
                break

        return selected

    def _create_assignments(
        self,
        schedule,
        allocations,
        unit,
        current_day,
    ):
        """
    Cria as atribuições dos colaboradores.
    """

        for employee, minutes in allocations:

            assignment = Assignment(
                employee_id=employee.id,
                day=current_day,
                unit=unit.nome,
                minutes=minutes,
            )

            schedule.add_assignment(
                assignment,
            )

    def _has_enough_minutes(
        self,
        employees,
        required_minutes,
    ):
        """
    Verifica se os minutos atribuídos
    são suficientes.
    """

        total = sum(
            employee.horas_por_dia * 60
            for employee in employees
        )

        return total >= required_minutes
    
    def _allocate_minutes(
        self,
        schedule,
        hotel,
        employees,
        day,
        required_minutes,
    ):
        assignments = []

        remaining = required_minutes

        remaining_employees = len(employees)

        for employee in employees:

            available = schedule.remaining_minutes(
                employee.id,
                day,
                hotel,
            )

            if available <= 0:
                remaining_employees -= 1
                continue

            share = remaining // remaining_employees

            assigned = min(
                available,
                share,
            )

            assignments.append(
                (employee, assigned)
            )

            remaining -= assigned
            remaining_employees -= 1

        return assignments