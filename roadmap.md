# Roadmap / deuda técnica

Cosas detectadas durante una revisión de redundancias en el código (2026-09-22),
pendientes de decidir si merece la pena abordarlas. No son bugs urgentes, son
limpieza/consolidación de código duplicado.

## 1. ~~`maquinas.py`: funciones de conteo/ranking casi clonadas~~ (RESUELTO)

`contar_trabajos`/`contar_averias` y `ranking_trabajos`/`ranking_averias`
tenían exactamente la misma estructura; la única diferencia real era el
filtro `AND tags LIKE '%Avería%'`. Corregido: ahora comparten base común,
`_contar_tareas(id_maquina, fecha_inicio, fecha_fin, solo_averias)` y
`_ranking_por(contador, top_n, fecha_inicio, fecha_fin)`, y las cuatro
funciones públicas quedan como envoltorios de una línea que solo fijan el
parámetro que las distingue. La firma y el comportamiento de las cuatro
funciones públicas no cambian, así que no afecta a quien ya las use.

## 2. ~~`main.py`: combo de prioridad copiado 4 veces~~ (RESUELTO)

El bucle que rellena el combo de prioridad aparecía literalmente igual en
`EditDialog`, `DialogoEditarPendiente`, la pestaña Registro y la pestaña
Pendientes. Corregido: se ha añadido `_llenar_combo_prioridad(combo,
valor_actual)` junto a `_llenar_combo_especialidades`/`_llenar_combo_usuarios`
en `MaintenanceApp`, y los cuatro puntos lo usan ahora (los dos diálogos lo
llaman a través de `parent`, igual que ya hacían con los otros dos combos).

## 3. ~~`main.py`: checkboxes de etiquetas duplicados~~ (RESUELTO)

La construcción de los checks Urgente/Eléctrico/Mecánico/Preventivo(/Avería)
y su posterior recomposición en texto (`final_tags`/`lista_tags`) se repetía
casi idéntica en `EditDialog`, `CompleteDialog` y la pestaña Registro.
Corregido: se han añadido dos helpers a nivel de módulo,
`_crear_checks_etiquetas(host, layout, incluir_averia=True)` (crea los
checks, los estiliza y los añade al layout) y `_tags_desde_checks(host,
incluir_averia=True)` (los serializa a la lista de etiquetas), usados ahora
en los tres sitios. De paso queda corregida una pequeña inconsistencia: los
checks de `EditDialog` no llevaban el estilo común (`_estilo_check_etiqueta`)
que sí tenían los otros dos sitios; ahora los tres se ven igual.

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

## 6. ~~Gráficas dibujadas a mano con boilerplate repetido~~ (RESUELTO)

`GraficoCircularTrabajos`, `GraficoBarrasRanking` y `GraficoBarrasMensual`
repetían el mismo boilerplate de constructor (`color_texto`, `color_fondo`,
`setMinimumHeight`, estado vacío "sin datos"). Corregido: se ha extraído
`_GraficoBase(QWidget)`, que centraliza `establecer_datos`, el `paintEvent`
común (fondo + estado vacío) y dos puntos de extensión, `_hay_datos()` y
`_texto_vacio()`, para las dos gráficas cuyo criterio de "vacío" no es
simplemente "lista sin elementos" (la circular filtra los valores a 0 al
guardar los datos; la mensual considera vacío que todos los meses sean 0).
Cada subclase se queda solo con su `_dibujar(painter)`, que es la única
parte que de verdad cambiaba entre las tres. Probado en modo offscreen
(`QT_QPA_PLATFORM=offscreen`) con datos y sin datos en las tres gráficas.
