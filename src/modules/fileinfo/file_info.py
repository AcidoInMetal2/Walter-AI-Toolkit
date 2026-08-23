from pathlib import Path


class FileInfo:

    def __init__(self, archivo: str):

        self.path = Path(archivo)

        self.nombre = self.path.name

        self.extension = self.path.suffix.upper()

        self.ruta = str(self.path)

        self.tamano = self.obtener_tamano()


    def obtener_tamano(self):

        bytes_size = self.path.stat().st_size

        unidades = ["B", "KB", "MB", "GB", "TB"]

        size = float(bytes_size)

        indice = 0

        while size >= 1024 and indice < len(unidades)-1:

            size /= 1024

            indice += 1

        return f"{size:.2f} {unidades[indice]}"