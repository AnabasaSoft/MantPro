// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later

import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'modelos.dart';
import 'i18n/strings.dart';
import 'sincronizador.dart';

/// true = hay sesión iniciada. AuthGate lo escucha para mostrar login o app.
final ValueNotifier<bool> sesionNotifier = ValueNotifier(false);

/// Se incrementa cada vez que se refrescan los roles del usuario desde el PC
/// (ver AuthService.refrescarRoles). Las pantallas que muestran u ocultan
/// botones según el rol lo escuchan para actualizarse solas, sin necesidad
/// de cerrar y volver a abrir sesión cuando cambian los permisos en el PC.
final ValueNotifier<int> rolesActualizadosNotifier = ValueNotifier(0);

/// Se incrementa cada vez que termina una sincronización con el PC (con o sin
/// conexión). Las pantallas lo escuchan para refrescarse desde la caché local.
final ValueNotifier<int> datosSincronizadosNotifier = ValueNotifier(0);

/// Lista de descripciones de cambios pendientes que el PC ha rechazado por
/// falta de permisos (p. ej. el admin le ha quitado el rol de almacén al
/// usuario después de que dejara algo en la cola offline). main.dart escucha
/// este notificador para avisar al usuario con un diálogo, ya que si no se
/// notifica el cambio se pierde en silencio.
final ValueNotifier<List<String>> permisoDenegadoNotifier = ValueNotifier([]);

/// t() con texto por defecto, por si la clave aún no está en i18n/strings.dart.
String tt(String clave, String defecto) {
  final v = t(clave);
  return v == clave ? defecto : v;
}

/// Modelo del móvil (p.ej. "Samsung SM-G991B"), para distinguir sesiones en
/// "Sesiones de dispositivos" cuando hay varios móviles con la misma app.
Future<String> _nombreDispositivo() async {
  try {
    final infoPlugin = DeviceInfoPlugin();
    if (Platform.isAndroid) {
      final info = await infoPlugin.androidInfo;
      return '${info.manufacturer} ${info.model}'.trim();
    }
    if (Platform.isIOS) {
      final info = await infoPlugin.iosInfo;
      return info.name.isNotEmpty ? info.name : info.utsname.machine;
    }
  } catch (_) {}
  return 'Android';
}

class AuthService {
  static String? token;
  static String? nombre;
  static String? login;
  static String? rol;
  static List<String> roles = [];
  static int? usuarioId;

  static bool get autenticado => token != null && token!.isNotEmpty;

  /// Solo admin y almacén pueden dar de alta/editar artículos y registrar movimientos de stock.
  /// Un usuario puede tener varios roles a la vez (p.ej. técnico y almacén).
  static bool get puedeGestionarAlmacen => roles.contains('admin') || roles.contains('almacen');

  static Future<void> cargar() async {
    final prefs = await SharedPreferences.getInstance();
    token = prefs.getString('auth_token');
    nombre = prefs.getString('auth_nombre');
    login = prefs.getString('auth_login');
    rol = prefs.getString('auth_rol');
    roles = prefs.getStringList('auth_roles') ?? (rol != null ? [rol!] : []);
    usuarioId = prefs.getInt('auth_id');
  }

  static Map<String, String> cabeceras() =>
      token != null ? {'Authorization': 'Bearer $token'} : {};

  static Future<String?> iniciarSesion(String ip, String usuario, String password) async {
    try {
      final res = await http.post(
        Uri.parse('http://$ip/api/login'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'login': usuario,
          'password': password,
          'dispositivo': '${await _nombreDispositivo()} (Stock)',
        }),
      ).timeout(const Duration(seconds: 10));

      final datos = json.decode(res.body) as Map<String, dynamic>;
      if (res.statusCode == 200 && datos['status'] == 'ok') {
        final prefs = await SharedPreferences.getInstance();
        token = datos['token'];
        nombre = datos['usuario']['nombre'];
        login = datos['usuario']['login'];
        rol = datos['usuario']['rol'];
        roles = (datos['usuario']['roles'] as List?)?.map((r) => r.toString()).toList() ??
            [rol ?? 'tecnico'];
        usuarioId = datos['usuario']['id'];
        await prefs.setInt('auth_id', usuarioId ?? 0);
        await prefs.setString('auth_token', token!);
        await prefs.setString('auth_nombre', nombre ?? '');
        await prefs.setString('auth_login', login ?? '');
        await prefs.setString('auth_rol', rol ?? 'tecnico');
        await prefs.setStringList('auth_roles', roles);
        sesionNotifier.value = true;
        return null;
      }
      return datos['message'] ?? tt('login_error', 'Usuario o contraseña incorrectos.');
    } catch (e) {
      return tt('login_sin_conexion',
          'No se pudo conectar con el PC. Comprueba la WiFi y que MantPro esté abierto.');
    }
  }

  static Future<void> cerrarSesion({String? ip}) async {
    if (ip != null && token != null) {
      try {
        await http.post(Uri.parse('http://$ip/api/logout'), headers: cabeceras())
            .timeout(const Duration(seconds: 5));
      } catch (_) {}
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('auth_nombre');
    await prefs.remove('auth_login');
    await prefs.remove('auth_rol');
    await prefs.remove('auth_roles');
    await prefs.remove('auth_id');
    token = null; nombre = null; login = null; rol = null; roles = []; usuarioId = null;
    sesionNotifier.value = false;
  }

  /// Vuelve a preguntar al PC quién soy (roles incluidos) sin necesidad de
  /// reintroducir la contraseña. Si el PC cambia el rol de este usuario (por
  /// ejemplo le añade "almacén"), el móvil lo detecta solo la próxima vez que
  /// se llame a esto, sin tener que cerrar y volver a abrir sesión.
  static Future<void> refrescarRoles() async {
    if (!autenticado) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      final ip = prefs.getString('pc_ip_url');
      if (ip == null) return;
      final res = await httpGetAuth(Uri.parse('http://$ip/api/yo')).timeout(const Duration(seconds: 8));
      if (res.statusCode != 200) return;
      final datos = json.decode(res.body);
      if (datos['status'] != 'ok') return;
      final nuevosRoles = ((datos['usuario']['roles'] as List?) ?? [])
          .map((r) => r.toString())
          .toList();
      if (nuevosRoles.isEmpty) return;
      nuevosRoles.sort();
      final actuales = List<String>.from(roles)..sort();
      if (listEquals(nuevosRoles, actuales)) return;
      roles = ((datos['usuario']['roles'] as List?) ?? []).map((r) => r.toString()).toList();
      rol = datos['usuario']['rol'];
      await prefs.setStringList('auth_roles', roles);
      await prefs.setString('auth_rol', rol ?? 'tecnico');
      rolesActualizadosNotifier.value++;
    } catch (_) {
      // Sin conexión con el PC: se sigue trabajando con los roles conocidos.
    }
  }
}

/// Si el PC responde 401, el token ya no vale: cerramos sesión y volvemos al login.
Future<void> comprobar401(int codigo) async {
  if (codigo == 401) {
    await AuthService.cerrarSesion();
  }
}

Future<http.Response> httpGetAuth(Uri url) async {
  final res = await http.get(url, headers: AuthService.cabeceras());
  await comprobar401(res.statusCode);
  return res;
}

class ApiException implements Exception {
  final String mensaje;
  ApiException(this.mensaje);
  @override
  String toString() => mensaje;
}

// Claves de SharedPreferences para la caché de lectura y las colas de
// escrituras pendientes de sincronizar con el PC (igual que en la app de
// trabajos: se guarda todo como JSON y SincronizadorStock lo va vaciando).
const String kStockCacheEstructura = 'stock_cache_estructura';
const String kStockCacheMateriales = 'stock_cache_materiales';
const String kStockCacheBajoMinimo = 'stock_cache_bajo_minimo';
const String kStockColaNuevos = 'stock_cola_nuevos';
const String kStockColaEdiciones = 'stock_cola_ediciones';
const String kStockColaMovimientos = 'stock_cola_movimientos';
const String kStockColaBorrados = 'stock_cola_borrados';

List<Map<String, dynamic>> leerColaMapas(SharedPreferences prefs, String key) {
  final s = prefs.getString(key);
  if (s == null) return [];
  return List<Map<String, dynamic>>.from(json.decode(s) as List);
}

List<int> leerColaIds(SharedPreferences prefs, String key) {
  final s = prefs.getString(key);
  if (s == null) return [];
  return List<int>.from(json.decode(s) as List);
}

/// Todas las llamadas al backend de stock del PC (comparte servidor y login con MantPro).
class StockApi {
  static Future<String> _ip() async {
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString('pc_ip_url');
    if (ip == null) throw ApiException(tt('msg_sin_conexion_pc', 'Sin conexión con el PC'));
    return ip;
  }

  static Future<List<Estanteria>> obtenerEstructura() async {
    try {
      final ip = await _ip();
      final res = await httpGetAuth(Uri.parse('http://$ip/api/stock/estructura'))
          .timeout(const Duration(seconds: 4));
      final datos = json.decode(res.body);
      if (res.statusCode != 200 || datos['status'] != 'ok') {
        throw ApiException(datos['message'] ?? 'Error al cargar la estructura del almacén');
      }
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(kStockCacheEstructura, res.body);
      return (datos['estanterias'] as List).map((e) => Estanteria.fromJson(e)).toList();
    } on ApiException {
      rethrow;
    } catch (_) {
      final cache = await _cacheEstructura();
      if (cache != null) return cache;
      throw ApiException(tt('msg_sin_conexion_pc', 'Sin conexión con el PC'));
    }
  }

  static Future<List<Estanteria>?> _cacheEstructura() async {
    final prefs = await SharedPreferences.getInstance();
    final s = prefs.getString(kStockCacheEstructura);
    if (s == null) return null;
    final datos = json.decode(s);
    return (datos['estanterias'] as List).map((e) => Estanteria.fromJson(e)).toList();
  }

  static Future<List<Articulo>?> _cacheMateriales() async {
    final prefs = await SharedPreferences.getInstance();
    final s = prefs.getString(kStockCacheMateriales);
    if (s == null) return null;
    final datos = json.decode(s);
    return (datos['materiales'] as List).map((m) => Articulo.fromJson(m)).toList();
  }

  /// Aplica sobre [base] las escrituras que aún no se han podido enviar al PC:
  /// ediciones y movimientos de artículos existentes, y artículos nuevos
  /// (con id negativo temporal) que todavía no tienen id real del servidor.
  static Future<List<Articulo>> _conPendientes(List<Articulo> base) async {
    final prefs = await SharedPreferences.getInstance();
    final ediciones = leerColaMapas(prefs, kStockColaEdiciones);
    final movimientos = leerColaMapas(prefs, kStockColaMovimientos);
    final nuevos = leerColaMapas(prefs, kStockColaNuevos);
    final borrados = leerColaIds(prefs, kStockColaBorrados);
    // Los artículos borrados en el móvil desaparecen al momento aunque el PC
    // todavía no haya confirmado el borrado (se retira de la cola en cuanto
    // haya conexión).
    var lista = List<Articulo>.from(base)..removeWhere((a) => borrados.contains(a.id));

    for (final e in ediciones) {
      final idx = lista.indexWhere((a) => a.id == e['id']);
      if (idx == -1) continue;
      final a = lista[idx];
      lista[idx] = Articulo(
        id: a.id,
        codigo: e['codigo'] ?? a.codigo,
        nombre: e['nombre'] ?? a.nombre,
        descripcion: e['descripcion'] ?? a.descripcion,
        unidad: e['unidad'] ?? a.unidad,
        stockActual: a.stockActual,
        stockMinimo: double.tryParse('${e['stock_minimo']}') ?? a.stockMinimo,
        seccionId: int.tryParse('${e['seccion_id']}') ?? a.seccionId,
        foto: a.foto,
        ubicacion: a.ubicacion,
      );
    }

    for (final m in movimientos) {
      final idx = lista.indexWhere((a) => a.id == m['materialId']);
      if (idx == -1) continue;
      final cantidad = double.tryParse('${m['cantidad']}') ?? 0;
      final delta = m['tipo'] == 'salida' ? -cantidad : cantidad;
      lista[idx] = lista[idx].conStockAjustado(delta);
    }

    for (final n in nuevos) {
      final localId = n['localId'] as int;
      lista.add(Articulo(
        // Id temporal estable (basado en el localId de la cola, no en la
        // posición en la lista) para poder editarlo o borrarlo mientras
        // sigue pendiente de enviar al PC.
        id: -localId,
        codigo: n['codigo'] ?? '',
        nombre: n['nombre'] ?? '',
        descripcion: n['descripcion'] ?? '',
        unidad: n['unidad'] ?? '',
        stockActual: double.tryParse('${n['stock_inicial']}') ?? 0,
        stockMinimo: double.tryParse('${n['stock_minimo']}') ?? 0,
        seccionId: int.tryParse('${n['seccion_id']}'),
        foto: null,
        ubicacion: '',
      ));
    }
    return lista;
  }

  static Future<List<Articulo>> obtenerMateriales({String? q}) async {
    try {
      final ip = await _ip();
      final uri = Uri.parse('http://$ip/api/stock/materiales')
          .replace(queryParameters: (q != null && q.isNotEmpty) ? {'q': q} : null);
      final res = await httpGetAuth(uri).timeout(const Duration(seconds: 4));
      final datos = json.decode(res.body);
      if (res.statusCode != 200 || datos['status'] != 'ok') {
        throw ApiException(datos['message'] ?? 'Error al cargar los materiales');
      }
      final lista = (datos['materiales'] as List).map((m) => Articulo.fromJson(m)).toList();
      if (q == null || q.isEmpty) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(kStockCacheMateriales, res.body);
        return _conPendientes(lista);
      }
      return lista;
    } on ApiException {
      rethrow;
    } catch (_) {
      final cache = await _cacheMateriales();
      if (cache == null) throw ApiException(tt('msg_sin_conexion_pc', 'Sin conexión con el PC'));
      final conPendientes = await _conPendientes(cache);
      if (q == null || q.isEmpty) return conPendientes;
      final ql = q.toLowerCase();
      return conPendientes
          .where((m) => m.nombre.toLowerCase().contains(ql) || m.codigo.toLowerCase().contains(ql))
          .toList();
    }
  }

  static Future<List<Articulo>> materialesBajoMinimo() async {
    try {
      final ip = await _ip();
      final res = await httpGetAuth(Uri.parse('http://$ip/api/stock/bajo_minimo'))
          .timeout(const Duration(seconds: 4));
      final datos = json.decode(res.body);
      if (res.statusCode != 200 || datos['status'] != 'ok') {
        throw ApiException(datos['message'] ?? 'Error al cargar el stock bajo mínimo');
      }
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(kStockCacheBajoMinimo, res.body);
      return (datos['materiales'] as List).map((m) => Articulo.fromJson(m)).toList();
    } on ApiException {
      rethrow;
    } catch (_) {
      // Sin conexión: recalculamos el bajo mínimo a partir de la caché de
      // materiales (ya con las escrituras pendientes aplicadas).
      final cache = await _cacheMateriales();
      if (cache == null) throw ApiException(tt('msg_sin_conexion_pc', 'Sin conexión con el PC'));
      final conPendientes = await _conPendientes(cache);
      return conPendientes.where((m) => m.bajoMinimo).toList();
    }
  }

  static Future<(Articulo, List<Movimiento>)> obtenerMaterial(int id) async {
    try {
      final ip = await _ip();
      final res = await httpGetAuth(Uri.parse('http://$ip/api/stock/material/$id'))
          .timeout(const Duration(seconds: 4));
      final datos = json.decode(res.body);
      if (res.statusCode != 200 || datos['status'] != 'ok') {
        throw ApiException(datos['message'] ?? 'Artículo no encontrado');
      }
      final m = Articulo.fromJson(datos['material']);
      final movs = ((datos['material']['movimientos'] as List?) ?? [])
          .map((x) => Movimiento.fromJson(x))
          .toList();
      return (m, movs);
    } on ApiException {
      rethrow;
    } catch (_) {
      final cache = await _cacheMateriales();
      if (cache != null) {
        final conPendientes = await _conPendientes(cache);
        final encontrado = conPendientes.where((a) => a.id == id);
        if (encontrado.isNotEmpty) return (encontrado.first, <Movimiento>[]);
      }
      throw ApiException(tt('msg_sin_conexion_pc', 'Sin conexión con el PC'));
    }
  }

  static String urlFoto(String ip, String foto) => 'http://$ip/api/foto/$foto';

  static Future<String> ipActual() => _ip();

  /// Crea o edita un artículo. Si [id] es null, crea uno nuevo.
  ///
  /// El cambio se guarda primero en el móvil (como en la app de trabajos) y
  /// se intenta enviar al PC en el acto; si no hay conexión se queda en la
  /// cola y se reintentará solo en la siguiente sincronización. Devuelve
  /// `true` si ya se ha confirmado en el PC, `false` si ha quedado pendiente.
  static Future<bool> guardarMaterial({
    int? id,
    required String codigo,
    required String nombre,
    required String descripcion,
    required String unidad,
    required double stockMinimo,
    int? seccionId,
    int? baldaId,
    double stockInicial = 0,
    File? foto,
    bool borrarFoto = false,
  }) async {
    final esNuevo = id == null;
    // Los artículos dados de alta sin conexión tienen un id temporal negativo
    // hasta que el PC confirma el alta: editarlos no requiere avisar al
    // servidor todavía, basta con actualizar los datos que están pendientes
    // de enviar en la propia cola de altas.
    final esTemporalExistente = id != null && id < 0;
    final campos = <String, String>{
      'codigo': codigo,
      'nombre': nombre,
      'descripcion': descripcion,
      'unidad': unidad,
      'stock_minimo': stockMinimo.toString(),
      // Si no se ha elegido sección todavía se manda la balda (o el hueco de
      // suelo) y el servidor resuelve o crea una sección por defecto: así no
      // hace falta tener secciones creadas de antemano para dar de alta.
      if (seccionId != null) 'seccion_id': seccionId.toString(),
      if (seccionId == null && baldaId != null) 'balda_id': baldaId.toString(),
    };
    if (esNuevo) campos['stock_inicial'] = stockInicial.toString();
    if (borrarFoto) campos['borrar_foto'] = '1';

    final prefs = await SharedPreferences.getInstance();

    if (esTemporalExistente) {
      final localId = -id;
      final cola = leerColaMapas(prefs, kStockColaNuevos);
      final idx = cola.indexWhere((e) => e['localId'] == localId);
      if (idx == -1) {
        throw ApiException(tt('msg_articulo_no_encontrado', 'Artículo no encontrado'));
      }
      cola[idx] = {
        ...cola[idx],
        ...campos,
        'fotoPath': borrarFoto ? null : (foto?.path ?? cola[idx]['fotoPath']),
      };
      await prefs.setString(kStockColaNuevos, json.encode(cola));
      final ip = await _ip();
      bool sincronizado = false;
      try {
        sincronizado = await StockSincronizador.intentarEnviarInmediato(ip, kStockColaNuevos, localId);
      } catch (_) {}
      // ignore: unawaited_futures
      StockSincronizador.sincronizarTodo(ip, silencioso: true);
      return sincronizado;
    }

    final ip = await _ip();
    final localId = DateTime.now().microsecondsSinceEpoch;
    final colaKey = esNuevo ? kStockColaNuevos : kStockColaEdiciones;
    if (esNuevo) {
      final cola = leerColaMapas(prefs, kStockColaNuevos);
      cola.add({'localId': localId, ...campos, 'fotoPath': foto?.path});
      await prefs.setString(kStockColaNuevos, json.encode(cola));
    } else {
      final cola = leerColaMapas(prefs, kStockColaEdiciones);
      cola.removeWhere((e) => e['id'] == id);
      cola.add({'localId': localId, 'id': id, ...campos, 'fotoPath': foto?.path, 'borrarFoto': borrarFoto});
      await prefs.setString(kStockColaEdiciones, json.encode(cola));
    }

    // Intento inmediato y acotado en el tiempo, para poder avisar al usuario
    // sin dejarle esperando: el resto de la cola y las cachés se reconcilian
    // aparte, en segundo plano, sin bloquear esta pantalla.
    bool sincronizado = false;
    try {
      sincronizado = await StockSincronizador.intentarEnviarInmediato(ip, colaKey, localId);
    } catch (_) {}
    // ignore: unawaited_futures
    StockSincronizador.sincronizarTodo(ip, silencioso: true);
    return sincronizado;
  }

  /// Registra una entrada o salida de stock. Igual que [guardarMaterial]: se
  /// guarda en el móvil y se intenta sincronizar en el acto; si no hay
  /// conexión queda pendiente y se reintenta más tarde.
  static Future<bool> registrarMovimiento({
    required int materialId,
    required String tipo,
    required double cantidad,
    String motivo = '',
  }) async {
    final prefs = await SharedPreferences.getInstance();
    if (materialId < 0) {
      // El artículo todavía no existe en el PC: se ajusta directamente la
      // cantidad inicial pendiente de enviar, sin cola de movimientos.
      final localId = -materialId;
      final cola = leerColaMapas(prefs, kStockColaNuevos);
      final idx = cola.indexWhere((e) => e['localId'] == localId);
      if (idx == -1) {
        throw ApiException(tt('msg_articulo_no_encontrado', 'Artículo no encontrado'));
      }
      final actual = double.tryParse('${cola[idx]['stock_inicial']}') ?? 0;
      final delta = tipo == 'salida' ? -cantidad : cantidad;
      cola[idx] = {...cola[idx], 'stock_inicial': (actual + delta).toString()};
      await prefs.setString(kStockColaNuevos, json.encode(cola));
      return true;
    }
    final ip = await _ip();
    final localId = DateTime.now().microsecondsSinceEpoch;
    final cola = leerColaMapas(prefs, kStockColaMovimientos);
    cola.add({'localId': localId, 'materialId': materialId, 'tipo': tipo, 'cantidad': cantidad, 'motivo': motivo});
    await prefs.setString(kStockColaMovimientos, json.encode(cola));

    bool sincronizado = false;
    try {
      sincronizado = await StockSincronizador.intentarEnviarInmediato(ip, kStockColaMovimientos, localId);
    } catch (_) {}
    // ignore: unawaited_futures
    StockSincronizador.sincronizarTodo(ip, silencioso: true);
    return sincronizado;
  }

  /// Elimina un artículo. Igual que las demás escrituras: desaparece de
  /// inmediato en el móvil (ver [_conPendientes]) y se confirma en el PC en
  /// el acto si hay conexión, o se queda en la cola para el siguiente intento.
  static Future<bool> borrarMaterial(int id) async {
    final prefs = await SharedPreferences.getInstance();
    if (id < 0) {
      // El artículo se dio de alta sin conexión y todavía no se ha enviado
      // al PC: basta con quitarlo de la cola de altas, no hay nada que borrar
      // en el servidor.
      final localId = -id;
      final cola = leerColaMapas(prefs, kStockColaNuevos);
      cola.removeWhere((e) => e['localId'] == localId);
      await prefs.setString(kStockColaNuevos, json.encode(cola));
      return true;
    }
    final ip = await _ip();
    final cola = leerColaIds(prefs, kStockColaBorrados);
    if (!cola.contains(id)) cola.add(id);
    await prefs.setString(kStockColaBorrados, json.encode(cola));

    bool sincronizado = false;
    try {
      sincronizado = await StockSincronizador.intentarBorrarInmediato(ip, id);
    } catch (_) {}
    // ignore: unawaited_futures
    StockSincronizador.sincronizarTodo(ip, silencioso: true);
    return sincronizado;
  }
}
