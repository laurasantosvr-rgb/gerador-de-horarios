class WeekendScorer:

    UNIT_DISTRIBUTION_WEIGHT = 1000
    ROTATION_DISTRIBUTION_WEIGHT = 500

    def score(
        self,
        schedule,
        previous_schedule,
        hotel,
        employee,
        weekend,
        planner,
    ) -> int:
        """
        Calcula a pontuação de um
        fim de semana válido.
        """

        score = 0

        score += self._unit_distribution_score(
            employee,
            weekend,
            planner,
        )

        score += self._rotation_distribution_score(
            employee,
            hotel,
            weekend,
            planner,
        )

        return score
    
    def _unit_distribution_score(
        self,
        employee,
        weekend,
        planner,
    ) -> int:
        """
    Penaliza fins de semana já
    atribuídos a colaboradores
    fixos da mesma unidade.
    """

        if planner._can_rotate(
            employee,
            planner.hotel,
        ):
            return 0

        saturday, _ = weekend

        key = (
            employee.unidade_principal,
            saturday,
        )

        employees = planner.unit_weekends.get(
            key,
            0,
        )

        return (
            employees
            * self.UNIT_DISTRIBUTION_WEIGHT
        )
    
    def _can_rotate(
        self,
        employee,
        hotel,
    ) -> bool:
        """
    Indica se o colaborador pode
    rodar entre unidades.
    """

        return any(
            reinforcement.employee_id == employee.id
            for reinforcement in hotel.reinforcements
        )
    
    def _rotation_distribution_score(
        self,
        employee,
        hotel,
        weekend,
        planner,
    ) -> int:
        """
    Penaliza fins de semana já
    atribuídos a colaboradores
    rotativos.
    """

        if not planner._can_rotate(
            employee,
            hotel,
        ):
            return 0

        saturday, _ = weekend

        employees = planner.rotation_weekends.get(
            saturday,
            0,
        )

        return (
            employees
            * self.ROTATION_DISTRIBUTION_WEIGHT
        )