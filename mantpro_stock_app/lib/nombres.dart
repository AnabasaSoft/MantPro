// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// MantPro Stock - Gestión de almacén
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

/// Comparación de nombres para avisar de artículos repetidos sin querer.
///
/// Es exactamente el mismo cálculo que hace el PC en mantpro/nucleo/nombres.py:
/// si se cambia aquí, hay que cambiarlo allí.
library;

/// Parecido mínimo (0 a 1) para avisar. Con 0,82 «Extractor de finos» /
/// «Extracción de finos» (0,84) avisa, y «Grapa 22mm una pata» / «Grapa 22mm
/// dos patas» (0,80) no.
const double kUmbralParecido = 0.82;

const _conTilde = 'áàäâãåéèëêíìïîóòöôõúùüûñç';
const _sinTilde = 'aaaaaaeeeeiiiiooooouuuunc';

/// Minúsculas, sin tildes y con los espacios juntados.
String normalizarNombre(String? texto) {
  final b = StringBuffer();
  for (final r in (texto ?? '').toLowerCase().runes) {
    final c = String.fromCharCode(r);
    final i = _conTilde.indexOf(c);
    b.write(i >= 0 ? _sinTilde[i] : c);
  }
  return b.toString().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).join(' ');
}

/// Distancia de Levenshtein (nº de letras a cambiar, quitar o poner).
int _distancia(String a, String b) {
  var anterior = List<int>.generate(b.length + 1, (j) => j);
  for (var i = 1; i <= a.length; i++) {
    final actual = <int>[i];
    for (var j = 1; j <= b.length; j++) {
      final coste = a[i - 1] == b[j - 1] ? 0 : 1;
      final valores = [anterior[j] + 1, actual[j - 1] + 1, anterior[j - 1] + coste];
      actual.add(valores.reduce((x, y) => x < y ? x : y));
    }
    anterior = actual;
  }
  return anterior.last;
}

List<String> _numeros(String s) => RegExp(r'\d+').allMatches(s).map((m) => m.group(0)!).toList();

/// true si los dos nombres son iguales o muy parecidos. No cuenta como
/// parecido lo que solo cambia en los números («Grapa 8mm» / «Grapa 16mm»).
bool sonParecidos(String a, String b) {
  a = normalizarNombre(a);
  b = normalizarNombre(b);
  if (a.isEmpty || b.isEmpty) return false;
  if (a == b) return true;
  if (_numeros(a).join(',') != _numeros(b).join(',')) return false;
  final largo = a.length > b.length ? a.length : b.length;
  return 1 - _distancia(a, b) / largo >= kUmbralParecido;
}
