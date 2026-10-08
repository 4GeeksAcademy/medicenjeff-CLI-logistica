# medicenjeff-CLI-logistica
Este repositorio tiene como objetivo crear la CLI de una empresa de logística, siguiendo el brief compartido por el product manager de la empresa.

## Requisitos

Python 3. No requiere instalar dependencias.

## Uso

Desde la carpeta del repositorio:

```bash
python3 todos.py agregar "Preparar envio"
python3 todos.py agregar "Revisar inventario"
python3 todos.py listar
python3 todos.py eliminar 1
python3 todos.py agregar "Preparar envio"
python3 todos.py listar
```

La lista final muestra:

```text
Lista de inventario
1. Revisar inventario
2. Preparar envio
```

Todas las tareas de la lista están pendientes. Las posiciones empiezan en 1 y
se recalculan al eliminar. Para volver a crear una tarea eliminada, usa `agregar`
con su título; se incorpora al final de la lista.

Cada comando carga automáticamente `todos.csv` desde el directorio actual.
Agregar o eliminar guarda inmediatamente la lista en ese archivo, con una
columna `titulo`. Si el archivo no existe, se empieza con una lista vacía y se
crea al agregar la primera tarea. Los títulos con comas se guardan correctamente
mediante el formato CSV. No se aceptan títulos vacíos ni posiciones inexistentes.

Puedes elegir otro archivo usando la opción antes del comando:

```bash
python3 todos.py --archivo /ruta/todos.csv listar
python3 todos.py --help
```

## Pruebas

```bash
python3 -m unittest -v test_todos
```
