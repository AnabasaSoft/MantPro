// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// MantPro Operarios - Tablet de avisos de trabajos pendientes
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

// Comprobación LOCAL de contraseñas contra el hash que guarda el servidor
// («pbkdf2_sha256$iteraciones$salt_b64$hash_b64», el mismo formato que
// mantpro/nucleo/usuarios.py). La tablet no manda nunca la contraseña a
// ninguna parte: solo la compara con el hash descargado.
//
// PBKDF2-HMAC-SHA256 con 200 000 iteraciones son 400 000 compresiones de
// SHA-256. Para que tarde lo menos posible no se usa Hmac() en cada vuelta:
// se precalculan una sola vez los estados tras los bloques ipad y opad, y
// cada iteración son exactamente dos compresiones sobre listas de enteros.
import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';

const int _mascara = 0xFFFFFFFF;

const List<int> _k = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

const List<int> _h0 = [
  0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
];

final Uint32List _kTabla = Uint32List.fromList(_k);

int _rotd(int x, int n) => ((x >> n) | (x << (32 - n))) & _mascara;

/// Una compresión de SHA-256: actualiza [h] (8 palabras) con el bloque [b] (16 palabras); [w] es memoria de trabajo (64).
void _comprimir(Uint32List h, Uint32List b, Uint32List w) {
  for (var i = 0; i < 16; i++) {
    w[i] = b[i];
  }
  for (var i = 16; i < 64; i++) {
    final x = w[i - 15], y = w[i - 2];
    final s0 = _rotd(x, 7) ^ _rotd(x, 18) ^ (x >> 3);
    final s1 = _rotd(y, 17) ^ _rotd(y, 19) ^ (y >> 10);
    w[i] = (w[i - 16] + s0 + w[i - 7] + s1) & _mascara;
  }
  var a = h[0], bb = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
  for (var i = 0; i < 64; i++) {
    final s1 = _rotd(e, 6) ^ _rotd(e, 11) ^ _rotd(e, 25);
    final ch = (e & f) ^ ((~e & _mascara) & g);
    final t1 = (hh + s1 + ch + _kTabla[i] + w[i]) & _mascara;
    final s0 = _rotd(a, 2) ^ _rotd(a, 13) ^ _rotd(a, 22);
    final maj = (a & bb) ^ (a & c) ^ (bb & c);
    final t2 = (s0 + maj) & _mascara;
    hh = g;
    g = f;
    f = e;
    e = (d + t1) & _mascara;
    d = c;
    c = bb;
    bb = a;
    a = (t1 + t2) & _mascara;
  }
  h[0] = (h[0] + a) & _mascara;
  h[1] = (h[1] + bb) & _mascara;
  h[2] = (h[2] + c) & _mascara;
  h[3] = (h[3] + d) & _mascara;
  h[4] = (h[4] + e) & _mascara;
  h[5] = (h[5] + f) & _mascara;
  h[6] = (h[6] + g) & _mascara;
  h[7] = (h[7] + hh) & _mascara;
}

/// Bloque de 64 bytes (16 palabras big-endian) a partir de [bytes] (hasta 64).
Uint32List _bloqueDeBytes(List<int> bytes) {
  final b = Uint32List(16);
  for (var i = 0; i < bytes.length; i++) {
    b[i >> 2] |= bytes[i] << (24 - 8 * (i & 3));
  }
  return b;
}

/// PBKDF2-HMAC-SHA256 de [contrasena] con [sal], [iteraciones] vueltas y [longitud] bytes de salida.
Uint8List pbkdf2Sha256(List<int> contrasena, List<int> sal, int iteraciones, int longitud) {
  // Clave del HMAC: si pasa de 64 bytes se sustituye por su SHA-256; se rellena con ceros hasta 64.
  var clave = contrasena;
  if (clave.length > 64) clave = sha256.convert(clave).bytes;
  final ipad = List<int>.filled(64, 0x36), opad = List<int>.filled(64, 0x5c);
  for (var i = 0; i < clave.length; i++) {
    ipad[i] ^= clave[i];
    opad[i] ^= clave[i];
  }
  final w = Uint32List(64);
  final estadoInterior = Uint32List.fromList(_h0);
  _comprimir(estadoInterior, _bloqueDeBytes(ipad), w);
  final estadoExterior = Uint32List.fromList(_h0);
  _comprimir(estadoExterior, _bloqueDeBytes(opad), w);

  final hmacGeneral = Hmac(sha256, clave);
  final salida = Uint8List(((longitud + 31) ~/ 32) * 32);
  final bloqueInt = Uint32List(16), bloqueExt = Uint32List(16);
  final hi = Uint32List(8), he = Uint32List(8);
  for (var n = 1; n <= (longitud + 31) ~/ 32; n++) {
    // U1 = HMAC(sal || INT_32_BE(n)); el resto de U se calcula con el atajo de dos compresiones.
    final u1 = hmacGeneral.convert([...sal, n >> 24 & 0xff, n >> 16 & 0xff, n >> 8 & 0xff, n & 0xff]).bytes;
    final u = Uint32List(8), t = Uint32List(8);
    for (var i = 0; i < 8; i++) {
      u[i] = (u1[4 * i] << 24) | (u1[4 * i + 1] << 16) | (u1[4 * i + 2] << 8) | u1[4 * i + 3];
      t[i] = u[i];
    }
    // Relleno fijo de un mensaje de 32 bytes tras el bloque de clave: 0x80, ceros y longitud (64 + 32) * 8 bits.
    bloqueInt[8] = 0x80000000;
    bloqueExt[8] = 0x80000000;
    bloqueInt[15] = 768;
    bloqueExt[15] = 768;
    for (var it = 1; it < iteraciones; it++) {
      for (var i = 0; i < 8; i++) {
        bloqueInt[i] = u[i];
        hi[i] = estadoInterior[i];
      }
      _comprimir(hi, bloqueInt, w);
      for (var i = 0; i < 8; i++) {
        bloqueExt[i] = hi[i];
        he[i] = estadoExterior[i];
      }
      _comprimir(he, bloqueExt, w);
      for (var i = 0; i < 8; i++) {
        u[i] = he[i];
        t[i] ^= he[i];
      }
    }
    for (var i = 0; i < 8; i++) {
      final p = (n - 1) * 32 + 4 * i;
      salida[p] = t[i] >> 24 & 0xff;
      salida[p + 1] = t[i] >> 16 & 0xff;
      salida[p + 2] = t[i] >> 8 & 0xff;
      salida[p + 3] = t[i] & 0xff;
    }
  }
  return Uint8List.sublistView(salida, 0, longitud);
}

/// true si [contrasena] corresponde al hash [almacenado] («pbkdf2_sha256$iter$salt_b64$hash_b64»).
/// Cualquier error (formato roto, otro algoritmo, base64 inválido...) da false.
bool verificarContrasena(String contrasena, String almacenado) {
  try {
    final partes = almacenado.split(r'$');
    if (partes.length != 4 || partes[0] != 'pbkdf2_sha256') return false;
    final iteraciones = int.parse(partes[1]);
    if (iteraciones < 1 || iteraciones > 2000000) return false;
    final sal = base64.decode(partes[2]);
    final esperado = base64.decode(partes[3]);
    if (esperado.isEmpty) return false;
    final obtenido = pbkdf2Sha256(utf8.encode(contrasena), sal, iteraciones, esperado.length);
    // Comparación en tiempo constante
    var diferencia = obtenido.length ^ esperado.length;
    for (var i = 0; i < esperado.length; i++) {
      diferencia |= obtenido[i] ^ esperado[i];
    }
    return diferencia == 0;
  } catch (_) {
    return false;
  }
}

/// Función de nivel superior para poder ejecutarla en un isolate con compute().
bool _verificarEnIsolate(List<String> datos) => verificarContrasena(datos[0], datos[1]);

/// Comprueba la contraseña en un isolate (la interfaz no se queda parada). Si el servidor avisa de que
/// la clave de serie sigue sin cambiar ([claveSerieBloqueada]), la contraseña «admin» es siempre incorrecta.
Future<bool> comprobarContrasena(String contrasena, String almacenado, {bool claveSerieBloqueada = false}) {
  if (claveSerieBloqueada && contrasena == 'admin') return Future.value(false);
  return compute(_verificarEnIsolate, [contrasena, almacenado]);
}

/// Límite de intentos fallidos seguidos: a los [maximoFallos] la comprobación se bloquea [bloqueo]
/// segundos (con cuenta atrás) y un acierto pone los fallos a cero.
class LimiteIntentos extends ChangeNotifier {
  static const int maximoFallos = 5;
  static const int segundosBloqueo = 30;

  int fallos = 0;
  DateTime? _hasta;
  Timer? _reloj;

  /// Reloj sustituible en las pruebas.
  DateTime Function() ahora = DateTime.now;

  bool get bloqueado => segundosRestantes > 0;

  int get segundosRestantes {
    final h = _hasta;
    if (h == null) return 0;
    final s = (h.difference(ahora()).inMilliseconds / 1000).ceil();
    return s > 0 ? s : 0;
  }

  void registrarAcierto() {
    fallos = 0;
    notifyListeners();
  }

  void registrarFallo() {
    fallos++;
    if (fallos >= maximoFallos) {
      fallos = 0;
      _hasta = ahora().add(const Duration(seconds: segundosBloqueo));
      _reloj?.cancel();
      _reloj = Timer.periodic(const Duration(seconds: 1), (_) {
        if (!bloqueado) {
          _reloj?.cancel();
          _reloj = null;
        }
        notifyListeners();
      });
    }
    notifyListeners();
  }

  @override
  void dispose() {
    _reloj?.cancel();
    super.dispose();
  }
}
