"""
Utilidad chica para formatear segundos como texto de reloj (HH:MM:SS),
usada donde se muestran timestamps de audio (transcript con hablantes,
etc). Vive acá porque tanto módulos como la UI la necesitan.
"""


def formatear_tiempo(segundos: float) -> str:
    total = int(segundos)
    horas, resto = divmod(total, 3600)
    minutos, segs = divmod(resto, 60)

    if horas:
        return f"{horas:02d}:{minutos:02d}:{segs:02d}"

    return f"{minutos:02d}:{segs:02d}"
