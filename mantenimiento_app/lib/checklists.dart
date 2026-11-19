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

/// Listas de comprobación de preventivos y trabajos.
///
/// Las plantillas se descargan del PC (/api/checklists) y se guardan en el
/// móvil, así que se rellenan sin conexión. Lo rellenado viaja con el aviso o
/// el pendiente completado en su cola de envío (campos «checklist», el JSON
/// de los puntos, y «checklist_plantilla», el nombre de la plantilla).
library;

import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'i18n/strings.dart';

/// Clave donde se guarda la respuesta de /api/checklists.
const claveCacheChecklists = 'checklists_cache';

const _estados = ['ok', 'mal', 'na'];

/// Plantillas guardadas en el móvil: [{id, nombre, puntos: [...]}].
Future<List<Map<String, dynamic>>> plantillasChecklist() async {
  final prefs = await SharedPreferences.getInstance();
  final datos = prefs.getString(claveCacheChecklists);
  if (datos == null) return [];
  try {
    final d = json.decode(datos);
    final lista = d is Map ? (d['plantillas'] ?? []) : d;
    return List<Map<String, dynamic>>.from((lista as List).map((e) => Map<String, dynamic>.from(e)));
  } catch (_) {
    return [];
  }
}

Future<Map<String, dynamic>?> plantillaChecklist(int? id) async {
  if (id == null) return null;
  for (final p in await plantillasChecklist()) {
    if (p['id'] == id) return p;
  }
  return null;
}

double? _numero(dynamic v) {
  if (v == null) return null;
  if (v is num) return v.toDouble();
  final texto = v.toString().trim().replaceAll(',', '.');
  return texto.isEmpty ? null : double.tryParse(texto);
}

/// Fases de un punto de tipo «trifasica» (motor trifásico). Las tres lecturas
/// viajan juntas en «valor», separadas por «;» («12,1;12,3;12,0»), igual que
/// en el PC (mantpro/nucleo/checklists.py).
const fasesTrifasica = ['L1', 'L2', 'L3'];

/// Las tres lecturas (texto, '' si falta alguna) de un valor trifásico.
List<String> fasesDe(dynamic valor) {
  final partes = (valor ?? '').toString().split(';').map((e) => e.trim()).take(3).toList();
  while (partes.length < 3) {
    partes.add('');
  }
  return partes;
}

/// Al revés que fasesDe: «12,1;12,3;12,0», o '' si no hay ninguna.
String unirFases(List<String> lecturas) {
  final partes = lecturas.map((e) => e.trim().replaceAll(';', '')).toList();
  return partes.any((e) => e.isNotEmpty) ? partes.join(';') : '';
}

/// (porcentaje, índice de la fase que más se aparta de la media), o null si
/// falta alguna lectura. Mismo cálculo que en el PC.
(double, int)? desequilibrioFases(dynamic valor) {
  final nums = fasesDe(valor).map(_numero).toList();
  if (nums.any((n) => n == null)) return null;
  final media = (nums[0]! + nums[1]! + nums[2]!) / 3;
  if (media <= 0) return null;
  var mayor = 0;
  for (var k = 1; k < 3; k++) {
    if ((nums[k]! - media).abs() > (nums[mayor]! - media).abs()) mayor = k;
  }
  return (((nums[mayor]! - media).abs() / media * 1000).round() / 10, mayor);
}

/// «Desequilibrio 3,2 % · se aparta más L2» o '' si no se puede calcular.
String textoDesequilibrio(dynamic valor) {
  final d = desequilibrioFases(valor);
  if (d == null) return '';
  return t('chk_desequilibrio').replaceAll('{p}', _fmt(d.$1)).replaceAll('{fase}', fasesTrifasica[d.$2]);
}

/// Desequilibrio máximo (%) de un punto trifásico, o null si no tiene.
double? _deseqMax(Map<String, dynamic> punto) {
  final n = punto['tipo'] == 'trifasica' ? _numero(punto['desequilibrio_max']) : null;
  return (n != null && n > 0) ? n : null;
}

/// «desequilibrio máx. 5 %» o '' si el punto no tiene límite.
String textoDeseqMax(Map<String, dynamic> punto) {
  final limite = _deseqMax(punto);
  return limite == null ? '' : t('chk_deseq_max').replaceAll('{p}', _fmt(limite));
}

/// true si el desequilibrio entre fases pasa del máximo del punto.
bool desequilibrioExcesivo(Map<String, dynamic> punto, dynamic valor) {
  final limite = _deseqMax(punto);
  final d = limite == null ? null : desequilibrioFases(valor);
  return d != null && d.$1 > limite!;
}

bool _fueraUno(Map<String, dynamic> punto, String valor) {
  final n = _numero(valor);
  if (n == null) return false;
  final minimo = _numero(punto['minimo']), maximo = _numero(punto['maximo']);
  return (minimo != null && n < minimo) || (maximo != null && n > maximo);
}

/// true si una lectura se sale del mínimo o el máximo del punto (en un motor
/// trifásico, si se sale cualquiera de las tres fases).
bool fueraDeRango(Map<String, dynamic> punto, String valor) {
  if (punto['tipo'] == 'trifasica') {
    return fasesDe(valor).any((v) => _fueraUno(punto, v)) || desequilibrioExcesivo(punto, valor);
  }
  return _fueraUno(punto, valor);
}

String _fmt(double n) => n == n.roundToDouble() ? n.toInt().toString() : n.toString();

/// «6–8,5 bar», «≤ 95 °C»… o «» si el punto no tiene rango.
String textoRango(Map<String, dynamic> punto) {
  final minimo = _numero(punto['minimo']), maximo = _numero(punto['maximo']);
  final unidad = (punto['unidad'] ?? '').toString();
  String r;
  if (minimo != null && maximo != null) {
    r = '${_fmt(minimo)}–${_fmt(maximo)}';
  } else if (minimo != null) {
    r = '≥ ${_fmt(minimo)}';
  } else if (maximo != null) {
    r = '≤ ${_fmt(maximo)}';
  } else {
    return '';
  }
  return '$r $unidad'.trim();
}

/// {ok, mal, na, sin} de una lista rellenada.
/// Separador de zona o máquina: un título que agrupa los puntos de debajo; no
/// se marca ni cuenta (igual que en el PC, tipo «seccion»).
bool esSeparador(dynamic it) => it is Map && it['tipo'] == 'seccion';

Map<String, int> recuentoChecklist(List items) {
  final r = {'ok': 0, 'mal': 0, 'na': 0, 'sin': 0};
  for (final it in items.where((e) => !esSeparador(e))) {
    final e = (it is Map) ? it['estado'] : null;
    r[_estados.contains(e) ? e : 'sin'] = r[_estados.contains(e) ? e : 'sin']! + 1;
  }
  return r;
}

/// «3 bien · 1 mal» para el historial.
String resumenChecklist(List items) {
  final r = recuentoChecklist(items);
  final partes = <String>[];
  if (r['ok']! > 0) partes.add(t('chk_resumen_ok').replaceAll('{n}', '${r['ok']}'));
  if (r['mal']! > 0) partes.add(t('chk_resumen_mal').replaceAll('{n}', '${r['mal']}'));
  if (r['na']! > 0) partes.add(t('chk_resumen_na').replaceAll('{n}', '${r['na']}'));
  if (r['sin']! > 0) partes.add(t('chk_resumen_sin').replaceAll('{n}', '${r['sin']}'));
  return partes.join(' · ');
}

String _textoEstado(String estado) =>
    {'ok': t('chk_txt_ok'), 'mal': t('chk_txt_mal'), 'na': t('chk_txt_na')}[estado] ?? t('chk_txt_sin');

// ---------------------------------------------------------------- borradores
// Una lista larga se puede dejar a medias (fin del turno) y seguir otro día:
// lo apuntado se guarda en el móvil al momento, por aviso o pendiente, y se
// recupera al volver a abrirla. Solo vive en este móvil (no se sincroniza);
// se borra al guardar la lista completa o al «Empezar de nuevo».

const _claveBorradores = 'checklist_borradores';

/// Resumen de los borradores para las tarjetas: {clave: "12/30"}.
final ValueNotifier<Map<String, String>> borradoresChecklist = ValueNotifier({});

/// Clave del borrador de un aviso o un pendiente («aviso:<uuid o id>»).
String claveBorradorChecklist(String tipo, dynamic uuid, dynamic id) => '$tipo:${uuid ?? id}';

Future<Map<String, dynamic>> _leerBorradores() async {
  final prefs = await SharedPreferences.getInstance();
  try {
    final d = json.decode(prefs.getString(_claveBorradores) ?? '{}');
    return d is Map ? Map<String, dynamic>.from(d) : {};
  } catch (_) {
    return {};
  }
}

String _resumenBorrador(Map b) {
  final items = (b['items'] as List? ?? []).where((e) => !esSeparador(e)).toList();
  final hechos = items.where((e) => e is Map && _estados.contains(e['estado'])).length;
  return '$hechos/${items.length}';
}

Future<void> _escribirBorradores(Map<String, dynamic> todos) async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString(_claveBorradores, json.encode(todos));
  borradoresChecklist.value = {for (final e in todos.entries) if (e.value is Map) e.key: _resumenBorrador(e.value as Map)};
}

/// Carga el resumen de borradores (al arrancar la app).
Future<void> cargarBorradoresChecklist() async {
  final todos = await _leerBorradores();
  borradoresChecklist.value = {for (final e in todos.entries) if (e.value is Map) e.key: _resumenBorrador(e.value as Map)};
}

Future<void> guardarBorradorChecklist(String clave, String plantilla, List<Map<String, dynamic>> items) async {
  final todos = await _leerBorradores();
  final algo = items.any((e) => _estados.contains(e['estado']) || '${e['valor'] ?? ''}'.isNotEmpty || '${e['nota'] ?? ''}'.isNotEmpty);
  if (algo) {
    todos[clave] = {'plantilla': plantilla, 'fecha': DateTime.now().toIso8601String(), 'items': items};
  } else {
    todos.remove(clave);
  }
  await _escribirBorradores(todos);
}

Future<void> borrarBorradorChecklist(String clave) async {
  final todos = await _leerBorradores();
  if (todos.remove(clave) != null) await _escribirBorradores(todos);
}

/// Pasa lo apuntado del borrador a los puntos de la plantilla actual: punto a
/// punto, solo si coincide el texto y el tipo (por si la plantilla ha cambiado).
int _aplicarBorrador(List<Map<String, dynamic>> items, Map borrador) {
  final viejos = (borrador['items'] as List? ?? []).whereType<Map>().toList();
  // Por el identificador fijo del punto (punto_uid), aunque se haya renombrado o
  // movido en la plantilla; los borradores de antes, por posición y texto.
  final porUid = {for (final v in viejos) if (v['punto_uid'] != null) v['punto_uid']: v};
  var n = 0;
  for (var i = 0; i < items.length; i++) {
    Map? v = items[i]['punto_uid'] != null ? porUid[items[i]['punto_uid']] : null;
    if (v == null && i < viejos.length && viejos[i]['texto'] == items[i]['texto']) v = viejos[i];
    if (v == null || v['tipo'] != items[i]['tipo'] || esSeparador(items[i])) continue;
    items[i]['estado'] = _estados.contains(v['estado']) ? v['estado'] : null;
    items[i]['valor'] = (v['valor'] ?? '').toString();
    items[i]['nota'] = (v['nota'] ?? '').toString();
    n++;
  }
  return n;
}

/// «📝 12/30» en la tarjeta del aviso o pendiente con la lista a medias.
Widget marcaBorradorChecklist(String clave) => ValueListenableBuilder<Map<String, String>>(
      valueListenable: borradoresChecklist,
      builder: (_, mapa, __) => mapa[clave] == null
          ? const SizedBox.shrink()
          : Padding(padding: const EdgeInsets.only(left: 6), child: Tooltip(message: t('chk_borrador_tarjeta'),
              child: Text('📝 ${mapa[clave]}', style: const TextStyle(fontSize: 12, color: Colors.orange, fontWeight: FontWeight.bold)))),
    );

String _fechaBorrador(String? iso) {
  final f = DateTime.tryParse(iso ?? '');
  if (f == null) return '';
  String dd(int n) => n.toString().padLeft(2, '0');
  // Fecha corta como en el PC: AAAA/MM/DD en euskera, DD.MM.AAAA en alemán, DD/MM/AAAA en el resto.
  final fecha = switch (idiomaNotifier.value) {
    'eu' => '${f.year}/${dd(f.month)}/${dd(f.day)}',
    'de' => '${dd(f.day)}.${dd(f.month)}.${f.year}',
    _ => '${dd(f.day)}/${dd(f.month)}/${f.year}',
  };
  return '$fecha ${dd(f.hour)}:${dd(f.minute)}';
}

/// Al completar un aviso o un pendiente: si tiene lista, la pide rellenar.
/// Devuelve {} si no tiene (o la plantilla no está en el móvil), null si se
/// cancela, o {"plantilla": nombre, "items": [...]} con lo rellenado.
/// Con [claveBorrador], lo apuntado se guarda al momento y, si se deja a
/// medias, se ofrece seguir donde se quedó la próxima vez.
Future<Map<String, dynamic>?> rellenarChecklistSiHay(BuildContext context, int? checklistId, String titulo,
    {String? claveBorrador}) async {
  final plantilla = await plantillaChecklist(checklistId);
  if (plantilla == null || (plantilla['puntos'] as List? ?? []).isEmpty) return {};
  if (!context.mounted) return null;
  final items = (plantilla['puntos'] as List).map((p) => <String, dynamic>{
        ...Map<String, dynamic>.from(p), 'estado': null, 'valor': '', 'nota': ''}).toList();
  if (claveBorrador != null) {
    final borrador = (await _leerBorradores())[claveBorrador];
    if (borrador is Map && context.mounted) {
      final seguir = await showDialog<bool>(context: context, barrierDismissible: false, builder: (ctx) => AlertDialog(
        title: Text(t('title_chk_borrador')),
        content: Text(t('msg_chk_borrador')
            .replaceAll('{fecha}', _fechaBorrador(borrador['fecha']?.toString()))
            .replaceAll('{hechos}', _resumenBorrador(borrador))),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(t('btn_chk_empezar_nuevo'))),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, true), child: Text(t('btn_chk_continuar'))),
        ],
      ));
      if (seguir == true) {
        _aplicarBorrador(items, borrador);
      } else if (seguir == false) {
        await borrarBorradorChecklist(claveBorrador);
      }
      if (!context.mounted) return null;
    }
  }
  final nombre = plantilla['nombre'].toString();
  final resultado = await Navigator.push<List<Map<String, dynamic>>>(context, MaterialPageRoute(
      builder: (_) => PantallaChecklist(titulo: titulo, plantilla: nombre, items: items,
          alCambiar: claveBorrador == null ? null : (actual) => guardarBorradorChecklist(claveBorrador, nombre, actual))));
  if (resultado == null) return null;
  return {'plantilla': nombre, 'items': resultado};
}

/// Campos que se añaden al envío al PC (formulario) a partir de lo rellenado.
Map<String, String> camposChecklist(dynamic checklist) {
  if (checklist is! Map || (checklist['items'] as List? ?? []).isEmpty) return {};
  return {'checklist': json.encode(checklist['items']), 'checklist_plantilla': (checklist['plantilla'] ?? '').toString()};
}

/// Rellenar una lista (o verla, con [soloLectura]). Devuelve los puntos.
class PantallaChecklist extends StatefulWidget {
  final String titulo, plantilla;
  final List<Map<String, dynamic>> items;
  final bool soloLectura;
  /// Se llama con la lista tal como va cada vez que se apunta algo (borrador).
  final void Function(List<Map<String, dynamic>>)? alCambiar;
  const PantallaChecklist({super.key, required this.titulo, required this.plantilla, required this.items,
      this.soloLectura = false, this.alCambiar});
  @override
  State<PantallaChecklist> createState() => _PantallaChecklistState();
}

class _PantallaChecklistState extends State<PantallaChecklist> {
  late final List<Map<String, dynamic>> _items;
  late final List<TextEditingController> _valores, _notas;
  /// Los tres campos (L1, L2, L3) de cada punto; solo se usan en los trifásicos.
  late final List<List<TextEditingController>> _fases;
  /// Si cada punto tiene ahora su lectura fuera de rango: así se sabe si un «mal»
  /// lo puso la lectura (y al corregirla vuelve a «bien») o el técnico a propósito.
  late final List<bool> _fuera;

  @override
  void initState() {
    super.initState();
    _items = widget.items.map((e) => Map<String, dynamic>.from(e)).toList();
    _valores = _items.map((e) => TextEditingController(text: (e['valor'] ?? '').toString())).toList();
    _notas = _items.map((e) => TextEditingController(text: (e['nota'] ?? '').toString())).toList();
    _fuera = _items.map((e) => fueraDeRango(e, (e['valor'] ?? '').toString())).toList();
    _fases = _items.map((e) => fasesDe(e['tipo'] == 'trifasica' ? e['valor'] : '')
        .map((v) => TextEditingController(text: v)).toList()).toList();
  }

  Timer? _espera;

  /// Guarda el borrador (con un pequeño retraso mientras se escribe).
  void _avisarCambio() {
    if (widget.alCambiar == null || widget.soloLectura) return;
    _espera?.cancel();
    _espera = Timer(const Duration(milliseconds: 400), _guardarBorradorYa);
  }

  void _guardarBorradorYa() {
    _espera?.cancel();
    widget.alCambiar?.call(_resultado().map((e) => Map<String, dynamic>.from(e)).toList());
  }

  @override
  void setState(VoidCallback fn) {
    super.setState(fn);
    _avisarCambio();
  }

  @override
  void dispose() {
    if (_espera?.isActive ?? false) _guardarBorradorYa();   // lo último escrito antes de salir
    for (final c in [..._valores, ..._notas, for (final f in _fases) ...f]) {
      c.dispose();
    }
    super.dispose();
  }

  String _valorDe(int i) {
    switch (_items[i]['tipo']) {
      case 'lectura': return _valores[i].text.trim();
      case 'trifasica': return unirFases(_fases[i].map((c) => c.text).toList());
      default: return '';
    }
  }

  void _lecturaCambiada(int i, String texto) {
    setState(() {
      _items[i]['valor'] = _valorDe(i);
      if (_numero(texto) == null) return;   // vacío o aún no es un número
      // Fuera de rango: «mal». Dentro: «bien» si aún no tenía estado o si el «mal»
      // venía de una lectura fuera de rango que se acaba de corregir (un «mal»
      // puesto a mano con una lectura correcta se respeta).
      final fuera = fueraDeRango(_items[i], _items[i]['valor']);
      if (fuera) {
        _items[i]['estado'] = 'mal';
      } else if (_items[i]['estado'] == null || (_fuera[i] && _items[i]['estado'] == 'mal')) {
        _items[i]['estado'] = 'ok';
      }
      _fuera[i] = fuera;
    });
  }

  List<Map<String, dynamic>> _resultado() {
    for (var i = 0; i < _items.length; i++) {
      _items[i]['valor'] = _valorDe(i);
      _items[i]['nota'] = _notas[i].text.trim();
    }
    return _items;
  }

  Future<void> _guardar() async {
    final faltan = _items.where((e) => !esSeparador(e) && !_estados.contains(e['estado'])).length;
    if (faltan > 0) {
      final seguir = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
        title: Text(t('title_checklist')),
        content: Text(t('msg_chk_sin_marcar').replaceAll('{n}', '$faltan')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(t('btn_chk_volver'))),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, true), child: Text(t('btn_chk_completar_igual'))),
        ],
      ));
      if (seguir != true) return;
    }
    if (mounted) Navigator.pop(context, _resultado());
  }

  Widget _botonEstado(int i, String estado, IconData icono, Color color) {
    final elegido = _items[i]['estado'] == estado;
    return ChoiceChip(
      avatar: Icon(icono, size: 18, color: elegido ? Colors.white : color),
      label: Text(_textoEstado(estado)),
      selected: elegido,
      selectedColor: color,
      labelStyle: TextStyle(color: elegido ? Colors.white : null, fontSize: 13),
      showCheckmark: false,
      onSelected: widget.soloLectura ? null : (_) => setState(() => _items[i]['estado'] = elegido ? null : estado),
    );
  }

  @override
  Widget build(BuildContext context) {
    final hechos = _items.where((e) => _estados.contains(e['estado'])).length;
    final total = _items.where((e) => !esSeparador(e)).length;
    // Número de cada punto sin contar los separadores
    final numeros = <int>[];
    var n = 0;
    for (final it in _items) {
      numeros.add(esSeparador(it) ? 0 : ++n);
    }
    return Scaffold(
      appBar: AppBar(title: Text(widget.soloLectura ? t('title_checklist') : t('title_rellenar_checklist'))),
      body: ListView(padding: const EdgeInsets.all(12), children: [
        Text(widget.titulo, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 4),
        Text('☑️ ${widget.plantilla} · $hechos/$total', style: const TextStyle(color: Colors.blueGrey)),
        const SizedBox(height: 8),
        for (var i = 0; i < _items.length; i++) if (esSeparador(_items[i])) Container(
          margin: const EdgeInsets.only(top: 14, bottom: 4),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          decoration: BoxDecoration(color: Colors.blue.withOpacity(0.12), borderRadius: BorderRadius.circular(6),
              border: Border(left: BorderSide(color: Colors.blue.shade700, width: 4))),
          child: Text('${_items[i]['texto']}', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.blue.shade800)),
        ) else Card(
          margin: const EdgeInsets.symmetric(vertical: 5),
          child: Padding(padding: const EdgeInsets.all(10), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('${numeros[i]}. ${_items[i]['texto']}', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
            if (_items[i]['tipo'] == 'lectura') ...[
              const SizedBox(height: 6),
              Row(children: [
                SizedBox(width: 130, child: TextField(
                  controller: _valores[i],
                  readOnly: widget.soloLectura,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                  onChanged: (v) => _lecturaCambiada(i, v),
                  style: TextStyle(
                      color: fueraDeRango(_items[i], _valores[i].text) ? Colors.red : null,
                      fontWeight: fueraDeRango(_items[i], _valores[i].text) ? FontWeight.bold : null),
                  decoration: InputDecoration(isDense: true, border: const OutlineInputBorder(),
                      labelText: t('chk_col_lectura'), suffixText: (_items[i]['unidad'] ?? '').toString()),
                )),
                const SizedBox(width: 10),
                if (textoRango(_items[i]).isNotEmpty)
                  Flexible(child: Text('${t('chk_rango')}: ${textoRango(_items[i])}',
                      style: const TextStyle(fontSize: 12, color: Colors.blueGrey))),
              ]),
            ],
            if (_items[i]['tipo'] == 'trifasica') ...[
              const SizedBox(height: 6),
              Row(children: [
                for (var k = 0; k < 3; k++) ...[
                  if (k > 0) const SizedBox(width: 6),
                  Expanded(child: TextField(
                    controller: _fases[i][k],
                    readOnly: widget.soloLectura,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                    onChanged: (v) => _lecturaCambiada(i, v),
                    style: TextStyle(
                        color: _fueraUno(_items[i], _fases[i][k].text) ? Colors.red : null,
                        fontWeight: _fueraUno(_items[i], _fases[i][k].text) ? FontWeight.bold : null),
                    decoration: InputDecoration(isDense: true, border: const OutlineInputBorder(),
                        labelText: fasesTrifasica[k], suffixText: (_items[i]['unidad'] ?? '').toString()),
                  )),
                ],
              ]),
              if (textoRango(_items[i]).isNotEmpty || textoDeseqMax(_items[i]).isNotEmpty)
                Padding(padding: const EdgeInsets.only(top: 4), child: Text(
                    [if (textoRango(_items[i]).isNotEmpty) '${t('chk_rango')}: ${textoRango(_items[i])}',
                     if (textoDeseqMax(_items[i]).isNotEmpty) textoDeseqMax(_items[i])].join(' · '),
                    style: const TextStyle(fontSize: 12, color: Colors.blueGrey))),
              if (textoDesequilibrio(_valorDe(i)).isNotEmpty)
                Padding(padding: const EdgeInsets.only(top: 2), child: Text(textoDesequilibrio(_valorDe(i)),
                    style: TextStyle(fontSize: 12,
                        color: desequilibrioExcesivo(_items[i], _valorDe(i)) ? Colors.red : Colors.blueGrey,
                        fontWeight: desequilibrioExcesivo(_items[i], _valorDe(i)) ? FontWeight.bold : null))),
            ],
            const SizedBox(height: 6),
            Wrap(spacing: 6, runSpacing: 4, children: [
              _botonEstado(i, 'ok', Icons.check_circle, Colors.green),
              _botonEstado(i, 'mal', Icons.cancel, Colors.red),
              _botonEstado(i, 'na', Icons.remove_circle, Colors.grey),
            ]),
            if (!widget.soloLectura || _notas[i].text.isNotEmpty) ...[
              const SizedBox(height: 6),
              TextField(controller: _notas[i], readOnly: widget.soloLectura, onChanged: (_) => _avisarCambio(),
                  decoration: InputDecoration(isDense: true, hintText: t('chk_col_nota'), prefixIcon: const Icon(Icons.notes, size: 18))),
            ],
          ])),
        ),
        const SizedBox(height: 70),
      ]),
      floatingActionButton: widget.soloLectura ? null : Row(mainAxisAlignment: MainAxisAlignment.end, children: [
        FloatingActionButton.extended(
          heroTag: 'chk_todo_bien',
          backgroundColor: Colors.white,
          foregroundColor: Colors.green,
          icon: const Icon(Icons.done_all),
          label: Text(t('btn_chk_todo_bien_corto')),
          onPressed: () => setState(() {
            for (final it in _items.where((e) => !esSeparador(e))) {
              it['estado'] ??= 'ok';
            }
          }),
        ),
        const SizedBox(width: 10),
        FloatingActionButton.extended(
          heroTag: 'chk_guardar',
          backgroundColor: Colors.green,
          foregroundColor: Colors.white,
          icon: const Icon(Icons.save),
          label: Text(t('btn_chk_guardar')),
          onPressed: _guardar,
        ),
      ]),
    );
  }
}

/// Fila «☑️ plantilla · 3 bien · 1 mal» para las tarjetas del historial;
/// al pulsarla se ve la lista entera.
Widget filaChecklistHistorial(BuildContext context, Map<String, dynamic>? checklist, String titulo) {
  if (checklist == null || (checklist['items'] as List? ?? []).isEmpty) return const SizedBox.shrink();
  final items = List<Map<String, dynamic>>.from((checklist['items'] as List).map((e) => Map<String, dynamic>.from(e)));
  final hayMal = items.any((e) => e['estado'] == 'mal');
  return InkWell(
    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => PantallaChecklist(
        titulo: titulo, plantilla: (checklist['plantilla'] ?? '').toString(), items: items, soloLectura: true))),
    child: Padding(padding: const EdgeInsets.only(top: 3), child: Row(children: [
      Icon(hayMal ? Icons.fact_check : Icons.fact_check_outlined, size: 15, color: hayMal ? Colors.red : Colors.green),
      const SizedBox(width: 4),
      Flexible(child: Text('${checklist['plantilla']} · ${resumenChecklist(items)}',
          style: TextStyle(fontSize: 12, color: hayMal ? Colors.red : Colors.green, decoration: TextDecoration.underline))),
    ])),
  );
}

// ---------------------------------------------------------------- tiempo trabajado
// (se apunta después, sin cronómetro: igual que en el PC, ver mano_obra.py)

/// Minutos a partir de lo que se escriba: «1:30», «1,5» (horas), «2» (horas),
/// «90 min», «1 h 30». null si está vacío o no se entiende.
int? leerDuracion(String texto) {
  final t = texto.trim().toLowerCase().replaceAll(',', '.');
  if (t.isEmpty) return null;
  var m = RegExp(r'^(\d+):(\d{1,2})$').firstMatch(t);
  if (m != null) return int.parse(m.group(1)!) * 60 + int.parse(m.group(2)!);
  m = RegExp(r'^(\d+(?:\.\d+)?)\s*min(?:utos)?$').firstMatch(t);
  if (m != null) return double.parse(m.group(1)!).round();
  m = RegExp(r'^(\d+(?:\.\d+)?)\s*h(?:oras?)?\s*(?:(\d+)\s*(?:min(?:utos)?)?)?$').firstMatch(t);
  if (m != null) return (double.parse(m.group(1)!) * 60).round() + int.parse(m.group(2) ?? '0');
  final h = double.tryParse(t);
  return h == null ? null : (h * 60).round();
}

/// «1 h 30 min», «45 min».
String textoDuracion(int? minutos) {
  if (minutos == null || minutos <= 0) return '';
  final h = minutos ~/ 60, m = minutos % 60;
  if (h > 0 && m > 0) return '$h h $m min';
  return h > 0 ? '$h h' : '$m min';
}

/// «1:30», para volver a ponerlo en el campo.
String textoEntradaDuracion(int? minutos) =>
    (minutos == null || minutos <= 0) ? '' : '${minutos ~/ 60}:${(minutos % 60).toString().padLeft(2, '0')}';

/// Campo «Tiempo trabajado» + personas. Se apunta al volver de la avería.
class CampoTiempoTrabajo extends StatefulWidget {
  final TextEditingController controlador;
  final int personas;
  final ValueChanged<int> alCambiarPersonas;
  /// Nota que se muestra bajo el campo mientras está vacío (p. ej. «opcional»).
  final String? ayudaVacio;
  const CampoTiempoTrabajo({super.key, required this.controlador, required this.personas, required this.alCambiarPersonas, this.ayudaVacio});
  @override
  State<CampoTiempoTrabajo> createState() => _CampoTiempoTrabajoState();
}

class _CampoTiempoTrabajoState extends State<CampoTiempoTrabajo> {
  @override
  Widget build(BuildContext context) {
    final texto = widget.controlador.text.trim();
    final minutos = leerDuracion(texto);
    final malo = texto.isNotEmpty && minutos == null;
    return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Expanded(child: TextField(
        controller: widget.controlador,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        onChanged: (_) => setState(() {}),
        decoration: InputDecoration(
          labelText: t('lbl_tiempo_trabajado'),
          hintText: t('ph_tiempo_trabajado'),
          prefixIcon: const Icon(Icons.timer_outlined),
          helperText: malo ? t('msg_tiempo_no_valido') : (minutos != null ? textoDuracion(minutos) : (texto.isEmpty ? widget.ayudaVacio : null)),
          helperMaxLines: 2,
          helperStyle: TextStyle(color: malo ? Colors.red : null),
        ),
      )),
      const SizedBox(width: 8),
      Padding(padding: const EdgeInsets.only(top: 8), child: Row(mainAxisSize: MainAxisSize.min, children: [
        IconButton(icon: const Icon(Icons.remove_circle_outline), visualDensity: VisualDensity.compact,
            onPressed: widget.personas > 1 ? () => widget.alCambiarPersonas(widget.personas - 1) : null),
        Text('× ${widget.personas}', style: const TextStyle(fontSize: 16)),
        IconButton(icon: const Icon(Icons.add_circle_outline), visualDensity: VisualDensity.compact,
            onPressed: () => widget.alCambiarPersonas(widget.personas + 1)),
      ])),
    ]);
  }
}
