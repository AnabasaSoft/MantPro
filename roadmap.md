# Roadmap / deuda técnica

Cosas detectadas durante una revisión de redundancias en el código (2026-09-22),
pendientes de decidir si merece la pena abordarlas. No son bugs urgentes, son
limpieza/consolidación de código duplicado.

## 1. `maquinas.py`: funciones de conteo/ranking casi clonadas

`contar_trabajos`/`contar_averias` y `ranking_trabajos`/`ranking_averias`
tienen exactamente la misma estructura; la única diferencia real es el filtro
`AND tags LIKE '%Avería%'`. Podrían unificarse en una sola función
parametrizada por filtro de tag, en vez de mantener dos copias que hay que
recordar actualizar en paralelo (como ya pasó al añadir `ranking_trabajos`
para el ranking del dashboard).

## 2. ~~`main.py`: combo de prioridad copiado 4 veces~~ (RESUELTO)

El bucle que rellena el combo de prioridad aparecía literalmente igual en
`EditDialog`, `DialogoEditarPendiente`, la pestaña Registro y la pestaña
Pendientes. Corregido: se ha añadido `_llenar_combo_prioridad(combo,
valor_actual)` junto a `_llenar_combo_especialidades`/`_llenar_combo_usuarios`
en `MaintenanceApp`, y los cuatro puntos lo usan ahora (los dos diálogos lo
llaman a través de `parent`, igual que ya hacían con los otros dos combos).

## 3. `main.py`: checkboxes de etiquetas duplicados

La construcción de los checks Urgente/Eléctrico/Mecánico/Preventivo(/Avería)
y su posterior recomposición en texto (`final_tags`/`lista_tags`) se repite
casi idéntica en `EditDialog`, `CompleteDialog` y la pestaña Registro. Podría
extraerse un helper que cree los checkboxes y otro que los serialice a texto.

## 4. ~~Timeout de conexión SQLite inconsistente entre módulos~~ (RESUELTO)

`maquinas.py._conn()` y `GestorBaseDatos.conectar()` (en `main.py`) no tenían
el `timeout=20` que sí tienen `almacen.py`/`usuarios.py` desde que se detectó
que el hilo del servidor Flask podía chocar con el PC escribiendo mucho
seguido ("database is locked"). Corregido: ambos usan ahora
`sqlite3.connect(..., timeout=20)`, igual que los otros dos módulos.

## 5. ~~`main.py`: conexiones SQLite sueltas sin helper centralizado~~ (RESUELTO)

Dentro de `ServidorSincronizacion` (el hilo del servidor Flask) había más de
una decena de `sqlite3.connect(self.db_path)` repartidos método a método,
con timeouts inconsistentes (la mayoría sin timeout, es decir 5s por
defecto; un par con `timeout=10`). Era precisamente el hilo que compite con
la GUI por la base de datos. Corregido: ahora todos pasan por
`self._conn()`, que reutiliza el `get_db_connection()` ya existente en el
módulo (`timeout=20` + modo WAL), en vez de repetir `sqlite3.connect` con
timeouts distintos en cada método.

## 6. Gráficas dibujadas a mano con boilerplate repetido (prioridad baja)

`GraficoCircularTrabajos`, `GraficoBarrasRanking` y `GraficoBarrasMensual`
repiten el mismo boilerplate de constructor (`color_texto`, `color_fondo`,
`setMinimumHeight`, estado vacío "sin datos"). La lógica de pintado en sí es
distinta en cada una, así que el ahorro de extraer una clase base sería
modesto; queda como mejora opcional, no prioritaria.
