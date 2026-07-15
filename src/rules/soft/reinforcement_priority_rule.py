from src.rules.soft.base_rule import BaseRule


class ReinforcementPriorityRule(BaseRule):
    """Valoriza os reforços preferenciais."""

    name = "Reinforcement Priority Rule"
    description = "Dá prioridade aos reforços definidos."
    weight = 10

    def penalty(
        self,
        schedule,
        hotel,
        year: int,
        month: int,
    ) -> int:

        return 0