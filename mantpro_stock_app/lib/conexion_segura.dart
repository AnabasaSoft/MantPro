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

/// Conexión cifrada (HTTPS) con el PC.
///
/// El PC usa un certificado propio, que ninguna autoridad avala: el móvil
/// confía en él porque su huella SHA-256 le llega en el QR de vinculación y
/// la compara en cada conexión («pinning»). Así nadie en la WiFi puede leer
/// el tráfico ni hacerse pasar por el PC.
///
/// Los móviles vinculados con una versión anterior (QR sin huella, por HTTP)
/// pasan solos a HTTPS la primera vez que conectan ([migrarAHttps]).
///
/// Este fichero es igual en mantenimiento_app y mantpro_stock_app.
library;

import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'rutas_servidor.dart';

/// «https» si el PC vinculado tiene huella guardada; «http» si no (PC con
/// una versión anterior de MantPro). Se usa en todas las direcciones del
/// PC: "$esquemaPC://$ip/api/...".
String esquemaPC = 'http';

/// Huella SHA-256 (hexadecimal) del certificado del PC vinculado.
String? huellaPC;

const _claveHuella = 'pc_huella';

/// Acepta el certificado del PC solo si su huella coincide con la guardada.
class _FijacionCertificado extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context)
      ..badCertificateCallback = (X509Certificate cert, String host, int port) =>
          huellaPC != null && sha256.convert(cert.der).toString() == huellaPC;
  }
}

/// Llamar al arrancar la app, antes de cualquier conexión con el PC: vale
/// para todo (http, Image.network...), porque todos crean su HttpClient.
Future<void> iniciarConexionSegura() async {
  HttpOverrides.global = _FijacionCertificado();
  final prefs = await SharedPreferences.getInstance();
  huellaPC = prefs.getString(_claveHuella);
  esquemaPC = huellaPC == null ? 'http' : 'https';
}

/// Guarda el PC leído del QR y devuelve su dirección ("ip:puerto") para
/// guardarla en 'pc_ip_url'. Admite el QR nuevo
/// (https://ip:puerto/?h=HUELLA&p=puertoHttp) y el de versiones anteriores
/// del PC (http://ip:puerto).
Future<String?> guardarVinculacion(String? leido) async {
  if (leido == null || leido.trim().isEmpty) return null;
  final prefs = await SharedPreferences.getInstance();
  final uri = Uri.tryParse(leido.trim());
  final huella = uri?.queryParameters['h'];
  if (uri != null && uri.scheme == 'https' && huella != null && huella.length == 64) {
    huellaPC = huella.toLowerCase();
    esquemaPC = 'https';
    await prefs.setString(_claveHuella, huellaPC!);
    final ruta = '${uri.host}:${uri.port}';
    // El QR puede llevar también la ruta de la nube (&n=dominio&e=empresa): se guardan las dos.
    await RutasServidor.guardar(pc: ruta, nube: rutaNubeDelQr(uri));
    return ruta;
  }
  // QR antiguo: sin cifrar hasta que el PC se actualice ([migrarAHttps]).
  huellaPC = null;
  esquemaPC = 'http';
  await prefs.remove(_claveHuella);
  final ruta = leido.trim().replaceAll('http://', '').replaceAll('/', '');
  await RutasServidor.guardar(pc: ruta);       // QR antiguo: solo el PC, y se olvida cualquier ruta de nube anterior
  return ruta;
}

/// Ruta de MantPro Cloud que lleva el QR del PC (`&n=dominio&e=empresa`): «dominio/m/empresa», o null si
/// el QR no la lleva o trae algo que no vale (solo se admiten un dominio y un uuid de 32 hexadecimales).
String? rutaNubeDelQr(Uri uri) {
  final n = uri.queryParameters['n'];
  final e = uri.queryParameters['e'];
  if (n == null || e == null) return null;
  if (!RegExp(r'^[A-Za-z0-9.:-]{1,100}$').hasMatch(n) || !RegExp(r'^[0-9a-f]{32}$').hasMatch(e)) return null;
  return '$n/m/$e';
}

/// Si el móvil sigue por HTTP con un PC que ya tiene HTTPS, pasa a HTTPS:
/// pide al PC su puerto y su huella, comprueba que la conexión cifrada
/// funciona y guarda la nueva dirección. Devuelve la dirección a usar a
/// partir de ahora (la misma si no ha cambiado nada).
Future<String> migrarAHttps(String ip) async {
  if (esquemaPC == 'https') return ip;
  try {
    // Primero, una comprobación rápida de que el PC está a mano: sin
    // conexión (lo normal en el taller) no se hace esperar al arranque.
    final host0 = ip.contains(':') ? ip.substring(0, ip.lastIndexOf(':')) : ip;
    final puerto0 = int.tryParse(ip.contains(':') ? ip.substring(ip.lastIndexOf(':') + 1) : '') ?? 80;
    final prueba = await Socket.connect(host0, puerto0, timeout: const Duration(milliseconds: 800));
    prueba.destroy();
    final res = await http.get(Uri.parse('http://$ip/api/tls')).timeout(const Duration(seconds: 4));
    if (res.statusCode != 200) return ip;
    final datos = json.decode(res.body);
    final huella = (datos['huella'] ?? '').toString().toLowerCase();
    final puerto = datos['puerto'];
    if (huella.length != 64 || puerto is! int) return ip;
    final host = ip.contains(':') ? ip.substring(0, ip.lastIndexOf(':')) : ip;
    final nueva = '$host:$puerto';
    final anterior = huellaPC;
    huellaPC = huella;
    try {
      final ping = await http.get(Uri.parse('https://$nueva/api/ping')).timeout(const Duration(seconds: 4));
      if (ping.statusCode != 200) { huellaPC = anterior; return ip; }
    } catch (_) {
      huellaPC = anterior;
      return ip;
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_claveHuella, huella);
    await prefs.setString('pc_ip_url', nueva);
    esquemaPC = 'https';
    return nueva;
  } catch (_) {
    return ip;
  }
}
