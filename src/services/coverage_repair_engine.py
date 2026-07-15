from datetime import timedelta
from src.enums.rest_pattern import RestPattern
from src.scheduler.coverage_evaluator import CoverageEvaluator

class CoverageRepairEngine:
    """
    Corrige unidades abaixo do mínimo
    movendo apenas as folgas necessárias.
    """

    def __init__(
        self,
        weekly_rest_planner,
        hard_engine,
    ):
        
        self.weekly_rest_planner = weekly_rest_planner

        self.coverage_evaluator = CoverageEvaluator(
            hard_engine,
        )

    def repair(
        self,
        schedule,
        hotel,
        scheduler,
        start_date,
        end_date,
    ):

        problems = self._understaffed_units(
            schedule,
            hotel,
        )

        for problem in problems:

            employee = self._find_employee_to_move(
                schedule,
                hotel,
                problem,
            )

            if employee is None:
                continue

            pattern, current_rest = self._find_current_rest(
                schedule,
                employee,
                problem["day"],
            )

            if pattern is None:
                continue

            week = self._week_days(
                problem["day"],
            )

            if pattern == RestPattern.CONSECUTIVE_PAIR:

                alternatives = self._alternative_rest_pairs(
                    current_rest,
                    week,
                )

            elif pattern == RestPattern.SINGLE_DAY:

                alternatives = self._alternative_single_days(
                    current_rest,
                    week,
                )

            for alternative in alternatives:

                if pattern == RestPattern.CONSECUTIVE_PAIR:

                    moved = self._try_move_rest_pair(
                        schedule,
                        hotel,
                        scheduler,
                        employee,
                        current_rest,
                        alternative,
                        start_date,
                        end_date,
                    )

                elif pattern == RestPattern.SINGLE_DAY:

                    moved = self._try_move_single_day(
                        schedule,
                        hotel,
                        scheduler,
                        employee,
                        current_rest,
                        alternative,
                        start_date,
                        end_date,
                    )

                if moved:
                    break
    
    def _understaffed_units(
        self,
        schedule,
        hotel,
    ):
        """
    Devolve todas as unidades que ficaram
    abaixo do mínimo de colaboradores.
    """

        problems = []

        for workload in hotel.daily_workloads:

            unit = hotel.units[
                workload.unidade
            ]

            assigned = len(
                schedule.get_unit_assignments(
                    unit.nome,
                    workload.data,
                )
            )

            if assigned < unit.minimo_colaboradores:

                problems.append(
                    {
                        "day": workload.data,
                        "unit": unit,
                        "assigned": assigned,
                        "minimum": unit.minimo_colaboradores,
                    }
                )

        return problems
    
    def _employees_day_off(
        self,
        schedule,
        hotel,
        unit,
        day,
    ):

        employees = []

        for employee in hotel.employees.values():

            if employee.unidade_principal != unit.nome:
                continue

            if not schedule.is_day_off(
                employee.id,
                day,
            ):
                continue

            employees.append(employee)

        return employees
    
    def _find_employee_to_move(
        self,
        schedule,
        hotel,
        problem,
    ):
        """
    Escolhe um colaborador de folga
    para tentar mover.
    """

        employees = self._employees_day_off(
            schedule,
            hotel,
            problem["unit"],
            problem["day"],
        )

        if not employees:
            return None

        return employees[0]

    def _find_current_rest(
        self,
        schedule,
        employee,
        day,
    ):
        """
    Devolve o descanso atual do colaborador
    na semana do dia indicado.

    Pode ser:
    - um par de folgas consecutivas;
    - um dia de folga isolado.
    """

        week = day.isocalendar().week

        employee_days_off = sorted(
            [
                day_off.day
                for day_off in schedule.day_offs
                if day_off.employee_id == employee.id
                and day_off.day.isocalendar().week == week
            ]
        )

        # -----------------------------
        # Procura um par consecutivo
        # -----------------------------

        for current_day in employee_days_off:

            next_day = current_day + timedelta(days=1)

            if next_day in employee_days_off:

                return (
                    RestPattern.CONSECUTIVE_PAIR,
                    (
                        current_day,
                        next_day,
                    ),
                )

        # -----------------------------
        # Procura um dia isolado
        # -----------------------------

        if len(employee_days_off) == 1:

            return (
                RestPattern.SINGLE_DAY,
                employee_days_off[0],
            )

        return (
            None,
            None,
        )
    
    def _alternative_rest_pairs(
        self,
        current_pair,
        week,
    ):

        alternatives = []

        for i in range(len(week) - 1):

            pair = (
                week[i],
                week[i + 1],
            )

            if pair == current_pair:
                continue

            alternatives.append(pair)

        return alternatives
    
    def _alternative_single_days(
        self,
        current_day,
        week,
    ):
        """
    Devolve todos os dias alternativos
    para mover uma folga isolada.
    """

        alternatives = []

        for day in week:

            if day == current_day:
                continue

            alternatives.append(day)

        return alternatives
    
    def _try_move_rest_pair(
        self,
        schedule,
        hotel,
        scheduler,
        employee,
        current_pair,
        new_pair,
        start_date,
        end_date,
    ):
        """
    Experimenta mover um par de folgas.
    Mantém a alteração apenas se melhorar
    a cobertura.
    """

        previous_day_offs = list(
            schedule.day_offs
        )

        previous_assignments = list(
            schedule.assignments
        )

        previous_problems = len(
            self._understaffed_units(
                schedule,
                hotel,
            )
        )

        # Move as folgas
        self._move_rest_pair(
            schedule,
            employee,
            current_pair,
            new_pair,
        )

        if not self._valid_rest_configuration(
            schedule,
            hotel,
            employee,
            new_pair,
        ):
            # desfazer
            self._move_rest_pair(
                schedule,
                employee,
                new_pair,
                current_pair,
            )
            return False

        # Volta a gerar o horário
        schedule.assignments.clear()

        scheduler._assign_period(
            schedule,
            hotel,
            start_date,
            end_date,
        )

        current_problems = len(
            self._understaffed_units(
                schedule,
                hotel,
            )
        )

        if current_problems < previous_problems:

            print(
                "✔ Melhorou:",
                employee.nome,
                current_pair,
                "->",
                new_pair,
            )

            return True

        # Repor estado anterior
        schedule.day_offs = previous_day_offs
        schedule.assignments = previous_assignments

        return False
    
    def _try_move_single_day(
        self,
        schedule,
        hotel,
        scheduler,
        employee,
        current_day,
        new_day,
        start_date,
        end_date,
    ):
        """
    Experimenta mover uma folga isolada.
    Mantém a alteração apenas se melhorar
    a cobertura.
    """

        previous_day_offs = list(
            schedule.day_offs
        )

        previous_assignments = list(
            schedule.assignments
        )

        previous_problems = len(
            self._understaffed_units(
                schedule,
                hotel,
            )
        )

        # Move a folga
        self._move_single_day(
            schedule,
            employee,
            current_day,
            new_day,
        )

        if not self._valid_rest_configuration(
            schedule,
            hotel,
            employee,
            (new_day,),
        ):
            self._move_single_day(
                schedule,
                employee,
                new_day,
                current_day,
            )
            return False

        # Volta a gerar o horário
        schedule.assignments.clear()

        scheduler._assign_period(
            schedule,
            hotel,
            start_date,
            end_date,
        )

        current_problems = len(
            self._understaffed_units(
                schedule,
                hotel,
            )
        )

        if current_problems < previous_problems:

            print(
                "✔ Melhorou:",
                employee.nome,
                current_day,
                "->",
                new_day,
            )

            return True

        # Repor estado anterior
        schedule.day_offs = previous_day_offs
        schedule.assignments = previous_assignments

        return False
    
    def _move_rest_pair(
        self,
        schedule,
        employee,
        current_pair,
        new_pair,
    ):
        """
    Move um par de folgas consecutivas.
    """

        first_day, second_day = current_pair

        new_first, new_second = new_pair

        # Remove o par atual
        schedule.day_offs = [
            day_off
            for day_off in schedule.day_offs
            if not (
                day_off.employee_id == employee.id
                and day_off.day in (
                    first_day,
                    second_day,
                    )
                )       
            ]

        # Adiciona o novo par
        schedule.add_day_off(
            employee.id,
            new_first,
        )

        schedule.add_day_off(
            employee.id,
            new_second,
        )

    def _move_single_day(
        self,
        schedule,
        employee,
        current_day,
        new_day,
    ):
        """
    Move uma folga isolada
    para outro dia.
    """

        self._remove_single_day(
            schedule,
            employee,
            current_day,
        )

        self._assign_single_day(
            schedule,
            employee,
            new_day,
        )

    def _week_days(
        self,
        day,
    ):
        """
    Devolve todos os dias da semana
    a que pertence 'day'.
    """

        monday = day - timedelta(days=day.weekday())

        return [
            monday + timedelta(days=i)
            for i in range(7)
        ]
    
    def _remove_single_day(
        self,
        schedule,
        employee,
        day,
    ):
        """
    Remove uma folga isolada
    do colaborador.
    """

        schedule.day_offs = [
            day_off
            for day_off in schedule.day_offs
            if not (
                day_off.employee_id == employee.id
                and day_off.day == day
            )
        ]

    def _assign_single_day(
        self,
        schedule,
        employee,
        day,
    ):
        """
    Atribui uma folga isolada
    ao colaborador.
    """

        schedule.add_day_off(
            employee.id,
            day,
        )

    def _valid_rest_configuration(
        self,
        schedule,
        hotel,
        employee,
        new_days,
    ) -> bool:

        return (
            not self._has_substitution_conflict(
                schedule,
                hotel,
                employee,
            )
            and not self._exceeds_five_consecutive_days(
                schedule,
                employee,
                new_days,
            )
            and self._maintains_minimum_staff(
                schedule,
                hotel,
                employee,
                new_days,
            )
        )
    
    def _has_substitution_conflict(
        self,
        schedule,
        hotel,
        employee,
    ) -> bool:

        partner = None

        for substitution in hotel.substitutions:

            if substitution.employee_id == employee.id:
                partner = hotel.employees[substitution.substitute_id]
                break

            if substitution.substitute_id == employee.id:
                partner = hotel.employees[substitution.employee_id]
                break

        if partner is None:
            return False

        employee_days = {
            day_off.day
            for day_off in schedule.day_offs
            if day_off.employee_id == employee.id
        }

        partner_days = {
            day_off.day
            for day_off in schedule.day_offs
            if day_off.employee_id == partner.id
        }

        return bool(employee_days & partner_days)
    
    def _exceeds_five_consecutive_days(
        self,
        schedule,
        employee,
        candidate_days,
    ) -> bool:
        
        print(
    employee.nome,
    "->",
    candidate_days,
    "consecutivos:",
    consecutive_days,
)

        return (
            self.weekly_rest_planner._consecutive_work_days(
                schedule,
                employee,
                candidate_days,
            )
            > 5
        )
    
    def _maintains_minimum_staff(
        self,
        schedule,
        hotel,
        employee,
        candidate_days,
    ) -> bool:

        for day in candidate_days:

            if not self.coverage_evaluator.can_cover(
                schedule,
                hotel,
                employee,
                day,
                simulated_employee=employee,
            ):
                return False

        return True
    
    def _substitution_partner(
        self,
        employee,
        hotel,
    ):

        for substitution in hotel.substitutions:

            if substitution.employee_id == employee.id:
                return hotel.employees[
                    substitution.substitute_id
                ]

            if substitution.substitute_id == employee.id:
                return hotel.employees[
                    substitution.employee_id
                ]

        return None