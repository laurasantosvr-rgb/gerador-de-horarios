from src.rules.validation.base_validation_rule import BaseValidationRule


class ScheduleValidator:
    """Valida um horário completo."""

    def __init__(self):

        self.rules: list[BaseValidationRule] = []

    def add_rule(
        self,
        rule,
    ) -> None:

        self.rules.append(rule)

    def validate(
        self,
        schedule,
        hotel,
        year: int,
        month: int,
    ) -> bool:

        for rule in self.rules:

            if not rule.validate(
                schedule,
                hotel,
                year,
                month,
            ):
                return False

        return True
    