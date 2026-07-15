from src.rules.hard.base_rule import BaseRule


class RuleEngine:
    """Responsável por verificar todas as regras."""

    def __init__(self):
        self.rules: list[BaseRule] = []

    def add_rule(self, rule: BaseRule):
        """Adiciona uma regra."""
        self.rules.append(rule)

    def can_assign(
        self,
        employee,
        unit,
        day,
        hotel,
        schedule,
    ) -> bool:

        for rule in self.rules:

            if not rule.is_valid(
                employee,
                unit,
                day,
                hotel,
                schedule,
            ):
                return False

        return True