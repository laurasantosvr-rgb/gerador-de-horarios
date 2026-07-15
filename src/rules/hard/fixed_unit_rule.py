from src.rules.hard.base_rule import BaseRule


class FixedUnitRule(BaseRule):
    """Impede colaboradores de serem colocados fora da unidade fixa."""

    name = "Fixed Unit"

    description = (
        "Os colaboradores que não podem rodar "
        "só podem trabalhar na sua unidade principal."
    )

    def is_valid(
        self,
        employee,
        unit,
        day,
        hotel,
        schedule,
    ) -> bool:

        if employee.pode_rodar:
            return True

        return employee.unidade_principal == unit.nome