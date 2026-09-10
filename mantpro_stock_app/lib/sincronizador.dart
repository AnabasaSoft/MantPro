// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later

import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'api.dart';

/// Sincroniza con el PC todo lo que se haya guardado en el móvil mientras no
/// había conexión: artículos nuevos, ediciones y movimientos de stock. Sigue
/// el mismo patrón que SincronizadorGlobal de la app de trabajos: cada cola
/// se intenta enviar entera, los envíos que tienen éxito se quitan de la
/// cola y el resto se queda para el siguiente intento.
class StockSincronizador {
  static Future<bool> _enviarMultipart(String url, Map<String, dynamic> item,
      {List<String> omitir = const []}) async {
    try {
      final req = http.MultipartRequest('POST', Uri.parse(url));
      req.headers.addAll(AuthService.cabeceras());
      for (final entrada in item.entries) {
        if (entrada.key == 'fotoPath' || omitir.contains(entrada.key) || entrada.value == null) continue;
        req.fields[entrada.key] = entrada.value.toString();
      }
      final fotoPath = item['fotoPath'] as String?;
      if (fotoPath != null && File(fotoPath).existsSync()) {
        req.files.add(await http.MultipartFile.fromPath('foto', fotoPath));
      }
      final streamed = await req.send().timeout(const Duration(seconds: 20));
      final res = await http.Response.fromStream(streamed);
      await comprobar401(res.statusCode);
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> _enviarMaterial(String ip, Map<String, dynamic> item, {required bool esNuevo}) {
    if (esNuevo) {
      return _enviarMultipart('http://$ip/api/stock/material', item, omitir: const ['localId']);
    }
    final id = item['id'];
    final campos = Map<String, dynamic>.from(item)..remove('id');
    if (item['borrarFoto'] == true) campos['borrar_foto'] = '1';
    return _enviarMultipart('http://$ip/api/stock/material/$id', campos,
        omitir: const ['localId', 'borrarFoto']);
  }

  static Future<bool> _enviarMovimiento(String ip, Map<String, dynamic> item) async {
    try {
      final res = await http.post(
        Uri.parse('http://$ip/api/stock/material/${item['materialId']}/movimiento'),
        headers: AuthService.cabeceras(),
        body: {
          'tipo': item['tipo'].toString(),
          'cantidad': item['cantidad'].toString(),
          'motivo': (item['motivo'] ?? '').toString(),
        },
      ).timeout(const Duration(seconds: 10));
      await comprobar401(res.statusCode);
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Intenta enviar solo el elemento [localId] de la cola [colaKey], con un
  /// tiempo de espera acotado por el propio envío. Se usa justo después de
  /// guardar algo, para poder decirle al usuario si ya está en el PC o si se
  /// ha quedado pendiente, sin bloquear la pantalla esperando el resto de la
  /// sincronización (eso se hace aparte, en segundo plano).
  static Future<bool> intentarEnviarInmediato(String ip, String colaKey, int localId) async {
    if (!AuthService.autenticado) await AuthService.cargar();
    if (!AuthService.autenticado) return false;
    final prefs = await SharedPreferences.getInstance();
    final cola = leerColaMapas(prefs, colaKey);
    Map<String, dynamic>? item;
    for (final e in cola) {
      if (e['localId'] == localId) {
        item = e;
        break;
      }
    }
    if (item == null) return true; // ya no está en la cola: se sincronizó por otra vía

    final ok = colaKey == kStockColaMovimientos
        ? await _enviarMovimiento(ip, item)
        : await _enviarMaterial(ip, item, esNuevo: colaKey == kStockColaNuevos);
    if (ok) {
      cola.removeWhere((e) => e['localId'] == localId);
      await prefs.setString(colaKey, json.encode(cola));
    }
    return ok;
  }

  static Future<void> sincronizarTodo(String ip, {bool silencioso = false}) async {
    final prefs = await SharedPreferences.getInstance();
    // La sincronización puede lanzarse fuera de la UI: recargamos el token.
    if (!AuthService.autenticado) await AuthService.cargar();
    if (!AuthService.autenticado) return; // sin sesión no se envía nada

    // 1. Artículos nuevos
    final colaNuevos = leerColaMapas(prefs, kStockColaNuevos);
    final nuevosOk = <Map<String, dynamic>>[];
    for (final item in colaNuevos) {
      if (await _enviarMaterial(ip, item, esNuevo: true)) nuevosOk.add(item);
    }
    for (final item in nuevosOk) {
      colaNuevos.remove(item);
    }
    await prefs.setString(kStockColaNuevos, json.encode(colaNuevos));

    // 2. Ediciones de artículos existentes
    final colaEdiciones = leerColaMapas(prefs, kStockColaEdiciones);
    final edicionesOk = <Map<String, dynamic>>[];
    for (final item in colaEdiciones) {
      if (await _enviarMaterial(ip, item, esNuevo: false)) edicionesOk.add(item);
    }
    for (final item in edicionesOk) {
      colaEdiciones.remove(item);
    }
    await prefs.setString(kStockColaEdiciones, json.encode(colaEdiciones));

    // 3. Movimientos (entradas/salidas)
    final colaMovimientos = leerColaMapas(prefs, kStockColaMovimientos);
    final movimientosOk = <Map<String, dynamic>>[];
    for (final item in colaMovimientos) {
      if (await _enviarMovimiento(ip, item)) movimientosOk.add(item);
    }
    for (final item in movimientosOk) {
      colaMovimientos.remove(item);
    }
    await prefs.setString(kStockColaMovimientos, json.encode(colaMovimientos));

    // 4. Refrescamos las cachés de lectura y los roles del usuario (por si
    // han cambiado en el PC mientras la app estaba conectada).
    try {
      final res = await httpGetAuth(Uri.parse('http://$ip/api/stock/estructura'))
          .timeout(const Duration(seconds: 8));
      if (res.statusCode == 200) await prefs.setString(kStockCacheEstructura, res.body);
    } catch (_) {}
    try {
      final res = await httpGetAuth(Uri.parse('http://$ip/api/stock/materiales'))
          .timeout(const Duration(seconds: 8));
      if (res.statusCode == 200) await prefs.setString(kStockCacheMateriales, res.body);
    } catch (_) {}
    try {
      final res = await httpGetAuth(Uri.parse('http://$ip/api/stock/bajo_minimo'))
          .timeout(const Duration(seconds: 8));
      if (res.statusCode == 200) await prefs.setString(kStockCacheBajoMinimo, res.body);
    } catch (_) {}
    await AuthService.refrescarRoles();

    datosSincronizadosNotifier.value++;
  }
}
