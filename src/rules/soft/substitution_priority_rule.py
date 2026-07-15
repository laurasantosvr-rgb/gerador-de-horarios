from src.rules.soft.base_rule import BaseRule


class SubstitutionPriorityRule(BaseRule):
    """Valoriza a utilização dos substitutos preferenciais."""

    name = "Substitution Priority Rule"

    description = (
        "Dá preferência aos colaboradores definidos "
        "como substitutos."
    )

    weight = 10

    def penalty(
        self,
        schedule,
        hotel,
        year: int,
        month: int,
    ) -> int:
        """
        Nesta primeira versão ainda não existe lógica
        para avaliar substituições.
        """

        return 0