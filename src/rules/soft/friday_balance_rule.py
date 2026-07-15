from src.rules.soft.base_rule import BaseRule


class FridayBalanceRule(BaseRule):

    name = "Friday Balance Rule"

    description = (
        "Evita folgas às sextas-feiras."
    )

    weight = 20

    def penalty(
        self,
        schedule,
        hotel,
        year,
        month,
    ) -> int:

        friday_offs = schedule.count_friday_offs(
            hotel,
            year,
            month,
        )

        return friday_offs * self.weight