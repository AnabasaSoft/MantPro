// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// MantPro Stock - Gestión de almacén
// Copyright (C) 2026 AnabasaSoft <anabasasoft@gmail.com>
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
import 'package:http/http.dart' as http;
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import 'i18n/strings.dart';
import 'api.dart';
import 'sincronizador.dart';
import 'pantallas/pantalla_almacen.dart';
import 'pantallas/pantalla_buscar.dart';
import 'pantallas/pantalla_bajo_minimo.dart';

// --- GESTOR DE TEMA GLOBAL ---
final ValueNotifier<ThemeMode> themeNotifier = ValueNotifier(ThemeMode.dark);

// --- COMPROBADOR DE ACTUALIZACIONES (GitHub Releases) ---
// IMPORTANTE: sube este número cada vez que publiques un nuevo release en GitHub (tag vX.Y.Z),
// así la app sabrá que la instalada se ha quedado atrás. Comparte repositorio con MantPro.
const String kAppVersion = '3.7.3';
const String kRepoOwner = 'AnabasaSoft';
const String kRepoName = 'MantPro';

int _compararVersiones(String a, String b) {
  List<int> parse(String v) => v.trim().replaceFirst(RegExp(r'^[vV]'), '').split('.').map((s) => int.tryParse(s.trim()) ?? 0).toList();
  final pa = parse(a), pb = parse(b);
  for (int i = 0; i < 3; i++) {
    final va = i < pa.length ? pa[i] : 0;
    final vb = i < pb.length ? pb[i] : 0;
    if (va != vb) return va.compareTo(vb);
  }
  return 0;
}

Future<void> comprobarActualizacionGitHub(BuildContext context, {bool forzar = false}) async {
  final prefs = await SharedPreferences.getInstance();
  if (!forzar) {
    final ultima = prefs.getInt('update_ultima_comprobacion') ?? 0;
    if (DateTime.now().millisecondsSinceEpoch - ultima < const Duration(hours: 24).inMilliseconds) return;
  }
  try {
    final res = await http.get(
      Uri.parse('https://api.github.com/repos/$kRepoOwner/$kRepoName/releases/latest'),
      headers: {'Accept': 'application/vnd.github+json'},
    ).timeout(const Duration(seconds: 6));
    await prefs.setInt('update_ultima_comprobacion', DateTime.now().millisecondsSinceEpoch);
    if (res.statusCode != 200) return;
    final data = json.decode(res.body);
    final String tag = (data['tag_name'] ?? '').toString();
    final String urlRelease = (data['html_url'] ?? 'https://github.com/$kRepoOwner/$kRepoName/releases').toString();
    final String notas = (data['body'] ?? '').toString();
    if (tag.isEmpty) return;
    if (_compararVersiones(tag, kAppVersion) <= 0) return;
    final descartada = prefs.getString('update_descartada');
    if (!forzar && descartada == tag) return;
    if (!context.mounted) return;
    showDialog(context: context, barrierDismissible: true, builder: (ctx) => AlertDialog(
      title: const Text("🚀 Nueva versión disponible"),
      content: SingleChildScrollView(child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
        Text("Tienes la versión $kAppVersion instalada y en GitHub ya está la $tag."),
        if (notas.trim().isNotEmpty) ...[const SizedBox(height: 10), Text(notas.trim(), style: const TextStyle(fontSize: 12, color: Colors.grey))],
      ])),
      actions: [
        TextButton(onPressed: () async { await prefs.setString('update_descartada', tag); if (ctx.mounted) Navigator.pop(ctx); }, child: const Text("Luego")),
        ElevatedButton.icon(icon: const Icon(Icons.download), label: const Text("Descargar"), onPressed: () async { await launchUrl(Uri.parse(urlRelease), mode: LaunchMode.externalApplication); if (ctx.mounted) Navigator.pop(ctx); }),
      ],
    ));
  } catch (_) {} // sin conexión o GitHub caído: no molestamos
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  final bool isDark = prefs.getBool('is_dark_mode') ?? true;
  themeNotifier.value = isDark ? ThemeMode.dark : ThemeMode.light;
  await cargarIdiomaGuardado();
  await AuthService.cargar();
  sesionNotifier.value = AuthService.autenticado;
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: idiomaNotifier,
      builder: (_, idiomaActual, __) {
        return ValueListenableBuilder<ThemeMode>(
          valueListenable: themeNotifier,
          builder: (_, mode, __) {
            return MaterialApp(
              home: const AuthGate(),
              debugShowCheckedModeBanner: false,
              title: "MantPro Stock",
              themeMode: mode,
              theme: ThemeData.light().copyWith(
                scaffoldBackgroundColor: const Color(0xFFF5F5F5),
                appBarTheme: const AppBarTheme(backgroundColor: Color(0xFF37474F), foregroundColor: Colors.white),
                cardColor: Colors.white,
                colorScheme: const ColorScheme.light(primary: Color(0xFF37474F), secondary: Colors.orangeAccent),
                bottomNavigationBarTheme: const BottomNavigationBarThemeData(backgroundColor: Color(0xFF37474F), selectedItemColor: Colors.white, unselectedItemColor: Colors.white60),
              ),
              darkTheme: ThemeData.dark().copyWith(
                scaffoldBackgroundColor: const Color(0xFF121212),
                appBarTheme: const AppBarTheme(backgroundColor: Color(0xFF1F1F1F), foregroundColor: Colors.white),
                cardColor: const Color(0xFF2C2C2C),
                dividerColor: Colors.grey[700],
                colorScheme: const ColorScheme.dark(primary: Color(0xFF90CAF9), secondary: Colors.orangeAccent, surface: Color(0xFF2C2C2C)),
                bottomNavigationBarTheme: const BottomNavigationBarThemeData(backgroundColor: Color(0xFF1F1F1F), selectedItemColor: Color(0xFF90CAF9), unselectedItemColor: Colors.grey),
              ),
            );
          },
        );
      },
    );
  }
}

// ==========================================================================
// PANTALLAS DE ACCESO
// ==========================================================================
class AuthGate extends StatefulWidget {
  const AuthGate({super.key});
  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  bool _cargando = true;
  String? _ip;

  @override
  void initState() {
    super.initState();
    _preparar();
  }

  Future<void> _preparar() async {
    final prefs = await SharedPreferences.getInstance();
    await AuthService.cargar();
    if (!mounted) return;
    setState(() {
      _ip = prefs.getString('pc_ip_url');
      _cargando = false;
    });
    sesionNotifier.value = AuthService.autenticado;
  }

  Future<void> _vincular() async {
    final c = await Navigator.push(
        context, MaterialPageRoute(builder: (_) => const QRScanScreen()));
    if (c != null) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('pc_ip_url', c);
      if (mounted) setState(() => _ip = c);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_cargando) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return ValueListenableBuilder<bool>(
      valueListenable: sesionNotifier,
      builder: (context, haySesion, _) {
        if (haySesion) return const MainScreen();
        return LoginScreen(ip: _ip, onVincular: _vincular);
      },
    );
  }
}

class LoginScreen extends StatefulWidget {
  final String? ip;
  final VoidCallback onVincular;
  const LoginScreen({super.key, required this.ip, required this.onVincular});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usuario = TextEditingController();
  final _password = TextEditingController();
  bool _cargando = false;
  bool _oculta = true;
  String? _error;

  @override
  void dispose() {
    _usuario.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _entrar() async {
    if (widget.ip == null) {
      setState(() => _error = tt('login_sin_pc',
          'Primero vincula el móvil con el PC escaneando el QR.'));
      return;
    }
    if (_usuario.text.trim().isEmpty || _password.text.isEmpty) {
      setState(() => _error = tt('login_vacio', 'Introduce usuario y contraseña.'));
      return;
    }
    setState(() { _cargando = true; _error = null; });
    final error = await AuthService.iniciarSesion(
        widget.ip!, _usuario.text.trim(), _password.text);
    if (!mounted) return;
    setState(() { _cargando = false; _error = error; });
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.warehouse, size: 88, color: tema.colorScheme.primary),
                const SizedBox(height: 16),
                Text(tt('app_titulo', 'MantPro Stock'), style: tema.textTheme.headlineSmall),
                const SizedBox(height: 4),
                Text(
                  tt('login_subtitulo', 'Identifícate para gestionar el almacén'),
                  style: tema.textTheme.bodySmall,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 28),
                TextField(
                  controller: _usuario,
                  autocorrect: false,
                  textInputAction: TextInputAction.next,
                  decoration: InputDecoration(
                    labelText: tt('login_usuario', 'Usuario'),
                    prefixIcon: const Icon(Icons.person_outline),
                    border: const OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _password,
                  obscureText: _oculta,
                  onSubmitted: (_) => _entrar(),
                  decoration: InputDecoration(
                    labelText: tt('login_password', 'Contraseña'),
                    prefixIcon: const Icon(Icons.lock_outline),
                    border: const OutlineInputBorder(),
                    suffixIcon: IconButton(
                      icon: Icon(_oculta ? Icons.visibility : Icons.visibility_off),
                      onPressed: () => setState(() => _oculta = !_oculta),
                    ),
                  ),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!,
                      style: TextStyle(color: tema.colorScheme.error),
                      textAlign: TextAlign.center),
                ],
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed: _cargando ? null : _entrar,
                    child: _cargando
                        ? const SizedBox(width: 20, height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2))
                        : Text(tt('login_entrar', 'ENTRAR')),
                  ),
                ),
                const SizedBox(height: 12),
                TextButton.icon(
                  onPressed: _cargando ? null : widget.onVincular,
                  icon: const Icon(Icons.qr_code_scanner),
                  label: Text(widget.ip == null
                      ? tt('btn_vincular_pc', 'Vincular PC')
                      : tt('btn_vincular_otro_pc', 'Vincular otro PC')),
                ),
                Text(
                  widget.ip == null
                      ? tt('login_pc_no_vinculado', 'Sin PC vinculado')
                      : 'PC: ${widget.ip}',
                  style: tema.textTheme.bodySmall?.copyWith(color: Colors.grey),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class QRScanScreen extends StatefulWidget {
  const QRScanScreen({super.key});
  @override
  State<QRScanScreen> createState() => _QRScanScreenState();
}

class _QRScanScreenState extends State<QRScanScreen> {
  bool _s = false;
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(t("title_qr"))),
      body: MobileScanner(onDetect: (c) {
        if (!_s && c.barcodes.isNotEmpty && c.barcodes.first.rawValue != null) {
          setState(() => _s = true);
          Navigator.pop(context,
              c.barcodes.first.rawValue!.replaceAll("http://", "").replaceAll("/", ""));
        }
      }),
    );
  }
}

// ==========================================================================
// PANTALLA PRINCIPAL: Almacén / Buscar / Bajo mínimo
// ==========================================================================
class MainScreen extends StatefulWidget {
  const MainScreen({super.key});
  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _indiceActual = 0;
  late final List<Widget> _pantallas;
  Timer? _timerSincronizacion;

  @override
  void initState() {
    super.initState();
    _pantallas = const [
      PantallaAlmacen(),
      PantallaBuscar(),
      PantallaBajoMinimo(),
    ];
    WidgetsBinding.instance.addPostFrameCallback((_) => comprobarActualizacionGitHub(context));
    _sincronizarAlArrancar();
    // Mientras la app está abierta, reintenta enviar lo pendiente y refresca
    // los roles del usuario, para detectar sin reconectar cambios hechos
    // desde el PC (p.ej. que le den permiso de almacén a un técnico).
    _timerSincronizacion = Timer.periodic(const Duration(seconds: 25), (_) => _sincronizarPeriodico());
  }

  @override
  void dispose() {
    _timerSincronizacion?.cancel();
    super.dispose();
  }

  Future<void> _sincronizarAlArrancar() async {
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString('pc_ip_url');
    if (ip == null || !AuthService.autenticado) return;
    try {
      await StockSincronizador.sincronizarTodo(ip);
    } catch (_) {
      // Sin conexión con el PC: se sigue trabajando con la caché local.
    }
  }

  Future<void> _sincronizarPeriodico() async {
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString('pc_ip_url');
    if (ip == null || !AuthService.autenticado) return;
    try {
      await StockSincronizador.sincronizarTodo(ip, silencioso: true);
    } catch (_) {}
  }

  Future<void> _cerrarSesion() async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(tt('btn_cerrar_sesion', 'Cerrar sesión')),
        content: Text(tt('msg_cerrar_sesion', '¿Seguro que quieres cerrar la sesión?')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(t('btn_no'))),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: Text(t('btn_si'))),
        ],
      ),
    );
    if (confirmar != true) return;
    final prefs = await SharedPreferences.getInstance();
    await AuthService.cerrarSesion(ip: prefs.getString('pc_ip_url'));
  }

  void _toggleTheme() async {
    final prefs = await SharedPreferences.getInstance();
    bool nuevoModo = themeNotifier.value != ThemeMode.dark;
    themeNotifier.value = nuevoModo ? ThemeMode.dark : ThemeMode.light;
    await prefs.setBool('is_dark_mode', nuevoModo);
  }

  void _mostrarSelectorIdioma() {
    showDialog(
      context: context,
      builder: (ctx) => SimpleDialog(
        title: Text(t('dlg_idioma_titulo')),
        children: idiomasDisponibles.map((idioma) {
          return SimpleDialogOption(
            onPressed: () {
              cambiarIdioma(idioma['codigo']!);
              Navigator.pop(ctx);
            },
            child: Text(idioma['nombre']!),
          );
        }).toList(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    bool isDark = Theme.of(context).brightness == Brightness.dark;
    return ValueListenableBuilder<String>(
      valueListenable: idiomaNotifier,
      builder: (context, idiomaActual, _) {
        final titulos = [
          t("tab_almacen"),
          t("tab_buscar"),
          t("tab_bajo_minimo"),
        ];
        return Scaffold(
          appBar: AppBar(title: Text(titulos[_indiceActual]), actions: [
            IconButton(icon: const Icon(Icons.language), onPressed: _mostrarSelectorIdioma),
            IconButton(icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode), onPressed: _toggleTheme),
            PopupMenuButton<String>(
              icon: const Icon(Icons.account_circle),
              tooltip: AuthService.nombre ?? '',
              onSelected: (v) { if (v == 'salir') _cerrarSesion(); },
              itemBuilder: (_) => [
                PopupMenuItem<String>(
                  enabled: false,
                  child: Text('👤 ${AuthService.nombre ?? ''}',
                      style: const TextStyle(fontWeight: FontWeight.bold)),
                ),
                PopupMenuItem<String>(
                  value: 'salir',
                  child: Text(tt('btn_cerrar_sesion', 'Cerrar sesión')),
                ),
              ],
            ),
          ]),
          body: IndexedStack(index: _indiceActual, children: _pantallas),
          bottomNavigationBar: BottomNavigationBar(
            currentIndex: _indiceActual,
            type: BottomNavigationBarType.fixed,
            onTap: (index) => setState(() => _indiceActual = index),
            items: [
              BottomNavigationBarItem(icon: const Icon(Icons.warehouse), label: t("tab_almacen")),
              BottomNavigationBarItem(icon: const Icon(Icons.search), label: t("tab_buscar")),
              BottomNavigationBarItem(icon: const Icon(Icons.warning_amber), label: t("tab_bajo_minimo")),
            ],
          ),
        );
      },
    );
  }
}
