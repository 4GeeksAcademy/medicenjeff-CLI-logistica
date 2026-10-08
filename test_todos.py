import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path

from todos import ListaTareas, main


class TestListaTareas(unittest.TestCase):
    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.addCleanup(self.directorio.cleanup)
        self.archivo = Path(self.directorio.name) / "todos.csv"

    def ejecutar(self, *argumentos):
        salida = io.StringIO()
        errores = io.StringIO()
        with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(errores):
            codigo = main(["--archivo", str(self.archivo), *argumentos])
        return codigo, salida.getvalue(), errores.getvalue()

    def test_lista_inicial_vacia(self):
        self.assertEqual(
            self.ejecutar("listar"),
            (0, "Lista de inventario\nNo hay tareas pendientes.\n", ""),
        )

    def test_print_list_vacia(self):
        lista = ListaTareas(self.archivo)
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            lista.print_list()
        self.assertEqual(
            salida.getvalue(), "Lista de inventario\nNo hay tareas pendientes.\n"
        )
        self.assertEqual(lista.tareas, [])
        self.assertFalse(self.archivo.exists())

    def test_print_list_numera_tareas_en_memoria_desde_uno(self):
        lista = ListaTareas(self.archivo)
        lista.add_one_task("Revisar inventario")
        lista.add_one_task("Confirmar entrega")
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            lista.print_list()
        self.assertEqual(
            salida.getvalue(),
            "Lista de inventario\n1. Revisar inventario\n2. Confirmar entrega\n",
        )
        self.assertEqual(lista.tareas, ["Revisar inventario", "Confirmar entrega"])
        self.assertFalse(self.archivo.exists())

    def test_add_one_task_agrega_en_memoria_sin_crear_archivo(self):
        lista = ListaTareas(self.archivo)
        lista.add_one_task("  Revisar inventario  ")
        lista.add_one_task("Confirmar entrega")
        self.assertEqual(lista.tareas, ["Revisar inventario", "Confirmar entrega"])
        self.assertFalse(self.archivo.exists())

    def test_add_one_task_no_modifica_csv_existente(self):
        lista = ListaTareas(self.archivo)
        lista.agregar("Preparar envio")
        contenido = self.archivo.read_bytes()
        lista.add_one_task("Revisar inventario")
        self.assertEqual(lista.tareas, ["Preparar envio", "Revisar inventario"])
        self.assertEqual(self.archivo.read_bytes(), contenido)
        self.assertEqual(ListaTareas(self.archivo).tareas, ["Preparar envio"])
        lista.guardar()
        self.assertEqual(ListaTareas(self.archivo).tareas, lista.tareas)

    def test_add_one_task_rechaza_titulos_vacios(self):
        lista = ListaTareas(self.archivo)
        for titulo in ("", "   "):
            with self.subTest(titulo=titulo):
                with self.assertRaises(ValueError):
                    lista.add_one_task(titulo)
        self.assertEqual(lista.tareas, [])
        self.assertFalse(self.archivo.exists())

    def test_guardar_y_cargar_titulo_con_coma_y_salto_de_linea(self):
        titulo = "Revisar pedidos, cajas\ny rutas"
        ListaTareas(self.archivo).agregar(titulo)
        self.assertEqual(ListaTareas(self.archivo).tareas, [titulo])
        with self.archivo.open(encoding="utf-8", newline="") as archivo:
            self.assertEqual(list(csv.reader(archivo)), [["titulo"], [titulo]])

    def test_flujo_eliminar_y_volver_a_crear(self):
        self.assertEqual(self.ejecutar("agregar", "Preparar envio")[0], 0)
        self.assertEqual(self.ejecutar("agregar", "Revisar inventario")[0], 0)
        self.assertEqual(
            self.ejecutar("listar")[1],
            "Lista de inventario\n1. Preparar envio\n2. Revisar inventario\n",
        )
        self.assertEqual(self.ejecutar("eliminar", "1")[0], 0)
        self.assertEqual(
            self.ejecutar("listar")[1], "Lista de inventario\n1. Revisar inventario\n"
        )
        self.assertEqual(self.ejecutar("agregar", "Preparar envio")[0], 0)
        self.assertEqual(
            self.ejecutar("listar")[1],
            "Lista de inventario\n1. Revisar inventario\n2. Preparar envio\n",
        )

    def test_eliminar_ultima_tarea_y_recargar(self):
        lista = ListaTareas(self.archivo)
        lista.agregar("Preparar envio")
        lista.eliminar(1)
        self.assertEqual(ListaTareas(self.archivo).tareas, [])

    def test_delet_task_elimina_por_posicion_y_renumera(self):
        lista = ListaTareas(self.archivo)
        lista.add_one_task("Preparar envio")
        lista.add_one_task("Revisar inventario")
        lista.add_one_task("Confirmar entrega")
        self.assertEqual(lista.delet_task(2), "Revisar inventario")
        self.assertEqual(lista.tareas, ["Preparar envio", "Confirmar entrega"])
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            lista.print_list()
        self.assertEqual(
            salida.getvalue(),
            "Lista de inventario\n1. Preparar envio\n2. Confirmar entrega\n",
        )
        self.assertEqual(lista.delet_task(2), "Confirmar entrega")
        self.assertEqual(lista.delet_task(1), "Preparar envio")
        self.assertEqual(lista.tareas, [])
        self.assertFalse(self.archivo.exists())

    def test_delet_task_no_modifica_csv_hasta_guardar(self):
        lista = ListaTareas(self.archivo)
        lista.agregar("Preparar envio")
        lista.agregar("Revisar inventario")
        contenido = self.archivo.read_bytes()
        lista.delet_task(1)
        self.assertEqual(lista.tareas, ["Revisar inventario"])
        self.assertEqual(self.archivo.read_bytes(), contenido)
        lista.guardar()
        self.assertEqual(ListaTareas(self.archivo).tareas, ["Revisar inventario"])

    def test_delet_task_rechaza_posiciones_invalidas_sin_modificar_lista(self):
        lista = ListaTareas(self.archivo)
        lista.add_one_task("Revisar inventario")
        for posicion in (0, -1, 2, "1", 1.5, None, True, False):
            with self.subTest(posicion=posicion):
                with self.assertRaises(ValueError):
                    lista.delet_task(posicion)
                self.assertEqual(lista.tareas, ["Revisar inventario"])
        self.assertFalse(self.archivo.exists())

    def test_delet_task_rechaza_lista_vacia(self):
        lista = ListaTareas(self.archivo)
        with self.assertRaises(ValueError):
            lista.delet_task(1)
        self.assertEqual(lista.tareas, [])
        self.assertFalse(self.archivo.exists())

    def test_posiciones_invalidas_no_modifican_archivo(self):
        ListaTareas(self.archivo).agregar("Preparar envio")
        contenido = self.archivo.read_bytes()
        for posicion in ("0", "-1", "2"):
            with self.subTest(posicion=posicion):
                codigo, salida, errores = self.ejecutar("eliminar", posicion)
                self.assertEqual(codigo, 1)
                self.assertEqual(salida, "")
                self.assertIn("La posicion no existe", errores)
                self.assertEqual(self.archivo.read_bytes(), contenido)

    def test_titulo_vacio_no_crea_archivo(self):
        self.assertEqual(self.ejecutar("agregar", "   ")[0], 1)
        self.assertFalse(self.archivo.exists())

    def test_csv_invalido_no_se_sobrescribe(self):
        self.archivo.write_text("columna_incorrecta\nPedido\n", encoding="utf-8")
        contenido = self.archivo.read_bytes()
        self.assertEqual(self.ejecutar("agregar", "Preparar envio")[0], 1)
        self.assertEqual(self.archivo.read_bytes(), contenido)


if __name__ == "__main__":
    unittest.main()