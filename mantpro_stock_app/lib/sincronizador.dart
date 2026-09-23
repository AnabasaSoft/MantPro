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
/// Resultado de intentar enviar un elemento pendiente al PC: [ok] se envió
/// bien, [error] es un fallo de red o del servidor (se reintenta más tarde,
/// el elemento se queda en la cola) y [sinPermiso] es un rechazo explícito
/// del PC porque el usuario ya no tiene el rol necesario (el elemento se
/// quita de la cola, ya que reintentarlo no serviría de nada, y se avisa al
/// usuario mediante [permisoDenegadoNotifier]).
enum _ResultadoEnvio { ok, error, sinPermiso }

class StockSincronizador {
  static Future<_ResultadoEnvio> _enviarMultipart(String url, Map<String, dynamic> item,
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
      if (res.statusCode == 200) {
        // Si se ha subido una foto desde este móvil, el PC devuelve el
        // nombre de fichero definitivo: dejamos cacheada localmente la copia
        // que ya teníamos, para no tener que descargarla de vuelta.
        if (fotoPath != null && File(fotoPath).existsSync()) {
          try {
            final nombreFoto = (json.decode(res.body) as Map)['foto'] as String?;
            if (nombreFoto != null) await StockApi.guardarFotoEnCache(nombreFoto, fotoPath);
          } catch (_) {}
        }
        return _ResultadoEnvio.ok;
      }
      if (res.statusCode == 403) return _ResultadoEnvio.sinPermiso;
      return _ResultadoEnvio.error;
    } catch (_) {
      return _ResultadoEnvio.error;
    }
  }

  static Future<_ResultadoEnvio> _enviarMaterial(String ip, Map<String, dynamic> item, {required bool esNuevo}) {
    if (esNuevo) {
      return _enviarMultipart('http://$ip/api/stock/material', item, omitir: const ['localId']);
    }
    final id = item['id'];
    final campos = Map<String, dynamic>.from(item)..remove('id');
    if (item['borrarFoto'] == true) campos['borrar_foto'] = '1';
    return _enviarMultipart('http://$ip/api/stock/material/$id', campos,
        omitir: const ['localId', 'borrarFoto']);
  }

  static Future<_ResultadoEnvio> _enviarBorrado(String ip, int id) async {
    try {
      final res = await http
          .delete(Uri.parse('http://$ip/api/stock/material/$id'), headers: AuthService.cabeceras())
          .timeout(const Duration(seconds: 10));
      await comprobar401(res.statusCode);
      // 404 (el material ya no existe en el PC) también se considera hecho.
      if (res.statusCode == 200 || res.statusCode == 404) return _ResultadoEnvio.ok;
      if (res.statusCode == 403) return _ResultadoEnvio.sinPermiso;
      return _ResultadoEnvio.error;
    } catch (_) {
      return _ResultadoEnvio.error;
    }
  }

  static Future<_ResultadoEnvio> _enviarMovimiento(String ip, Map<String, dynamic> item) async {
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
      if (res.statusCode == 200) return _ResultadoEnvio.ok;
      if (res.statusCode == 403) return _ResultadoEnvio.sinPermiso;
      return _ResultadoEnvio.error;
    } catch (_) {
      return _ResultadoEnvio.error;
    }
  }

  /// Añade una descripción a [permisoDenegadoNotifier] para que la app avise
  /// al usuario de que un cambio pendiente se ha descartado por falta de
  /// permisos, en vez de dejarlo desaparecer en silencio de la cola.
  static void _avisarSinPermiso(String descripcion) {
    permisoDenegadoNotifier.value = [...permisoDenegadoNotifier.value, descripcion];
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

    final resultado = colaKey == kStockColaMovimientos
        ? await _enviarMovimiento(ip, item)
        : await _enviarMaterial(ip, item, esNuevo: colaKey == kStockColaNuevos);
    if (resultado != _ResultadoEnvio.error) {
      // ok o sinPermiso: en ambos casos se quita de la cola (si es sinPermiso
      // reintentarlo no serviría de nada) y se avisa al usuario si procede.
      cola.removeWhere((e) => e['localId'] == localId);
      await prefs.setString(colaKey, json.encode(cola));
    }
    if (resultado == _ResultadoEnvio.sinPermiso) {
      _avisarSinPermiso(item['nombre']?.toString() ?? tt('lbl_articulo', 'Artículo'));
    }
    return resultado == _ResultadoEnvio.ok;
  }

  /// Igual que [intentarEnviarInmediato] pero para un borrado, cuya cola solo
  /// guarda ids sueltos (no mapas con 'localId').
  static Future<bool> intentarBorrarInmediato(String ip, int id) async {
    if (!AuthService.autenticado) await AuthService.cargar();
    if (!AuthService.autenticado) return false;
    final resultado = await _enviarBorrado(ip, id);
    if (resultado != _ResultadoEnvio.error) {
      final prefs = await SharedPreferences.getInstance();
      final cola = leerColaIds(prefs, kStockColaBorrados);
      cola.remove(id);
      await prefs.setString(kStockColaBorrados, json.encode(cola));
    }
    if (resultado == _ResultadoEnvio.sinPermiso) {
      _avisarSinPermiso(tt('msg_borrado_articulo', 'Borrado de artículo'));
    }
    return resultado == _ResultadoEnvio.ok;
  }

  static Future<void> sincronizarTodo(String ip, {bool silencioso = false}) async {
    final prefs = await SharedPreferences.getInstance();
    // La sincronización puede lanzarse fuera de la UI: recargamos el token.
    if (!AuthService.autenticado) await AuthService.cargar();
    if (!AuthService.autenticado) return; // sin sesión no se envía nada

    // 1. Artículos nuevos
    final colaNuevos = leerColaMapas(prefs, kStockColaNuevos);
    final nuevosQuitar = <Map<String, dynamic>>[];
    for (final item in colaNuevos) {
      final resultado = await _enviarMaterial(ip, item, esNuevo: true);
      if (resultado != _ResultadoEnvio.error) nuevosQuitar.add(item);
      if (resultado == _ResultadoEnvio.sinPermiso) {
        _avisarSinPermiso(item['nombre']?.toString() ?? tt('lbl_articulo', 'Artículo'));
      }
    }
    for (final item in nuevosQuitar) {
      colaNuevos.remove(item);
    }
    await prefs.setString(kStockColaNuevos, json.encode(colaNuevos));

    // 2. Ediciones de artículos existentes
    final colaEdiciones = leerColaMapas(prefs, kStockColaEdiciones);
    final edicionesQuitar = <Map<String, dynamic>>[];
    for (final item in colaEdiciones) {
      final resultado = await _enviarMaterial(ip, item, esNuevo: false);
      if (resultado != _ResultadoEnvio.error) edicionesQuitar.add(item);
      if (resultado == _ResultadoEnvio.sinPermiso) {
        _avisarSinPermiso(item['nombre']?.toString() ?? tt('lbl_articulo', 'Artículo'));
      }
    }
    for (final item in edicionesQuitar) {
      colaEdiciones.remove(item);
    }
    await prefs.setString(kStockColaEdiciones, json.encode(colaEdiciones));

    // 3. Movimientos (entradas/salidas)
    final colaMovimientos = leerColaMapas(prefs, kStockColaMovimientos);
    final movimientosQuitar = <Map<String, dynamic>>[];
    for (final item in colaMovimientos) {
      final resultado = await _enviarMovimiento(ip, item);
      if (resultado != _ResultadoEnvio.error) movimientosQuitar.add(item);
      if (resultado == _ResultadoEnvio.sinPermiso) {
        _avisarSinPermiso(tt('lbl_movimiento_stock', 'Movimiento de stock'));
      }
    }
    for (final item in movimientosQuitar) {
      colaMovimientos.remove(item);
    }
    await prefs.setString(kStockColaMovimientos, json.encode(colaMovimientos));

    // 4. Borrados
    final colaBorrados = leerColaIds(prefs, kStockColaBorrados);
    final borradosQuitar = <int>[];
    for (final id in colaBorrados) {
      final resultado = await _enviarBorrado(ip, id);
      if (resultado != _ResultadoEnvio.error) borradosQuitar.add(id);
      if (resultado == _ResultadoEnvio.sinPermiso) {
        _avisarSinPermiso(tt('msg_borrado_articulo', 'Borrado de artículo'));
      }
    }
    for (final id in borradosQuitar) {
      colaBorrados.remove(id);
    }
    await prefs.setString(kStockColaBorrados, json.encode(colaBorrados));

    // 5. Refrescamos las cachés de lectura y los roles del usuario (por si
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
