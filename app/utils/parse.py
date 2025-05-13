from datetime import timedelta
import re

def parse_date(value: str = "") -> timedelta:
    """Parses a duration string (e.g., '3d', '6h30m', '2d4h20m10s') into a timedelta object."""
    if not value:
        return timedelta(days=1)  # Valor por defecto: 1 día

    # Expresión regular para capturar números seguidos de unidades (d, h, m, s)
    pattern = re.findall(r"(\d+)([dhms])", value)
    
    if not pattern:
        raise ValueError(f"Formato inválido: '{value}'. Usa formatos como '1d', '3h30m', '45m10s'.")

    # Mapeo de unidades a timedelta
    tiempo_total = timedelta()
    unidades = {"d": "days", "h": "hours", "m": "minutes", "s": "seconds"}

    for cantidad, unidad in pattern:
        cantidad = int(cantidad)
        tiempo_total += timedelta(**{unidades[unidad]: cantidad})

    return tiempo_total