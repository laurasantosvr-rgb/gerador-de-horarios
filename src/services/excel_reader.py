from pathlib import Path

import pandas as pd

from src.config import EXCEL_FILE


class ExcelReader:
    """Lê o ficheiro Excel com os dados do projeto."""

    REQUIRED_SHEETS = [
        "Funcionarios",
        "Unidades",
        "Ferias",
        "Substituicoes",
        "Reforcos",
        "Feriados",
        "CargaDiaria",
        "FolgasFixas",
    ]

    def __init__(self, file=None):

        # Se vier um ficheiro da interface
        if file is not None:
            self.file = file
            self.file_path = None

        # Caso contrário usa o ficheiro por defeito
        else:

            self.file = None

            self.file_path = (
                Path(__file__).resolve().parents[2]
                / "data"
                / "input"
                / EXCEL_FILE
            )

    def load(self):

        # Excel vindo do Streamlit
        if self.file is not None:
            excel = pd.ExcelFile(self.file)

        # Excel da pasta data/input
        else:

            if not self.file_path.exists():
                raise FileNotFoundError(
                    f"Ficheiro não encontrado:\n{self.file_path}"
                )

            excel = pd.ExcelFile(self.file_path)

        data = {}

        for sheet in self.REQUIRED_SHEETS:

            if sheet not in excel.sheet_names:
                raise ValueError(
                    f"A folha '{sheet}' não existe no ficheiro Excel."
                )

            data[sheet] = pd.read_excel(
                excel,
                sheet_name=sheet
            )

        return data