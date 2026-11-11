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

/// Las dos rutas del móvil: el PC (WiFi) y MantPro Cloud (internet).
///
/// El QR del PC puede llevar, además de la dirección del PC, el dominio de la nube y la empresa
/// (`&n=dominio&e=uuid`). El móvil guarda las dos rutas y usa UNA a la vez: la «activa», que se
/// escribe en `pc_ip_url`, la misma clave de siempre. Así el resto de la app, que construye todas
/// las direcciones como `$esquemaPC://$ip/api/...`, no cambia: la ruta de la nube es otra cadena
/// `ip` (`mantpro-cloud.com/m/<empresa>`) con su propio camino.
///
/// Reglas (decididas con el usuario):
///   * Se prefiere el PC: si responde a una sonda rápida (2 s) se usa; si no, la nube.
///   * Si la ruta activa falla (red, 5xx, licencia de la nube caducada o suspendida) se vuelve a
///     decidir sin que el técnico haga nada. Con la nube activa se vuelve a probar el PC cada minuto.
///   * Sin ruta de nube (QR antiguo o PC sin sesión de nube) NADA de esto se aplica: la app se
///     comporta exactamente como siempre.
///   * Un 401 de la nube en los 15 minutos siguientes a entrar con el PC no cierra la sesión: la
///     nube recibe las sesiones del PC con un retraso de hasta 10 minutos.
///
/// Todo es local (SharedPreferences): sin conexión la app sigue funcionando con sus colas.
library;

import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'conexion_segura.dart';

class RutasServidor {
  RutasServidor._();

  /// Clave de SharedPreferences con la ruta activa (la que lee el resto de la app).
  static const claveActiva = 'pc_ip_url';
  static const _clavePc = 'ruta_pc';
  static const _claveNube = 'ruta_nube';
  static const _claveInicioSesion = 'ruta_inicio_sesion';
  static const _claveInicioEnNube = 'ruta_inicio_en_nube';

  static const graciaSesion = Duration(minutes: 15);
  static const esperaSondaPc = Duration(seconds: 2);
  static const esperaSondaNube = Duration(seconds: 10);   // la primera petición del día arranca el trabajador de la empresa
  static const volverAlPcCada = Duration(seconds: 60);
  static const minimoEntreFallos = Duration(seconds: 5);
  static const esperaTrasFallarTodo = Duration(seconds: 20);

  /// true mientras la ruta activa es la de la nube (para el indicador de la pantalla y la notificación).
  static final ValueNotifier<bool> enNube = ValueNotifier(false);

  /// Sonda: ¿responde [ruta] con [esquema]? Cambia en las pruebas.
  @visibleForTesting
  static Future<bool> Function(String esquema, String ruta, Duration limite) sonda = _sondaHttp;

  /// Reloj. Cambia en las pruebas.
  @visibleForTesting
  static DateTime Function() ahora = DateTime.now;

  static DateTime? _ultimoSondeoPc;
  static DateTime? _ultimoFallo;
  static DateTime? _noAntesDe;
  static Future<void>? _resolviendo;

  /// Deja el estado como recién arrancada la app (las pruebas lo necesitan entre un caso y otro).
  @visibleForTesting
  static void reiniciarParaPruebas() {
    sonda = _sondaHttp;
    ahora = DateTime.now;
    _ultimoSondeoPc = null;
    _ultimoFallo = null;
    _noAntesDe = null;
    _resolviendo = null;
    enNube.value = false;
  }

  static Future<bool> _sondaHttp(String esquema, String ruta, Duration limite) async {
    try {
      final r = await http.get(Uri.parse('$esquema://$ruta/api/ping')).timeout(limite);
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Al arrancar la app: recuerda qué ruta estaba activa.
  static Future<void> cargar() async {
    final p = await SharedPreferences.getInstance();
    final nube = p.getString(_claveNube);
    enNube.value = nube != null && p.getString(claveActiva) == nube;
  }

  /// true si este móvil tiene ruta de nube (vinculado con un QR que la llevaba).
  static Future<bool> hayNube() async => (await SharedPreferences.getInstance()).getString(_claveNube) != null;

  /// Guarda las rutas de un QR recién leído. Siempre empieza por el PC. Sin [nube] (QR antiguo o PC
  /// sin sesión de nube) se olvida cualquier ruta de nube anterior.
  static Future<void> guardar({required String pc, String? nube}) async {
    final p = await SharedPreferences.getInstance();
    await p.setString(claveActiva, pc);
    await p.setString(_clavePc, pc);
    if (nube == null) {
      await p.remove(_claveNube);
    } else {
      await p.setString(_claveNube, nube);
    }
    enNube.value = false;
    _ultimoSondeoPc = null;
    _ultimoFallo = null;
    _noAntesDe = null;
    await p.remove(_claveInicioSesion);           // sesión nueva: se olvida dónde se entró antes
    await p.remove(_claveInicioEnNube);
  }

  /// La ruta del PC: lo que haya en la ruta activa si no es la de la nube (otras partes de la app
  /// pueden reescribirla, p. ej. al pasar a HTTPS) o, si no, la última del PC que se conoció.
  static String? _rutaPc(SharedPreferences p) {
    final activa = p.getString(claveActiva);
    final nube = p.getString(_claveNube);
    if (activa != null && activa != nube) return activa;
    return p.getString(_clavePc);
  }

  /// Decide la ruta: el PC si responde, si no la nube. Si no responde ninguna no cambia nada (y no
  /// insiste durante 20 s). Varias llamadas a la vez comparten la misma comprobación.
  static Future<void> resolver({bool forzar = false}) {
    return _resolviendo ??= _resolver(forzar).whenComplete(() => _resolviendo = null);
  }

  static Future<void> _resolver(bool forzar) async {
    final p = await SharedPreferences.getInstance();
    final nube = p.getString(_claveNube);
    if (nube == null) return;                     // sin ruta de nube no hay nada que decidir
    if (!forzar && _noAntesDe != null && ahora().isBefore(_noAntesDe!)) return;
    final pc = _rutaPc(p);
    // Entré en la nube hace poco: el PC aún no conoce mi sesión (le llega en su siguiente sincronización).
    if (pc != null && !await _pcNoConoceLaSesion(p)) {
      _ultimoSondeoPc = ahora();
      if (await sonda(esquemaPC, pc, esperaSondaPc)) {
        await _fijar(p, pc, nube, false);
        _noAntesDe = null;
        return;
      }
    }
    if (await sonda('https', nube, esperaSondaNube)) {
      await _fijar(p, pc, nube, true);
      _noAntesDe = null;
      return;
    }
    _noAntesDe = ahora().add(esperaTrasFallarTodo);
  }

  static Future<void> _fijar(SharedPreferences p, String? pc, String nube, bool aNube) async {
    if (pc != null) await p.setString(_clavePc, pc);
    await p.setString(claveActiva, aNube ? nube : pc!);
    enNube.value = aNube;
  }

  /// Llamar en cada comprobación periódica: con la nube activa, vuelve a probar el PC cada minuto.
  static Future<void> tictac() async {
    if (!enNube.value) return;
    final ultimo = _ultimoSondeoPc;
    if (ultimo != null && ahora().difference(ultimo) < volverAlPcCada) return;
    await resolver(forzar: true);
  }

  /// Llamar cuando una petición falla por la ruta (error de red o [esFalloDeRuta]). Como mucho una vez
  /// cada 5 segundos: las peticiones siguientes ya usan la ruta nueva.
  static Future<void> alFallar() async {
    final t = ahora();
    final ultimo = _ultimoFallo;
    if (ultimo != null && t.difference(ultimo) < minimoEntreFallos) return;
    _ultimoFallo = t;
    await resolver();
  }

  /// Códigos que significan «esta ruta no puede ahora» (no un error de la petición): licencia de la nube
  /// caducada o suspendida (402) y servidor caído o sin trabajador (502, 503, 504). NUNCA el 403 (es «sin
  /// permiso» y la app descarta el elemento de la cola) ni el 501 (fotos aún no disponibles en la nube).
  static bool esFalloDeRuta(int codigo) => codigo == 402 || codigo == 502 || codigo == 503 || codigo == 504;

  /// Apunta el momento y la ruta con la que se entró (para la regla del 401).
  static Future<void> marcarInicioSesion() async {
    final p = await SharedPreferences.getInstance();
    await p.setString(_claveInicioSesion, ahora().toIso8601String());
    await p.setBool(_claveInicioEnNube, enNube.value);
  }

  /// Cuándo se entró y con qué ruta, si fue hace menos de 15 minutos; si no, null.
  static (DateTime, bool)? _inicioReciente(SharedPreferences p) {
    final inicio = DateTime.tryParse(p.getString(_claveInicioSesion) ?? '');
    if (inicio == null || ahora().difference(inicio) >= graciaSesion) return null;
    return (inicio, p.getBool(_claveInicioEnNube) ?? false);
  }

  static Future<bool> _pcNoConoceLaSesion(SharedPreferences p) async => _inicioReciente(p)?.$2 ?? false;

  /// true si un 401 NO debe cerrar la sesión: se entró hace menos de 15 minutos por una ruta y ahora se
  /// está en la OTRA, que puede no conocer todavía la sesión (el PC y la nube se pasan las sesiones al
  /// sincronizar, con hasta 10 minutos de retraso). Pasado ese tiempo, o en la misma ruta en la que se
  /// entró, un 401 es real (p. ej. un técnico dado de baja).
  static Future<bool> sesionEnGracia() async {
    final p = await SharedPreferences.getInstance();
    final reciente = _inicioReciente(p);
    return reciente != null && enNube.value != reciente.$2;
  }
}
