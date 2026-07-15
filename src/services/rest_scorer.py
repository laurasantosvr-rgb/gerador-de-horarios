from datetime import timedelta

class RestScorer:
    """
    Calcula a pontuação de pares de folgas
    e de folgas individuais.
    """

    UNIT_DISTRIBUTION_WEIGHT = 100000
    WEEK_BALANCE_WEIGHT = 70000
    TOTAL_DISTRIBUTION_WEIGHT = 50000
    ROTATION_DISTRIBUTION_WEIGHT = 40000
    HOLIDAY_OFF_FAIRNESS_WEIGHT = 30000
    FRIDAY_WEIGHT = 25000
    WORKLOAD_WEIGHT = 100
    WEEKEND_WEIGHT = 50
    FAIRNESS_WEIGHT = 20

    def score_pair(
        self,
        schedule,
        hotel,
        employee,
        pair,
        planner,
    ) -> int:

        score = 0

        score += self._unit_distribution_score(
            hotel,
            employee,
            pair,
            planner,
        )

        score += self._total_distribution_score(
            pair,
            planner,
        )

        score += self._rotation_distribution_score(
            hotel,
            employee,
            pair,
            planner,
        )

        score += self._workload_score(
            hotel,
            pair,
        )

        score += self._weekend_score(
            pair,
        )

        score += self._friday_score(
            pair,
        )

        score += self._fairness_score(
            schedule,
            employee,
            pair,
        )

        score += self._holiday_off_fairness_score(
            schedule,
            hotel,
            employee,
            pair,
            planner,
        )

        score += self._week_balance_score(
            planner,
            pair,
        )

        return score
    
    def score_single_day(
        self,
        schedule,
        hotel,
        employee,
        days,
        planner,
    ) -> int:

        score = 0

        score += self._unit_distribution_score(
            hotel,
            employee,
            days,
            planner,
        )

        score += self._total_distribution_score(
            days,
            planner,
        )

        score += self._rotation_distribution_score(
            hotel,
            employee,
            days,
            planner,
        )

        score += self._workload_score(
            hotel,
            days,
        )

        score += self._weekend_score(
            days,
        )

        score += self._friday_score(
            days,
        )

        score += self._fairness_score(
            schedule,
            employee,
            days,
        )

        score += self._holiday_off_fairness_score(
            schedule,
            hotel,
            employee,
            days,
            planner,
        )

        score += self._week_balance_score(
            planner,
            days,
        )

        return score

    def _unit_distribution_score(
        self,
        hotel,
        employee,
        days,
        planner,
    ) -> int:
        """
    Penaliza concentrações de folgas
    dentro da mesma unidade.
    """
        
        unit = hotel.units[
            employee.unidade_principal
        ]
        
        total = len(
            planner._unit_employees(
                hotel,
                employee.unidade_principal,
            )
        )

        if total == 0:
            return 0

        score = 0

        for day in days:

            key = (
                employee.unidade_principal,
                day,
            )

            employees_off = (
                planner.total_day_offs.get(day, 0)
                + planner.vacation_day_offs.get(day, 0)
                + planner.fixed_day_offs.get(day, 0)
                + 1
            )

            score += self._distribution_penalty(
                employees_off,
                total,
                unit.minimo_colaboradores,
                self.UNIT_DISTRIBUTION_WEIGHT,
            )

        return score

    def _rotation_distribution_score(
        self,
        hotel,
        employee,
        days,
        planner,
    ) -> int:
        """
    Penaliza dias em que já existem
    muitos colaboradores rotativos
    de folga.
    """

        if not planner._can_rotate(
            employee,
            hotel,
        ):
            return 0

        total = planner._rotation_count(
            hotel,
        )

        if total == 0:
            return 0

        score = 0

        for day in days:

            employees_off = (
                planner.total_day_offs.get(day, 0)
                + planner.vacation_day_offs.get(day, 0)
                + planner.fixed_day_offs.get(day, 0)
                + 1
            )

            score += self._rotation_distribution_penalty(
                employees_off,
                total,
                self.ROTATION_DISTRIBUTION_WEIGHT,
            )

        return score
    
    def _workload(
        self,
        hotel,
        days,
    ) -> int:
        """
    Calcula a carga total dos dias.
    """

        total = 0

        for workload in hotel.daily_workloads:

            if workload.data not in days:
                continue

            unit = hotel.units[
                workload.unidade
            ]

            total += (
                workload.checkouts
                * unit.checkout_minutos
            )

            total += (
                workload.stayovers
                * unit.stayover_minutos
            )

            total += unit.zonas_comuns_minutos

        return total


    def _workload_score(
        self,
        hotel,
        days,
    ) -> int:
        """
    Penaliza folgas em dias
    de maior carga de trabalho.
    """

        workload = self._workload(
            hotel,
            days,
        )

        return (
            workload
            * self.WORKLOAD_WEIGHT
        )

    def _weekend_score(
        self,
        days,
    ):
        score = 0

        for day in days:

            if day.weekday() == 5:      # sábado
                score += 30000

            elif day.weekday() == 6:    # domingo
                score += 30000

        return score
    
    def _fairness_score(
        self,
        schedule,
        employee,
    days,
    ) -> int:
        """
    Penaliza colaboradores que já tiveram
    muitos fins de semana livres,
    promovendo uma distribuição equilibrada.
    """

        weekend_days = sum(
            1
            for day in days
            if day.weekday() in (5, 6)
        )

        if weekend_days == 0:
            return 0

        # TODO:
        # Utilizar o histórico de horários
        # para contar fins de semana já atribuídos.

        return weekend_days * self.FAIRNESS_WEIGHT
    
    def _distribution_penalty(
        self,
        off,
        total,
        minimum,
        weight,
    ):
        available = total - off

        if available < minimum:
            return 1_000_000

        if available == minimum:
            return 200_000

        if available == minimum + 1:
            return 50_000

        return int(
            (off / total) * weight
        )
    
    def _rotation_distribution_penalty(
        self,
        off,
        total,
        weight,
    ):
        ratio = off / total

        if ratio >= 0.80:
            return 1_000_000

        if ratio >= 0.60:
            return 200_000

        if ratio >= 0.40:
            return 50_000

        return int(
            ratio * weight
        )
    
    def _total_distribution_score(
        self,
        days,
        planner,
    ):
        """
    Penaliza dias em que já existem
    muitos colaboradores de folga.
    """

        score = 0

        for day in days:

            employees_off = (
                planner.total_day_offs.get(day, 0)
                + planner.vacation_day_offs.get(day, 0)
                + planner.fixed_day_offs.get(day, 0)
                + 1
            )

            score += (
                employees_off
                * self.TOTAL_DISTRIBUTION_WEIGHT
            )

        return score

    
    def _holiday_off_fairness_score(
        self,
        schedule,
        hotel,
        employee,
        days,
        planner,
    ):
        """
    Penaliza colaboradores que já tiveram
    muitos feriados de folga.
    """

        holiday_days = sum(
            1
            for day in days
            if any(
                holiday.data == day
                for holiday in hotel.holidays
            )
        )
        
        if holiday_days == 0:
            return 0

        holiday_offs = planner.history.holiday_offs(
            employee.id,
        )

        return (
         holiday_offs
            * holiday_days
            * self.HOLIDAY_OFF_FAIRNESS_WEIGHT
        )
    
    def _week_balance_score(
        self,
        planner,
        days,
    ):
        """
    Penaliza atribuições que aumentem
    o desequilíbrio das folgas ao
    longo da semana.
    """

        #
        # Segunda-feira da semana.
        #

        monday = min(days)

        while monday.weekday() != 0:
            monday -= timedelta(days=1)

        #
        # Indisponibilidade simulada
        # de segunda a sexta.
        #

        counts = []

        for offset in range(5):

            day = monday + timedelta(days=offset)

            count = (
                planner.total_day_offs.get(
                    day,
                    0,
                )
                + planner.vacation_day_offs.get(
                    day,
                    0,
                )
                + planner.fixed_day_offs.get(
                    day,
                    0,
                )
            )

            if day in days:
                count += 1

            counts.append(count)

        #
        # Desequilíbrio.
        #

        average = sum(counts) / len(counts)

        imbalance = sum(
            abs(count - average)
            for count in counts
        )

        return int(
            imbalance
            * self.WEEK_BALANCE_WEIGHT
        )

    def _friday_score(
        self,
        days,
    ):
        """
        Penaliza folgas que incluam sexta-feira.
        """

        score = 0

        for day in days:
            if day.weekday() == 4:   # sexta-feira
                score += self.FRIDAY_WEIGHT

        return score
