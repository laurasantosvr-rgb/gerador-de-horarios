class CandidateProvider:
    """
    Encontra os colaboradores que podem
    trabalhar numa unidade num determinado dia.
    """

    def __init__(self, hard_engine):
        self.hard_engine = hard_engine

    def unit_candidates(
        self,
        schedule,
        hotel,
        unit,
        current_day,
    ):
        """
    Encontra todos os colaboradores que podem
    trabalhar nesta unidade neste dia.
    """

        candidates = []

        for employee in hotel.employees.values():

            if not employee.ativo:
                continue

            if schedule.is_day_off(
                employee.id,
                current_day,
            ):
                continue

            if employee.unidade_principal != unit.nome:
                continue

            if (
                schedule.remaining_minutes(
                    employee.id,
                    current_day,
                    hotel,
                ) <= 0
            ):
                continue

            if self.hard_engine.can_assign(
                employee,
                unit,
                current_day,
                hotel,
                schedule,
            ):

                candidates.append(employee)

        return candidates

    def reinforcement_candidates(
        self,
        schedule,
        hotel,
        unit,
        current_day,
    ):
        """
    Devolve os reforços definidos
    para esta unidade.
    """

        candidates = []

        for reinforcement in hotel.reinforcements:


            if reinforcement.unit != unit.nome:
                continue

            employee = hotel.employees[
                reinforcement.employee_id
            ]

            if employee is None:
                continue

            if not employee.ativo:
                continue

            if schedule.is_day_off(
                employee.id,
                current_day,
            ):
                continue

            if (
                schedule.remaining_minutes(
                    employee.id,
                    current_day,
                    hotel,
                ) <= 0
            ):
                continue

            if self.hard_engine.can_assign(
                employee,
                unit,
                current_day,
                hotel,
                schedule,
            ):
                candidates.append(employee)

        return candidates

    def rotation_candidates(
        self,
        schedule,
        hotel,
        unit,
        current_day,
    ):
        """
    Devolve colaboradores que podem rodar
    para esta unidade.
    """

        candidates = []

        for employee in hotel.employees.values():

            if not employee.ativo:
                continue

            if schedule.is_day_off(
                employee.id,
                current_day,
            ):
                continue

            if (
                schedule.remaining_minutes(
                    employee.id,
                    current_day,
                    hotel,
                ) <= 0
            ):
                continue

            # Não pertence a esta unidade
            if employee.unidade_principal == unit.nome:
                continue

            # Não pode rodar
            if not employee.pode_rodar:
                continue

            if self.hard_engine.can_assign(
                employee,
                unit,
                current_day,
                hotel,
                schedule,
            ):
                candidates.append(employee)

        return candidates
    
    def mandatory_substitute(
        self,
        schedule,
        hotel,
        unit,
        current_day,
    ):
        """
    Devolve a substituta obrigatória da unidade,
    se estiver disponível.
    """

        # Só existe esta regra para a unidade B
        if unit.nome != "B":
            return []

        for substitution in hotel.substitutions:

            titular = hotel.employees[
                substitution.employee_id
            ]

            substituta = hotel.employees[
                substitution.substitute_id
            ]

            # O titular não pertence a esta unidade
            if titular.unidade_principal != unit.nome:
                continue

            # Se o titular já está a trabalhar,
            # não é preciso substituta
            if schedule.is_working(
                titular.id,
                current_day,
            ):
                return []
            
            if (
                schedule.remaining_minutes(
                    substituta.id,
                    current_day,
                    hotel,
                ) <= 0
            ):
                return []

            # A substituta já foi atribuída
            if (
                schedule.remaining_minutes(
                    substituta.id,
                    current_day,
                    hotel,
                ) <= 0
            ):
                continue

            # Pode trabalhar?
            if self.hard_engine.can_assign(
                substituta,
                unit,
                current_day,
                hotel,
                schedule,
            ):
                return [substituta]

            # Está de férias, folga, baixa, etc.
            return []

        return []