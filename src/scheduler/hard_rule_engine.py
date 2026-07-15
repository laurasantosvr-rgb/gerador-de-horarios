from src.rules.hard.base_rule import BaseRule


class HardRuleEngine:
    """Aplica todas as Hard Rules."""

    def __init__(self):
        self.rules: list[BaseRule] = []

    def add_rule(self, rule: BaseRule) -> None:
        """Adiciona uma regra ao motor."""
        self.rules.append(rule)

    def can_assign(
        self,
        employee,
        unit,
        day,
        hotel,
        schedule,
    ) -> bool:
        """
        Verifica se todas as Hard Rules são satisfeitas.
        """

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