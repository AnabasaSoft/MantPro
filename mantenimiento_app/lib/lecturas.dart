// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// MantPro - Sistema de Mantenimiento Preventivo
// Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft) <anabasasoft@gmail.com>
// https://github.com/AnabasaSoft/MantPro
//
// Este programa es software libre: puedes redistribuirlo y/o modificarlo bajo
// los términos de la Licencia Pública General Affero de GNU publicada por la
// Free Software Foundation, ya sea la versión 3 de la Licencia o (a tu
// elección) cualquier versión posterior.
//
// Este programa se distribuye con la esperanza de que sea útil, pero SIN
// NINGUNA GARANTÍA; ni siquiera la garantía implícita de COMERCIABILIDAD o
// IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Consulta la Licencia Pública
// General Affero de GNU para más detalles.
//
// Deberías haber recibido una copia de la Licencia Pública General Affero de
// GNU junto con este programa. Si no, consulta <https://www.gnu.org/licenses/>.

/// Evolución de las lecturas de las listas de comprobación (resistencia de
/// tierra, aislamiento, motores trifásicos…) en la ficha de la máquina,
/// 100 % sin conexión:
///
/// - Llegan con las máquinas (/api/maquinas, campo «lecturas»: cada máquina
///   solo con las suyas y las últimas de cada punto; ver
///   checklists.lecturas_por_maquina en el PC) y se guardan con ellas.
/// - Aquí se juntan las de la máquina y sus submáquinas por la «clave» del
///   punto, con la misma regla que el diálogo «📈 Lecturas» del PC.
library;

import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'i18n/strings.dart';
import 'checklists.dart' show textoRango, fasesTrifasica;
import 'contadores.dart' show cifraLectura;

/// Ids de la máquina y de todas sus submáquinas (a cualquier profundidad).
List<int> idsConSubmaquinas(List<Map<String, dynamic>> planas, int maquinaId) {
  final hijos = <dynamic, List<int>>{};
  for (final m in planas) {
    if (m['id'] is int) hijos.putIfAbsent(m['padre_id'], () => []).add(m['id'] as int);
  }
  final resultado = <int>[];
  void anadir(int id) {
    if (resultado.contains(id) || resultado.length > 5000) return;
    resultado.add(id);
    for (final h in hijos[id] ?? const <int>[]) {
      anadir(h);
    }
  }
  anadir(maquinaId);
  return resultado;
}

/// Puntos con lecturas de esas máquinas, juntados por su clave, con las
/// lecturas de la más antigua a la más reciente y el rango, texto y unidad de
/// la más reciente (como en el PC). Ordenados por texto.
List<Map<String, dynamic>> evolucionLecturas(List<Map<String, dynamic>> planas, List<int> ids) {
  final porId = {for (final m in planas) m['id']: m};
  final puntos = <String, Map<String, dynamic>>{};
  for (final id in ids) {
    for (final p in (porId[id]?['lecturas'] as List?) ?? const []) {
      if (p is! Map) continue;
      final clave = '${p['clave'] ?? '${p['texto']}|${p['unidad']}|${p['tipo']}'}';
      final junto = puntos.putIfAbsent(clave, () => {'clave': clave, 'tipo': p['tipo'], 'lecturas': <Map<String, dynamic>>[], '_fecha': ''});
      final lecturas = [for (final l in (p['lecturas'] as List?) ?? const []) if (l is Map) Map<String, dynamic>.from(l)..['maquina_id'] = id];
      (junto['lecturas'] as List<Map<String, dynamic>>).addAll(lecturas);
      // El texto, la unidad y el rango, los de la máquina con la lectura más reciente
      final ultima = lecturas.isEmpty ? '' : '${lecturas.last['fecha'] ?? ''}';
      if (ultima.compareTo(junto['_fecha'] as String) >= 0) {
        junto['_fecha'] = ultima;
        for (final k in ['texto', 'unidad', 'minimo', 'maximo', 'desequilibrio_max']) {
          junto[k] = p[k];
        }
      }
    }
  }
  final lista = puntos.values.where((p) => (p['lecturas'] as List).isNotEmpty).toList();
  for (final p in lista) {
    (p['lecturas'] as List<Map<String, dynamic>>).sort((a, b) => '${a['fecha']}'.compareTo('${b['fecha']}'));
    p.remove('_fecha');
  }
  lista.sort((a, b) => '${a['texto']}'.toLowerCase().compareTo('${b['texto']}'.toLowerCase()));
  return lista;
}

/// ¿Tiene la máquina (o alguna submáquina) lecturas guardadas en el móvil?
bool hayLecturas(List<Map<String, dynamic>> planas, int maquinaId) =>
    evolucionLecturas(planas, idsConSubmaquinas(planas, maquinaId)).isNotEmpty;

/// Fecha corta en el orden de cada idioma (igual que el PC):
/// AAAA/MM/DD en euskera, DD.MM.AAAA en alemán y DD/MM/AAAA en el resto.
String fechaCortaIdioma(String? iso) {
  final s = (iso ?? '');
  if (s.length < 10) return s;
  final a = s.substring(0, 4), m = s.substring(5, 7), d = s.substring(8, 10);
  switch (idiomaNotifier.value) {
    case 'eu': return '$a/$m/$d';
    case 'de': return '$d.$m.$a';
    default: return '$d/$m/$a';
  }
}

String _conUnidad(dynamic v, String unidad) {
  final n = v is num ? v : null;
  if (n == null) return '—';
  return unidad.isEmpty ? cifraLectura(n) : '${cifraLectura(n)} $unidad';
}

/// Valor de una lectura para mostrarla: el número con su unidad, las tres
/// fases de un motor trifásico, o el texto tal cual si no es un número.
String textoValorLectura(Map<String, dynamic> l, String unidad, String tipo) {
  if (tipo == 'trifasica') {
    final valores = (l['valores'] as List?) ?? const [];
    final partes = [for (var i = 0; i < 3; i++) '${fasesTrifasica[i]} ${i < valores.length && valores[i] is num ? cifraLectura(valores[i] as num) : '-'}'];
    return '${partes.join(' · ')}${unidad.isEmpty ? '' : ' $unidad'}';
  }
  if (l['valor'] is num) return _conUnidad(l['valor'], unidad);
  return '${l['valor_texto'] ?? ''}';
}

/// «Desequilibrio 3,2 % · se aparta más L2» de una lectura trifásica, o ''.
String textoDesequilibrioLectura(Map<String, dynamic> l) {
  final d = l['desequilibrio'];
  final f = l['fase_desviada'];
  if (d is! num || f is! int || f < 0 || f > 2) return '';
  return t('chk_desequilibrio').replaceAll('{p}', cifraLectura(d)).replaceAll('{fase}', fasesTrifasica[f]);
}

/// Pantalla «📈 Lecturas» de una máquina (y sus submáquinas).
class PantallaLecturas extends StatefulWidget {
  final int maquinaId;
  final List<Map<String, dynamic>> planas;
  const PantallaLecturas({super.key, required this.maquinaId, required this.planas});

  @override
  State<PantallaLecturas> createState() => _PantallaLecturasState();
}

class _PantallaLecturasState extends State<PantallaLecturas> {
  int? _elegida;   // null: la máquina con todas sus submáquinas

  String _nombre(int id) =>
      '${widget.planas.firstWhere((m) => m['id'] == id, orElse: () => {'nombre': ''})['nombre'] ?? ''}';

  @override
  Widget build(BuildContext context) {
    final todas = idsConSubmaquinas(widget.planas, widget.maquinaId);
    final ids = _elegida == null ? todas : [_elegida!];
    final puntos = evolucionLecturas(widget.planas, ids);
    final variasMaquinas = todas.length > 1;
    return Scaffold(
      appBar: AppBar(title: Text(t('tit_lecturas_maquina').replaceAll('{maquina}', _nombre(widget.maquinaId)))),
      body: ListView(padding: const EdgeInsets.all(12), children: [
        if (variasMaquinas)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: DropdownButtonFormField<int?>(
              initialValue: _elegida,
              isExpanded: true,
              decoration: InputDecoration(labelText: t('lbl_lect_maquina'), isDense: true),
              items: [
                DropdownMenuItem<int?>(value: null, child: Text(t('lbl_lect_todas'))),
                for (final id in todas) DropdownMenuItem<int?>(value: id, child: Text(_nombre(id), overflow: TextOverflow.ellipsis)),
              ],
              onChanged: (v) => setState(() => _elegida = v),
            ),
          ),
        if (puntos.isEmpty)
          Padding(padding: const EdgeInsets.symmetric(vertical: 24), child: Text(t('msg_lect_sin_lecturas_movil'))),
        for (final p in puntos) _TarjetaPunto(punto: p, nombreMaquina: variasMaquinas && _elegida == null ? _nombre : null),
        Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Text(t('lbl_lect_datos_sincro'), style: Theme.of(context).textTheme.bodySmall),
        ),
      ]),
    );
  }
}

class _TarjetaPunto extends StatelessWidget {
  final Map<String, dynamic> punto;
  final String Function(int)? nombreMaquina;   // con submáquinas: de cuál es cada lectura
  const _TarjetaPunto({required this.punto, this.nombreMaquina});

  @override
  Widget build(BuildContext context) {
    final lecturas = punto['lecturas'] as List<Map<String, dynamic>>;
    final unidad = '${punto['unidad'] ?? ''}';
    final tipo = '${punto['tipo'] ?? 'lectura'}';
    final rango = textoRango({'minimo': punto['minimo'], 'maximo': punto['maximo'], 'unidad': unidad});
    final fuera = lecturas.where((l) => l['fuera'] == true).length;
    final ultima = lecturas.last;
    final rojo = Theme.of(context).colorScheme.error;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('${punto['texto'] ?? ''}${unidad.isEmpty ? '' : ' ($unidad)'}', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 4),
          Text('${t('lbl_lect_rango')}: ${rango.isEmpty ? t('lbl_lect_sin_rango') : rango}'),
          Text(t('lbl_lect_resumen_movil').replaceAll('{n}', '${lecturas.length}').replaceAll('{fuera}', '$fuera'),
              style: TextStyle(color: fuera > 0 ? rojo : null)),
          Text.rich(TextSpan(children: [
            TextSpan(text: '${t('lbl_lect_ultima')}: '),
            TextSpan(text: textoValorLectura(ultima, unidad, tipo),
                style: TextStyle(fontWeight: FontWeight.bold, color: ultima['fuera'] == true ? rojo : Colors.green)),
            TextSpan(text: ' (${fechaCortaIdioma('${ultima['fecha']}')})'),
          ])),
          const SizedBox(height: 8),
          SizedBox(height: 170, width: double.infinity, child: GraficoLecturas(punto: punto)),
          ExpansionTile(
            tilePadding: EdgeInsets.zero,
            title: Text(t('lbl_lect_ver_lecturas').replaceAll('{n}', '${lecturas.length}')),
            children: [
              for (final l in lecturas.reversed)
                ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(l['fuera'] == true ? Icons.warning_amber_rounded : Icons.check_circle_outline,
                      color: l['fuera'] == true ? rojo : Colors.green),
                  title: Text('${fechaCortaIdioma('${l['fecha']}')} · ${textoValorLectura(l, unidad, tipo)}',
                      style: TextStyle(color: l['fuera'] == true ? rojo : null)),
                  subtitle: Text([
                    if (l['fuera'] == true) t('lbl_lect_fuera'),
                    if (tipo == 'trifasica' && textoDesequilibrioLectura(l).isNotEmpty) textoDesequilibrioLectura(l),
                    if (nombreMaquina != null && l['maquina_id'] is int) nombreMaquina!(l['maquina_id'] as int),
                    if ('${l['tecnico'] ?? ''}'.isNotEmpty) '${l['tecnico']}',
                    if ('${l['nota'] ?? ''}'.isNotEmpty) '«${l['nota']}»',
                  ].join(' · ')),
                ),
            ],
          ),
        ]),
      ),
    );
  }
}

/// Gráfico de la evolución de un punto: la banda del rango correcto en verde,
/// la línea de las lecturas (tres en un motor trifásico, una por fase) y los
/// puntos fuera de rango en rojo. Eje horizontal por fecha.
class GraficoLecturas extends StatelessWidget {
  final Map<String, dynamic> punto;
  const GraficoLecturas({super.key, required this.punto});

  @override
  Widget build(BuildContext context) {
    final esquema = Theme.of(context).colorScheme;
    return CustomPaint(painter: _PintorLecturas(
      punto: punto,
      colorTexto: esquema.onSurface,
      colorLinea: esquema.primary,
      colorError: esquema.error,
    ));
  }
}

class _PintorLecturas extends CustomPainter {
  final Map<String, dynamic> punto;
  final Color colorTexto, colorLinea, colorError;
  _PintorLecturas({required this.punto, required this.colorTexto, required this.colorLinea, required this.colorError});

  static const _coloresFases = [Color(0xFF1E88E5), Color(0xFFFB8C00), Color(0xFF8E24AA)];

  double? _num(dynamic v) => v is num ? v.toDouble() : null;

  /// Series a dibujar: una (el valor) o tres (las fases de un motor trifásico).
  List<List<double?>> _series(List<Map<String, dynamic>> lecturas) {
    if (punto['tipo'] == 'trifasica') {
      return [
        for (var f = 0; f < 3; f++)
          [for (final l in lecturas) (l['valores'] is List && (l['valores'] as List).length > f) ? _num((l['valores'] as List)[f]) : null]
      ];
    }
    return [[for (final l in lecturas) _num(l['valor'])]];
  }

  void _texto(Canvas canvas, String s, Offset pos, {bool derecha = false, bool centro = false}) {
    final tp = TextPainter(text: TextSpan(text: s, style: TextStyle(color: colorTexto.withValues(alpha: 0.7), fontSize: 10)),
        textDirection: TextDirection.ltr)..layout();
    var x = pos.dx;
    if (derecha) x -= tp.width;
    if (centro) x -= tp.width / 2;
    tp.paint(canvas, Offset(x, pos.dy - tp.height / 2));
  }

  @override
  void paint(Canvas canvas, Size size) {
    final lecturas = (punto['lecturas'] as List).cast<Map<String, dynamic>>();
    final series = _series(lecturas);
    final valores = [for (final s in series) ...s.whereType<double>()];
    if (valores.isEmpty) return;
    final minimo = _num(punto['minimo']), maximo = _num(punto['maximo']);
    final conLimites = [...valores, if (minimo != null) minimo, if (maximo != null) maximo];
    var bajo = conLimites.reduce(math.min);
    var alto = conLimites.reduce(math.max);
    if (alto - bajo < 1e-9) { bajo -= 1; alto += 1; }
    final margen = (alto - bajo) * 0.1;
    bajo -= margen; alto += margen;

    const izq = 40.0, abajo = 16.0, arriba = 6.0, der = 8.0;
    final ancho = size.width - izq - der, altoG = size.height - abajo - arriba;
    double y(double v) => arriba + (alto - v) / (alto - bajo) * altoG;

    // Eje horizontal por fecha (si todas son del mismo día, repartidas)
    final dias = [for (final l in lecturas) DateTime.tryParse('${l['fecha']}')?.millisecondsSinceEpoch.toDouble()];
    final conocidos = dias.whereType<double>().toList();
    final d0 = conocidos.isEmpty ? 0.0 : conocidos.reduce(math.min), d1 = conocidos.isEmpty ? 0.0 : conocidos.reduce(math.max);
    double x(int i) {
      if (lecturas.length == 1) return izq + ancho / 2;
      final d = dias[i];
      if (d == null || d1 - d0 < 1) return izq + ancho * i / (lecturas.length - 1);
      return izq + ancho * (d - d0) / (d1 - d0);
    }

    // Banda del rango correcto
    if (minimo != null || maximo != null) {
      final yArriba = maximo != null ? y(maximo) : arriba, yAbajo = minimo != null ? y(minimo) : arriba + altoG;
      canvas.drawRect(Rect.fromLTRB(izq, yArriba, izq + ancho, yAbajo), Paint()..color = Colors.green.withValues(alpha: 0.12));
      final borde = Paint()..color = Colors.green.withValues(alpha: 0.6)..strokeWidth = 1;
      if (maximo != null) canvas.drawLine(Offset(izq, yArriba), Offset(izq + ancho, yArriba), borde);
      if (minimo != null) canvas.drawLine(Offset(izq, yAbajo), Offset(izq + ancho, yAbajo), borde);
    }

    // Ejes y etiquetas
    final eje = Paint()..color = colorTexto.withValues(alpha: 0.3)..strokeWidth = 1;
    canvas.drawLine(Offset(izq, arriba), Offset(izq, arriba + altoG), eje);
    canvas.drawLine(Offset(izq, arriba + altoG), Offset(izq + ancho, arriba + altoG), eje);
    _texto(canvas, cifraLectura(alto - margen), Offset(izq - 4, y(alto - margen)), derecha: true);
    _texto(canvas, cifraLectura(bajo + margen), Offset(izq - 4, y(bajo + margen)), derecha: true);
    final fechaIni = fechaCortaIdioma('${lecturas.first['fecha']}'), fechaFin = fechaCortaIdioma('${lecturas.last['fecha']}');
    if (lecturas.length == 1) {
      _texto(canvas, fechaIni, Offset(izq + ancho / 2, size.height - 6), centro: true);
    } else {
      _texto(canvas, fechaIni, Offset(izq, size.height - 6));
      if (fechaFin != fechaIni) _texto(canvas, fechaFin, Offset(izq + ancho, size.height - 6), derecha: true);
    }

    // Líneas y puntos
    for (var s = 0; s < series.length; s++) {
      final color = series.length > 1 ? _coloresFases[s] : colorLinea;
      final linea = Paint()..color = color..strokeWidth = 2..style = PaintingStyle.stroke;
      final camino = Path();
      var empezado = false;
      for (var i = 0; i < lecturas.length; i++) {
        final v = series[s][i];
        if (v == null) continue;
        final o = Offset(x(i), y(v));
        if (!empezado) { camino.moveTo(o.dx, o.dy); empezado = true; } else { camino.lineTo(o.dx, o.dy); }
      }
      canvas.drawPath(camino, linea);
      for (var i = 0; i < lecturas.length; i++) {
        final v = series[s][i];
        if (v == null) continue;
        final fueraUno = (minimo != null && v < minimo) || (maximo != null && v > maximo);
        canvas.drawCircle(Offset(x(i), y(v)), fueraUno ? 4 : 3, Paint()..color = fueraUno ? colorError : color);
      }
    }
    // Leyenda de las fases
    if (series.length > 1) {
      for (var f = 0; f < 3; f++) {
        final px = izq + 8 + f * 34.0;
        canvas.drawCircle(Offset(px, arriba + 6), 3, Paint()..color = _coloresFases[f]);
        _texto(canvas, fasesTrifasica[f], Offset(px + 6, arriba + 6));
      }
    }
  }

  @override
  bool shouldRepaint(covariant _PintorLecturas old) => old.punto != punto || old.colorTexto != colorTexto;
}
