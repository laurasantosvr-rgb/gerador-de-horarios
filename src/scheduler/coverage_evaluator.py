from src.scheduler.candidate_provider import CandidateProvider
from src.services.workload_calculator import WorkloadCalculator


class CoverageEvaluator:

    def __init__(
        self,
        hard_engine,
    ):

        self.workload_calculator = WorkloadCalculator()

        self.candidate_provider = CandidateProvider(
            hard_engine,
        )

    def can_cover(
        self,
        schedule,
        hotel,
        employee,
        day,
        simulated_employee=None,
    ):
        """
        Verifica se a unidade consegue ser
        coberta nesse dia.
        """

        unit = hotel.units[
            employee.unidade_principal
        ]

        required = self._required_minutes(
            hotel,
            unit,
            day,
        )

        assigned, people = self._simulate_assignment(
            schedule,
            hotel,
            unit,
            day,
            simulated_employee,
        )

        return (
            assigned >= required
            and people >= unit.minimo_colaboradores
        )
    
    def _required_minutes(
        self,
        hotel,
        unit,
        day,
    ):
        """
    Calcula os minutos necessários
    para esta unidade neste dia.
    """

        workload = None

        for daily_workload in hotel.daily_workloads:

            if (
                daily_workload.data == day
                and daily_workload.unidade == unit.nome
            ):
                workload = daily_workload
                break

        if workload is None:
            return 0

        return self.workload_calculator.calculate_required_minutes(
            unit,
            workload,
        )

    def _available_candidates(
        self,
        schedule,
        hotel,
        unit,
        day,
        simulated_employee=None,
    ):
        """
    Devolve todos os colaboradores que podem
    trabalhar nesta unidade.
    """

        employees = {}

        for employee in self.candidate_provider.unit_candidates(
            schedule,
            hotel,
            unit,
            day,
        ):
            
            if (
                simulated_employee is not None
                and employee.id == simulated_employee.id
            ):
                continue

            employees[employee.id] = employee

        for employee in self.candidate_provider.reinforcement_candidates(
            schedule,
            hotel,
            unit,
            day,
        ):
            
            if (
                simulated_employee is not None
                and employee.id == simulated_employee.id
            ):
                continue

            employees[employee.id] = employee

        for employee in self.candidate_provider.rotation_candidates(
            schedule,
            hotel,
            unit,
            day,
        ):
            
            if (
                simulated_employee is not None
                and employee.id == simulated_employee.id
            ):
                continue

            employees[employee.id] = employee

        return list(employees.values())
    
    def _simulate_assignment(
        self,
        schedule,
        hotel,
        unit,
        day,
        simulated_employee=None,
    ):
        
        required = self._required_minutes(
            hotel,
            unit,
            day,
        )

        remaining = required

        simulated_remaining = {
            employee.id: schedule.remaining_minutes(
                employee.id,
                day,
                hotel,
            )
            for employee in hotel.employees.values()
        }

        used_people = set()

        candidates = self.candidate_provider.unit_candidates(
            schedule,
            hotel,
            unit,
            day,
        )

        candidates = self._remove_simulated_employee(
            candidates,
            simulated_employee,
        )

        assigned, people = self._assignable_minutes(
            candidates,
            simulated_remaining,
            remaining,
        )

        remaining -= assigned

        used_people.update(people)

        if remaining <= 0:
            return (
                required,
                len(used_people),
            )

        candidates = self.candidate_provider.reinforcement_candidates(
            schedule,
            hotel,
            unit,
            day)
        
        candidates = self._remove_simulated_employee(
            candidates,
            simulated_employee,
        )

        assigned, people = self._assignable_minutes(
            candidates,
            simulated_remaining,
            remaining,
        )
        
        remaining -= assigned

        used_people.update(people)

        if remaining <= 0:
            return (
                required,
                len(used_people),
            )

        candidates = self.candidate_provider.mandatory_substitute(
            schedule,
            hotel,
            unit,
            day)
        
        candidates = self._remove_simulated_employee(
            candidates,
            simulated_employee,
        )
        
        assigned, people = self._assignable_minutes(
            candidates,
            simulated_remaining,
            remaining,
        )
        
        remaining -= assigned

        used_people.update(people)

        if remaining <= 0:
            return (
                required,
                len(used_people),
            )       

        candidates = self.candidate_provider.rotation_candidates(
            schedule,
            hotel,
            unit,
            day)
        
        candidates = self._remove_simulated_employee(
            candidates,
            simulated_employee,
        )
        
        assigned, people = self._assignable_minutes(
            candidates,
            simulated_remaining,
            remaining)
        
        remaining -= assigned

        used_people.update(people)

        if remaining <= 0:
            return (
                required,
                len(used_people),
            )

        assigned_minutes = required - remaining

        return (
            assigned_minutes,
            len(used_people),
        )
    
    def _assignable_minutes(
        self,
        employees,
        simulated_remaining,
        remaining,
    ):
        
        assigned = 0

        used = set()

        for employee in employees:

            if remaining <= 0:
                break

            available = simulated_remaining[
                employee.id
            ]

            if available <= 0:
                continue

            minutes = min(
                available,
                remaining,
            )

            assigned += minutes

            remaining -= minutes

            simulated_remaining[
                employee.id
            ] -= minutes

            used.add(employee.id)

        return assigned, used
    
    def _remove_simulated_employee(
        self,
        employees,
        simulated_employee,
    ):
        if simulated_employee is None:
            return employees

        return [
            employee
            for employee in employees
            if employee.id != simulated_employee.id
        ]