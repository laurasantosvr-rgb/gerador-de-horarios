from src.rules.soft.base_rule import BaseRule


class SoftRuleEngine:
    """Aplica todas as Soft Rules."""

    def __init__(self):
        self.rules: list[BaseRule] = []

    def add_rule(self, rule: BaseRule) -> None:
        """Adiciona uma regra ao motor."""
        self.rules.append(rule)

    def total_penalty(
        self,
        schedule,
        hotel,
        year: int,
        month: int,
    ) -> int:
        """
        Calcula a penalização total do horário.
        """

        total = 0

        for rule in self.rules:

            total += rule.penalty(
                schedule,
                hotel,
                year,
                month,
            )

        return total