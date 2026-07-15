from dataclasses import dataclass


@dataclass
class Employee:
    """Representa um colaborador da equipa de housekeeping."""
    
    id: int
    nome: str
    ativo: bool
    horas_por_dia: int
    unidade_principal: str
    pode_rodar: bool
    trabalha_fins_de_semana: bool
    trabalha_feriados: bool