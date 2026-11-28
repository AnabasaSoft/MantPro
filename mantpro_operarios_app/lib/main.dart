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

import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'actualizador.dart';
import 'api.dart';
import 'conexion_segura.dart';
import 'i18n/strings.dart';
import 'pantalla_quiosco.dart';
import 'pantalla_vincular.dart';
import 'rutas_servidor.dart';
import 'sincronizador.dart';
import 'tema.dart';

// --- COMPROBADOR DE ACTUALIZACIONES (GitHub Releases) ---
// IMPORTANTE: sube este número cada vez que publiques un nuevo release en GitHub (tag vX.Y.Z),
// así la app sabrá que la instalada se ha quedado atrás. Comparte repositorio con MantPro.
// Al compilar en GitHub se sustituye por la versión del tag; compilada desde el
// código (en local) se queda así, igual que el PC, y no busca actualizaciones.
const String kAppVersion = 'Dev Version';
const String kRepoOwner = 'AnabasaSoft';
const String kRepoName = 'MantPro';

/// Compara dos versiones tipo "1.2.3" (o "v1.2.3"): <0 si a es más antigua que b, 0 si son iguales, >0 si es más nueva.
/// Admite el prefijo "v" y sufijos de versión de pruebas ("3.10.2-dev1",
/// "3.10.2-rc.1"): se compara la parte numérica y, si es igual, la versión
/// final va por delante de sus versiones de pruebas (antes "2-dev1" se leía
/// como 0, y una versión de pruebas creía ser la 3.10.0).
/// Clave ordenable de una versión: parte numérica, luego si es final (va por
/// delante de sus versiones de pruebas) y, entre versiones de pruebas del mismo
/// número, su etiqueta y su número: 3.10.2-dev < 3.10.2-dev.1 < 3.10.2-dev.3 <
/// 3.10.2-beta < 3.10.2-rc.1 < 3.10.2. Igual que clave_version() en el PC.
List<int> _claveVersion(String v) {
  const ordenPruebas = {'dev': 0, 'alpha': 1, 'a': 1, 'beta': 2, 'b': 2, 'rc': 3};
  final limpia = v.trim().replaceFirst(RegExp(r'^[vV]'), '');
  final guion = limpia.indexOf('-');
  final numeros = guion < 0 ? limpia : limpia.substring(0, guion);
  final partes = numeros.split('.').map((s) => int.tryParse(s.trim()) ?? 0).take(3).toList();
  while (partes.length < 3) { partes.add(0); }
  if (guion < 0) return [...partes, 1, 0, 0];
  final sufijo = limpia.substring(guion + 1).toLowerCase();
  final etiqueta = sufijo.replaceAll(RegExp(r'[^a-z]'), '');
  final numero = RegExp(r'\d+').firstMatch(sufijo)?.group(0);
  return [...partes, 0, ordenPruebas[etiqueta] ?? 0, int.tryParse(numero ?? '') ?? 0];
}

int _compararVersiones(String a, String b) {
  final ka = _claveVersion(a), kb = _claveVersion(b);
  for (int i = 0; i < ka.length; i++) {
    if (ka[i] != kb[i]) return ka[i].compareTo(kb[i]);
  }
  return 0;
}

/// Release más nueva de la lista de GitHub. A quien tiene una versión estable
/// solo se le ofrecen estables; a quien ya tiene instalada una versión de
/// pruebas (-dev, -beta, -rc…), también las de pruebas. («releases/latest» de
/// GitHub nunca devuelve pre-releases, por eso se pide la lista.)
Map<String, dynamic>? _releaseMasNueva(List<dynamic> releases) {
  final aceptaPruebas = kAppVersion.contains('-');
  Map<String, dynamic>? mejor;
  for (final r in releases.whereType<Map<String, dynamic>>()) {
    final tag = (r['tag_name'] ?? '').toString();
    if (tag.isEmpty || r['draft'] == true || (r['prerelease'] == true && !aceptaPruebas)) continue;
    if (mejor == null || _compararVersiones(tag, mejor['tag_name'].toString()) > 0) mejor = r;
  }
  return mejor;
}

Future<void> comprobarActualizacionGitHub(BuildContext context, {bool forzar = false}) async {
  // Compilada desde el código (no desde un tag): su versión no es real y
  // siempre parecería desactualizada, así que no se busca nada.
  if (!RegExp(r'^\d').hasMatch(kAppVersion)) {
    if (forzar && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t("msg_actualizaciones_codigo_fuente"))));
    }
    return;
  }
  final prefs = await SharedPreferences.getInstance();
  if (!forzar) {
    final ultima = prefs.getInt('update_ultima_comprobacion') ?? 0;
    if (DateTime.now().millisecondsSinceEpoch - ultima < const Duration(hours: 24).inMilliseconds) return;
  }
  try {
    final res = await http.get(
      Uri.parse('https://api.github.com/repos/$kRepoOwner/$kRepoName/releases?per_page=30'),
      headers: {'Accept': 'application/vnd.github+json'},
    ).timeout(const Duration(seconds: 6));
    await prefs.setInt('update_ultima_comprobacion', DateTime.now().millisecondsSinceEpoch);
    if (res.statusCode != 200) { if (forzar && context.mounted) _mostrarSnackSinNovedad(context, error: true); return; }
    final data = _releaseMasNueva(json.decode(res.body) as List<dynamic>) ?? {};
    final String tag = (data['tag_name'] ?? '').toString();
    final String notas = (data['body'] ?? '').toString();
    if (tag.isEmpty) return;
    if (_compararVersiones(tag, kAppVersion) <= 0) { if (forzar && context.mounted) _mostrarSnackSinNovedad(context, error: false); return; }
    final descartada = prefs.getString('update_descartada');
    if (!forzar && descartada == tag) return;
    if (!context.mounted) return;
    showDialog(context: context, barrierDismissible: true, builder: (ctx) => AlertDialog(
      title: Text(t("msg_nueva_version_titulo")),
      content: SingleChildScrollView(child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
        Text(t("msg_nueva_version_cuerpo").replaceAll('{actual}', kAppVersion).replaceAll('{nueva}', tag)),
        if (notas.trim().isNotEmpty) ...[const SizedBox(height: 10), Text(notas.trim(), style: const TextStyle(fontSize: 12, color: Colors.grey))],
      ])),
      actions: [
        TextButton(onPressed: () async { await prefs.setString('update_descartada', tag); if (ctx.mounted) Navigator.pop(ctx); }, child: Text(t("btn_luego"))),
        // Descarga el APK y abre el instalador de Android (antes llevaba a GitHub).
        ElevatedButton.icon(icon: const Icon(Icons.system_update), label: Text(t("btn_actualizar")), onPressed: () {
          Navigator.pop(ctx);
          descargarEInstalar(context, data, 'MantProOperarios.apk');
        }),
      ],
    ));
  } catch (e) { if (forzar && context.mounted) _mostrarSnackSinNovedad(context, error: true); } // sin conexión o GitHub caído: no molestamos
}

void _mostrarSnackSinNovedad(BuildContext context, {required bool error}) {
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error ? t("msg_sin_actualizaciones_sin_conexion") : t("msg_ya_ultima_version").replaceAll('{version}', kAppVersion))));
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Conexión cifrada con el PC (ver conexion_segura.dart): antes de cualquier petición.
  await iniciarConexionSegura();
  final prefs = await SharedPreferences.getInstance();
  final ipGuardada = prefs.getString('pc_ip_url');
  if (ipGuardada != null && ipGuardada.isNotEmpty) await migrarAHttps(ipGuardada);
  // Rutas del PC y de la nube: se recuerda la activa y se vuelve a decidir sin esperar (la app es offline).
  await RutasServidor.cargar();
  unawaited(RutasServidor.resolver(forzar: true));
  await cargarIdiomaGuardado();
  temaOscuroNotifier.value = prefs.getBool('tema_oscuro') ?? true;
  await AuthService.cargar();
  await Sincronizador.cargar();
  await Sincronizador.limpiarHuerfanas();
  sesionNotifier.value = AuthService.autenticado;
  // Pantalla inmersiva: la tablet fija en el taller no enseña las barras del sistema.
  await SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  runApp(const MyApp());
  // Enviar lo pendiente al arrancar y cada 30 s mientras la app esté abierta.
  Sincronizador.iniciarPeriodico();
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: idiomaNotifier,
      builder: (context, idioma, _) => ValueListenableBuilder<bool>(
        valueListenable: temaOscuroNotifier,
        builder: (context, oscuro, _) => MaterialApp(
          title: t('app_titulo'),
          debugShowCheckedModeBanner: false,
          theme: construirTema(oscuro),
          locale: Locale(idioma),
          supportedLocales: [for (final i in idiomasDisponibles) Locale(i['codigo']!)],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: const PuertaEntrada(),
        ),
      ),
    );
  }
}

/// Sin token, la vinculación; con token, el quiosco (que funciona sin red con lo guardado).
class PuertaEntrada extends StatelessWidget {
  const PuertaEntrada({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<bool>(
      valueListenable: sesionNotifier,
      builder: (context, haySesion, _) => haySesion ? const PantallaQuiosco() : const PantallaVincular(),
    );
  }
}
