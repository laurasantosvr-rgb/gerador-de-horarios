class CandidateScorer:

    UNIT_SCORE = 1000
    SUBSTITUTION_SCORE = 5000
    REINFORCEMENT_SCORE = 3000
    WORKLOAD_SCORE = 100
    WEEKEND_SCORE = 20
    """Calcula uma pontuação para cada colaborador."""

    def _workload_score(
            self,
            employee,
            schedule,
        ) -> int:
            """
    Dá prioridade a quem trabalhou menos dias.
    """

            worked_days = schedule.count_working_days(
                employee.id,
            )

            return max(
                0,
                100 - worked_days * 5,
            )
    
    def _reinforcement_score(
        self,
        employee,
        unit,
        hotel,
    ) -> int:
        """
    Dá prioridade aos reforços
    definidos para a unidade.
    """

        for reinforcement in hotel.reinforcements:

            if (
                reinforcement.unit == unit.nome
                and reinforcement.employee_id == employee.id
            ):
                return (
                    4000
                    - reinforcement.priority * 1000
                )

        return 0
    
    def _substitution_score(
        self,
        employee,
        unit,
        hotel,
        schedule,
        day,
    ) -> int:
        """
    Dá prioridade ao substituto preferencial
    quando o titular da unidade não está a trabalhar.
    """

        # Procurar os colaboradores da unidade
        for principal in hotel.employees.values():

            if principal.unidade_principal != unit.nome:
                continue

            # O titular está a trabalhar nesta unidade hoje?
            principal_working = any(
                assignment.employee_id == principal.id
                and assignment.day == day
                and assignment.unit == unit.nome
                for assignment in schedule.assignments
            )

            if principal_working:
                continue

            # Procurar substituto
            for substitution in hotel.substitutions:
        
                if substitution.employee_id != principal.id:
                    continue

                if substitution.substitute_id == employee.id:
                    return self.SUBSTITUTION_SCORE

        return 0
    
    def score(
        self,
        employee,
        unit,
        day,
        hotel,
        schedule,
    ) -> int:

        score = 0

        score += self._workload_score(
            employee,
            schedule,
        )

        score += self._reinforcement_score(
            employee,
            unit,
            hotel,
        )

        score += self._substitution_score(
            employee,
            unit,
            hotel,
            schedule,
            day,
        )

        return score