class DataValidator:

    REQUIRED_COLUMNS = {
        "Funcionarios": [
            "Nome",
            "Ativo",
            "Horas por dia",
            "Unidade principal",
            "Pode rodar",
            "Trabalha fins de semana",
            "Trabalha feriados",
        ]
    }

    def validate(self, data):

        for sheet, columns in self.REQUIRED_COLUMNS.items():

            dataframe = data[sheet]

            for column in columns:

                if column not in dataframe.columns:
                    raise ValueError(
                        f"Na folha '{sheet}' falta a coluna '{column}'."
                    )

        return True