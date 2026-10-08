import contextlib
import csv
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def ejecutar_proceso(self, *argumentos, entrada=""):
        return subprocess.run(
            [sys.executable, "-B", str(Path(__file__).with_name("todos.py").resolve()),
             *argumentos],
            cwd=self.directorio.name,
            input=entrada,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            check=False,
        )

    def test_cli_real_ciclo_completo_y_persistencia_entre_ejecuciones(self):
        for comando in (
            ("agregar", "Revisar inventario"),
            ("agregar", 'Confirmar entrega, "cajas"'),
            ("eliminar", "1"),
            ("agregar", "Revisar inventario"),
            ("guardar",),
        ):
            resultado = self.ejecutar_proceso(*comando)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            self.assertEqual(resultado.stderr, "")
        esperado = (
            'Lista de inventario\n1. Confirmar entrega, "cajas"\n2. Revisar inventario\n'
        )
        for comando in ("listar", "cargar"):
            resultado = self.ejecutar_proceso(comando)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            self.assertEqual(resultado.stdout, esperado)
        self.assertTrue(self.archivo.exists())

    def test_cli_real_menu_completo_en_una_sesion(self):
        entradas = "1\nPedido uno\n1\nPedido dos\n3\n1\n1\nPedido uno\n4\n5\n0\n"
        resultado = self.ejecutar_proceso(entrada=entradas)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(resultado.stderr, "")
        self.assertIn("Tarea eliminada: Pedido uno", resultado.stdout)
        self.assertIn("Tareas guardadas en todos.csv.", resultado.stdout)
        self.assertIn("1. Pedido dos\n2. Pedido uno\n", resultado.stdout)
        resultado = self.ejecutar_proceso("listar")
        self.assertEqual(
            resultado.stdout, "Lista de inventario\n1. Pedido dos\n2. Pedido uno\n"
        )

    def test_cli_real_ayuda_y_argumentos_invalidos(self):
        resultado = self.ejecutar_proceso("--help")
        self.assertEqual(resultado.returncode, 0)
        for comando in ("agregar", "listar", "eliminar", "guardar", "cargar", "interactivo"):
            self.assertIn(comando, resultado.stdout)
        resultado = self.ejecutar_proceso("eliminar", "texto")
        self.assertEqual(resultado.returncode, 2)
        self.assertNotIn("Traceback", resultado.stderr)
        resultado = self.ejecutar_proceso("eliminar", "1")
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("La posicion no existe", resultado.stderr)
        self.assertFalse(self.archivo.exists())

    def test_cli_real_archivo_personalizado(self):
        archivo = Path(self.directorio.name) / "inventario.csv"
        resultado = self.ejecutar_proceso(
            "--archivo", str(archivo), "interactivo", entrada="1\nPedido\n0\n"
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        resultado = self.ejecutar_proceso("--archivo", str(archivo), "cargar")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(resultado.stdout, "Lista de inventario\n1. Pedido\n")
        self.assertFalse(self.archivo.exists())

    def test_lista_inicial_vacia(self):
        self.assertEqual(
            self.ejecutar("listar"),
            (0, "Lista de inventario\nNo hay tareas pendientes.\n", ""),
        )

    def test_interactivo_agrega_muchas_tareas_en_una_ejecucion(self):
        titulos = [f"Pedido {numero}" for numero in range(1, 51)]
        entradas = []
        for titulo in titulos:
            entradas.extend(["1", titulo])
        entradas.extend(["2", "0"])
        with patch("builtins.input", side_effect=entradas):
            codigo, salida, errores = self.ejecutar("interactivo")
        self.assertEqual(codigo, 0)
        self.assertEqual(errores, "")
        self.assertIn("1. Pedido 1\n", salida)
        self.assertIn("50. Pedido 50\n", salida)
        self.assertEqual(ListaTareas(self.archivo).tareas, titulos)

    def test_sin_comando_abre_interactivo_y_conserva_tareas(self):
        ListaTareas(self.archivo).agregar("Preparar envio")
        with patch("builtins.input", side_effect=["1", "Revisar inventario", "0"]):
            codigo, salida, errores = self.ejecutar()
        self.assertEqual(codigo, 0)
        self.assertEqual(errores, "")
        self.assertIn("Tarea agregada: Revisar inventario", salida)
        self.assertEqual(
            ListaTareas(self.archivo).tareas, ["Preparar envio", "Revisar inventario"]
        )

    def test_interactivo_continua_tras_errores_y_permite_recrear(self):
        entradas = [
            "9", "1", "   ", "1", "Revisar inventario",
            "3", "texto", "3", "0", "3", "1",
            "1", "Revisar inventario", "2", "0",
        ]
        with patch("builtins.input", side_effect=entradas):
            codigo, salida, errores = self.ejecutar("interactivo")
        self.assertEqual(codigo, 0)
        self.assertIn("Opcion invalida", salida)
        self.assertIn("El titulo no puede estar vacio", errores)
        self.assertIn("La posicion debe ser un numero entero", errores)
        self.assertIn("La posicion no existe", errores)
        self.assertIn("Tarea eliminada: Revisar inventario", salida)
        self.assertIn("1. Revisar inventario\n", salida)
        self.assertEqual(ListaTareas(self.archivo).tareas, ["Revisar inventario"])

    def test_interactivo_fin_de_entrada_conserva_cambios(self):
        for interrupcion in (EOFError(), KeyboardInterrupt()):
            with self.subTest(interrupcion=type(interrupcion).__name__):
                with patch("builtins.input", side_effect=["1", "Pedido", interrupcion]):
                    codigo, salida, errores = self.ejecutar("interactivo")
                self.assertEqual(codigo, 0)
                self.assertEqual(errores, "")
                self.assertIn("Tarea agregada: Pedido", salida)
                self.assertIn("Pedido", ListaTareas(self.archivo).tareas)

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

    def test_save_todos_persiste_tareas_en_memoria_como_csv(self):
        lista = ListaTareas(self.archivo)
        titulos = ["Revisar inventario", 'Confirmar recepci\u00f3n, "cajas"\ny rutas']
        for titulo in titulos:
            lista.add_one_task(titulo)
        lista.save_todos()
        self.assertEqual(lista.tareas, titulos)
        self.assertEqual(ListaTareas(self.archivo).tareas, titulos)
        with self.archivo.open(encoding="utf-8", newline="") as archivo:
            self.assertEqual(
                list(csv.reader(archivo)), [["titulo"], *[[titulo] for titulo in titulos]]
            )

    def test_save_todos_reemplaza_contenido_sin_duplicar_tareas(self):
        lista = ListaTareas(self.archivo)
        lista.add_one_task("Preparar envio")
        lista.add_one_task("Revisar inventario")
        lista.save_todos()
        lista.save_todos()
        self.assertEqual(
            ListaTareas(self.archivo).tareas, ["Preparar envio", "Revisar inventario"]
        )
        lista.delet_task(1)
        lista.save_todos()
        self.assertEqual(ListaTareas(self.archivo).tareas, ["Revisar inventario"])
        lista.delet_task(1)
        lista.save_todos()
        self.assertEqual(ListaTareas(self.archivo).tareas, [])

    def test_save_todos_crea_csv_valido_con_lista_vacia(self):
        lista = ListaTareas(self.archivo)
        lista.save_todos()
        with self.archivo.open(encoding="utf-8", newline="") as archivo:
            self.assertEqual(list(csv.reader(archivo)), [["titulo"]])
        self.assertEqual(ListaTareas(self.archivo).tareas, [])

    def test_load_todos_reemplaza_memoria_sin_duplicar_tareas(self):
        lista = ListaTareas(self.archivo)
        titulos = ["Revisar inventario", 'Confirmar recepci\u00f3n, "cajas"\ny rutas']
        with self.archivo.open("w", encoding="utf-8", newline="") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["titulo"])
            escritor.writerows([titulo] for titulo in titulos)
        contenido = self.archivo.read_bytes()
        lista.add_one_task("Tarea sin guardar")
        lista.load_todos()
        self.assertEqual(lista.tareas, titulos)
        lista.load_todos()
        self.assertEqual(lista.tareas, titulos)
        self.assertEqual(self.archivo.read_bytes(), contenido)

    def test_load_todos_archivo_inexistente_deja_lista_vacia(self):
        lista = ListaTareas(self.archivo)
        lista.add_one_task("Tarea sin guardar")
        lista.load_todos()
        self.assertEqual(lista.tareas, [])
        self.assertFalse(self.archivo.exists())

    def test_load_todos_csv_sin_tareas_deja_lista_vacia(self):
        lista = ListaTareas(self.archivo)
        lista.add_one_task("Tarea sin guardar")
        self.archivo.write_text("titulo\n", encoding="utf-8")
        lista.load_todos()
        self.assertEqual(lista.tareas, [])

    def test_load_todos_csv_invalido_conserva_memoria(self):
        lista = ListaTareas(self.archivo)
        lista.add_one_task("Tarea sin guardar")
        for contenido in (
            "",
            "otra_columna\nPedido\n",
            "titulo\nPedido valido\n   \n",
            "titulo\nPedido valido\nPedido,extra\n",
        ):
            with self.subTest(contenido=contenido):
                self.archivo.write_text(contenido, encoding="utf-8")
                with self.assertRaises(ValueError):
                    lista.load_todos()
                self.assertEqual(lista.tareas, ["Tarea sin guardar"])
                self.assertEqual(self.archivo.read_text(encoding="utf-8"), contenido)

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