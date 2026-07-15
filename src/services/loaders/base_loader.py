class BaseLoader:
    """Classe base para converter DataFrames em objetos Python."""

    def __init__(self, dataframe):
        self.dataframe = dataframe

    def load(self):
        """Percorre todas as linhas e cria uma lista de objetos."""

        objects = []

        for _, row in self.dataframe.iterrows():
            objects.append(self.create_object(row))

        return objects

    def create_object(self, row):
        """Este método será implementado pelas subclasses."""
        raise NotImplementedError(
            "As subclasses devem implementar o método create_object()."
        )