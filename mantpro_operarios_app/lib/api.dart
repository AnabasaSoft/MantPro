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

// Sesión de la tablet (un administrador que la vincula) y utilidades comunes
// de las peticiones al servidor (PC o MantPro Cloud): mismo patrón que
// mantpro_stock_app/lib/api.dart.
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'conexion_segura.dart';
import 'i18n/strings.dart';
import 'rutas_servidor.dart';

/// true = la tablet está vinculada (hay token). La puerta de entrada lo escucha para mostrar la vinculación o el quiosco.
final ValueNotifier<bool> sesionNotifier = ValueNotifier(false);

/// Identificador único de una operación (cabecera X-MantPro-Op): el servidor lo usa para no repetir
/// un aviso si el envío se reintenta. Igual que mantenimiento_app/lib/main.dart.
String nuevaOperacion() {
  final r = Random.secure();
  final azar = List.generate(4, (_) => r.nextInt(1 << 16).toRadixString(36).padLeft(4, '0')).join();
  return 'mp-${DateTime.now().microsecondsSinceEpoch.toRadixString(36)}-$azar';
}

/// Modelo de la tablet (p. ej. «Samsung SM-T510»), para distinguir sesiones en «Sesiones de dispositivos».
Future<String> _nombreDispositivo() async {
  try {
    if (Platform.isAndroid) {
      final info = await DeviceInfoPlugin().androidInfo;
      return '${info.manufacturer} ${info.model}'.trim();
    }
  } catch (_) {}
  return 'Android';
}

const _canalMovil = MethodChannel('mantpro/movil');

/// Identificador del dispositivo (ANDROID_ID, por canal nativo); si no se puede leer, uno aleatorio guardado.
Future<String> _idMovil() async {
  try {
    final id = await _canalMovil.invokeMethod<String>('idMovil');
    if (id != null && id.isNotEmpty) return id;
  } catch (_) {}
  final prefs = await SharedPreferences.getInstance();
  var propio = prefs.getString('movil_id_propio');
  if (propio == null) {
    final azar = Random.secure();
    propio = 'i-${List.generate(16, (_) => azar.nextInt(16).toRadixString(16)).join()}';
    await prefs.setString('movil_id_propio', propio);
  }
  return propio;
}

class AuthService {
  static String? token;
  static String? nombre;
  static String? login;
  static int? usuarioId;

  static bool get autenticado => token != null && token!.isNotEmpty;

  // El token va en el almacenamiento seguro del sistema (Keystore de Android), no en SharedPreferences.
  static const _almacenSeguro = FlutterSecureStorage();

  static Future<void> cargar() async {
    final prefs = await SharedPreferences.getInstance();
    try {
      token = await _almacenSeguro.read(key: 'auth_token');
    } catch (_) {
      token = null;
    }
    nombre = prefs.getString('auth_nombre');
    login = prefs.getString('auth_login');
    usuarioId = prefs.getInt('auth_id');
  }

  static Map<String, String> cabeceras() => token != null ? {'Authorization': 'Bearer $token'} : {};

  /// Inicia sesión con un administrador. Devuelve el texto del error, o null si ha ido bien (la tablet
  /// queda con token y datos guardados, pero la puerta de entrada no cambia hasta [confirmarVinculacion]).
  static Future<String?> iniciarSesion(String ip, String usuario, String password) async {
    try {
      // Con ruta de nube: el PC si responde y, si no, la nube (sin ella no cambia nada).
      await RutasServidor.resolver();
      ip = (await SharedPreferences.getInstance()).getString(RutasServidor.claveActiva) ?? ip;
      final res = await http
          .post(
            Uri.parse('$esquemaPC://$ip/api/login'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode({
              'login': usuario,
              'password': password,
              'dispositivo': '${await _nombreDispositivo()} (Operarios)',
              'dispositivo_id': await _idMovil(),
            }),
          )
          .timeout(const Duration(seconds: 10));

      final datos = json.decode(res.body) as Map<String, dynamic>;
      if (res.statusCode == 200 && datos['status'] == 'ok') {
        final u = datos['usuario'] as Map<String, dynamic>;
        // Igual que usuarios.es_admin del servidor: si la lista de roles llega vacía (usuarios anteriores a los
        // roles múltiples), cuenta el rol principal «rol».
        var roles = (u['roles'] as List?)?.map((r) => r.toString()).toList() ?? <String>[];
        if (roles.isEmpty) roles = [u['rol']?.toString() ?? ''];
        // Solo un administrador vincula la tablet: si no lo es, se cierra la sesión que se acaba de abrir.
        if (!roles.contains('admin')) {
          try {
            await http.post(Uri.parse('$esquemaPC://$ip/api/logout'),
                headers: {'Authorization': 'Bearer ${datos['token']}'}).timeout(const Duration(seconds: 5));
          } catch (_) {}
          await _borrarSesion();
          return t('vinc_solo_admin');
        }
        final prefs = await SharedPreferences.getInstance();
        token = datos['token'];
        nombre = (u['nombre'] ?? u['login'] ?? '').toString();
        login = (u['login'] ?? '').toString();
        usuarioId = (u['id'] as num?)?.toInt();
        await _almacenSeguro.write(key: 'auth_token', value: token!);
        await prefs.setString('auth_nombre', nombre ?? '');
        await prefs.setString('auth_login', login ?? '');
        await prefs.setInt('auth_id', usuarioId ?? 0);
        await RutasServidor.marcarInicioSesion();
        return null;
      }
      if (datos['error'] == 'bloqueado') {
        return t('login_bloqueado').replaceAll('{min}', '${datos['minutos'] ?? 15}');
      }
      if (datos['error'] == 'movil_adjudicado') {
        return t('login_movil_adjudicado').replaceAll('{nombre}', '${datos['tecnico'] ?? ''}');
      }
      if (datos['error'] == 'limite_moviles') return t('login_limite_moviles');
      if (res.statusCode == 402 || res.statusCode >= 500) return t('login_nube_no_disponible');
      if (datos['error'] == 'credenciales') return t('login_error');
      return (datos['message'] ?? t('login_error')).toString();
    } catch (e) {
      if (await RutasServidor.hayNube()) return t('login_sin_conexion_nube');
      return t('login_sin_conexion');
    }
  }

  /// Da por buena la vinculación: la puerta de entrada pasa al quiosco.
  static void confirmarVinculacion() => sesionNotifier.value = true;

  static Future<void> _borrarSesion() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    try {
      await _almacenSeguro.delete(key: 'auth_token');
    } catch (_) {}
    await prefs.remove('auth_nombre');
    await prefs.remove('auth_login');
    await prefs.remove('auth_id');
    token = null;
    nombre = null;
    login = null;
    usuarioId = null;
  }

  /// Desvincula la tablet: avisa al servidor (si hay conexión) y borra el token. NO toca la cola de avisos.
  static Future<void> cerrarSesion({String? ip}) async {
    if (ip != null && token != null) {
      try {
        await http.post(Uri.parse('$esquemaPC://$ip/api/logout'), headers: cabeceras()).timeout(const Duration(seconds: 5));
      } catch (_) {}
    }
    await _borrarSesion();
    sesionNotifier.value = false;
  }
}
