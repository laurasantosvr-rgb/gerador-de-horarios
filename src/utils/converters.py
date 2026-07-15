def to_bool(value):
    """Converte S/N para True/False."""

    return str(value).strip().upper() == "S"