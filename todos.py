import argparse
import csv
import sys
from pathlib import Path


class ListaTareas:
    def __init__(self, archivo="todos.csv"):
        self.archivo = Path(archivo)
        self.tareas = []
        self.cargar()

    def cargar(self):
        if not self.archivo.exists():
            self.tareas = []
            return
        with self.archivo.open(encoding="utf-8", newline="") as archivo:
            lector = csv.DictReader(archivo)
            if lector.fieldnames != ["titulo"]:
                raise ValueError("El CSV debe tener una sola columna llamada titulo.")
            tareas = []
            for fila in lector:
                if None in fila or not fila["titulo"] or not fila["titulo"].strip():
                    raise ValueError("El CSV contiene una tarea invalida.")
                tareas.append(fila["titulo"])
        self.tareas = tareas

    def guardar(self):
        with self.archivo.open("w", encoding="utf-8", newline="") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["titulo"])
            escritor.writerows([titulo] for titulo in self.tareas)

    def add_one_task(self, titulo):
        titulo = titulo.strip()
        if not titulo:
            raise ValueError("El titulo no puede estar vacio.")
        self.tareas.append(titulo)

    def agregar(self, titulo):
        self.add_one_task(titulo)
        self.guardar()

    def print_list(self):
        print("Lista de inventario")
        if not self.tareas:
            print("No hay tareas pendientes.")
            return
        for posicion, titulo in enumerate(self.tareas, start=1):
            print(f"{posicion}. {titulo}")

    def delet_task(self, number_to_delete):
        if not isinstance(number_to_delete, int) or isinstance(number_to_delete, bool):
            raise ValueError("La posicion debe ser un numero entero.")
        if number_to_delete < 1 or number_to_delete > len(self.tareas):
            raise ValueError("La posicion no existe en la lista de tareas.")
        return self.tareas.pop(number_to_delete - 1)

    def eliminar(self, posicion):
        titulo = self.delet_task(posicion)
        self.guardar()
        return titulo


def main(argv=None):
    parser = argparse.ArgumentParser(description="Gestion de tareas de logistica.")
    parser.add_argument(
        "--archivo", default="todos.csv", help="Archivo CSV (por defecto: todos.csv)."
    )
    comandos = parser.add_subparsers(dest="comando", required=True)
    agregar = comandos.add_parser("agregar", help="Agregar una tarea por titulo.")
    agregar.add_argument("titulo")
    comandos.add_parser("listar", help="Mostrar tareas pendientes numeradas.")
    eliminar = comandos.add_parser("eliminar", help="Eliminar por posicion.")
    eliminar.add_argument("posicion", type=int)
    argumentos = parser.parse_args(argv)

    try:
        lista = ListaTareas(argumentos.archivo)
        if argumentos.comando == "agregar":
            lista.agregar(argumentos.titulo)
            print(f"Tarea agregada: {lista.tareas[-1]}")
        elif argumentos.comando == "eliminar":
            titulo = lista.eliminar(argumentos.posicion)
            print(f"Tarea eliminada: {titulo}")
        else:
            lista.print_list()
    except (OSError, ValueError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())