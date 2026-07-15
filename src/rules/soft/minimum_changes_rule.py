from src.rules.soft.base_rule import BaseRule


class MinimumChangesRule(BaseRule):
    """Penaliza alterações desnecessárias ao horário."""

    name = "Minimum Changes Rule"

    description = (
        "Quando o horário é recalculado, devem ser feitas "
        "o mínimo possível de alterações."
    )

    weight = 100

    def penalty(
        self,
        schedule,
        hotel,
        year,
        month,
        previous_schedule=None,
    ) -> int:

        if previous_schedule is None:
            return 0

        changes = schedule.count_changes(
            previous_schedule,
        )

        return changes * self.weight