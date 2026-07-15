from dataclasses import dataclass


@dataclass(slots=True)
class Unit:
    """Representa uma unidade (AP, JP, HM ou B)."""

    nome: str
    checkout_minutos: int
    stayover_minutos: int
    zonas_comuns_minutos: int
    frequencia_zc: str
    minimo_colaboradores: int