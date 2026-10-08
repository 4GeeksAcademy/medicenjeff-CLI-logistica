# medicenjeff-CLI-logistica
Este repositorio tiene como objetivo crear la CLI de una empresa de logística, siguiendo el brief compartido por el product manager de la empresa.

## Requisitos

Python 3. No requiere instalar dependencias.

## Uso

Para gestionar tantas tareas como necesites en una misma ejecución:

```bash
python3 todos.py
```

El menú permite agregar (`1`), mostrar (`2`), eliminar (`3`), guardar (`4`),
cargar nuevamente el CSV (`5`) y salir (`0`).
Después de cada operación vuelve al menú, sin un límite fijo de tareas.
Cada cambio se guarda automáticamente en `todos.csv`. Los títulos se escriben
directamente cuando se solicitan, sin comillas. También puedes iniciar este modo
con `python3 todos.py interactivo`. `Ctrl+C` o `Ctrl+D` finalizan la sesión;
los cambios realizados ya están guardados.

Los comandos individuales siguen disponibles.
Desde la carpeta del repositorio:

```bash
python3 todos.py agregar "Preparar envio"
python3 todos.py agregar "Revisar inventario"
python3 todos.py listar
python3 todos.py eliminar 1
python3 todos.py agregar "Preparar envio"
python3 todos.py listar
python3 todos.py guardar
python3 todos.py cargar
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

`guardar` vuelve a escribir las tareas cargadas en el CSV; `cargar` las lee y
las muestra numeradas. No necesitas entrar al intérprete de Python ni escribir
llamadas como `add_one_task(...)` en Bash: toda la experiencia está disponible
mediante estos comandos y el menú interactivo.

Puedes elegir otro archivo usando la opción antes del comando:

```bash
python3 todos.py --archivo /ruta/todos.csv listar
python3 todos.py --help
```

## Pruebas

```bash
python3 -m unittest -v test_todos
```
