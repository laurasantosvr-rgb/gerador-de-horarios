class WorkloadCalculator:

    WEEKDAYS = {
        0: "segunda-feira",
        1: "terça-feira",
        2: "quarta-feira",
        3: "quinta-feira",
        4: "sexta-feira",
        5: "sábado",
        6: "domingo",
    }

    def calculate_required_minutes(
        self,
        unit,
        daily_workload,
    ) -> int:

        # Unidades sem carga diária
        if daily_workload is None:
            return unit.minimo_colaboradores * 60

        minutes = (
            daily_workload.checkouts * unit.checkout_minutos
            + daily_workload.stayovers * unit.stayover_minutos
        )

        frequencia = unit.frequencia_zc.strip().lower()

        if frequencia == "diário":
            minutes += unit.zonas_comuns_minutos

        elif (
            frequencia
            == self.WEEKDAYS[daily_workload.data.weekday()]
        ):
            minutes += unit.zonas_comuns_minutos

        return max(
            minutes,
            unit.minimo_colaboradores * 60,
        )