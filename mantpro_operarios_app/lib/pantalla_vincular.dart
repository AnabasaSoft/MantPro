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

// Vinculación de la tablet: 1) escanear el QR del PC (trae también la ruta
// de MantPro Cloud) y 2) usuario y contraseña de un ADMINISTRADOR. Tras
// iniciar sesión se descarga la lista de usuarios y se entra en el quiosco.
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api.dart';
import 'boton_idioma.dart';
import 'conexion_segura.dart';
import 'i18n/strings.dart';
import 'pantalla_qr.dart';
import 'sincronizador.dart';
import 'tema.dart';

class PantallaVincular extends StatefulWidget {
  const PantallaVincular({super.key});
  @override
  State<PantallaVincular> createState() => _PantallaVincularState();
}

class _PantallaVincularState extends State<PantallaVincular> {
  final _usuario = TextEditingController();
  final _contrasena = TextEditingController();
  String? _ip;
  bool _trabajando = false;
  bool _oculta = true;
  // Texto ya traducido del error (o null) y, si hace falta, el paso en que se quedó la vinculación.
  String? _error;
  bool _sesionIniciada = false;

  @override
  void initState() {
    super.initState();
    SharedPreferences.getInstance().then((p) {
      if (mounted) setState(() => _ip = p.getString('pc_ip_url'));
    });
  }

  @override
  void dispose() {
    _usuario.dispose();
    _contrasena.dispose();
    super.dispose();
  }

  Future<void> _escanear() async {
    final leido = await Navigator.push<String>(context, MaterialPageRoute(builder: (_) => const PantallaQr()));
    final ruta = await guardarVinculacion(leido);
    if (ruta == null) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('pc_ip_url', ruta);
    if (mounted) setState(() { _ip = ruta; _error = null; });
  }

  Future<void> _entrar() async {
    if (_ip == null) {
      setState(() => _error = t('login_sin_pc'));
      return;
    }
    if (_usuario.text.trim().isEmpty || _contrasena.text.isEmpty) {
      setState(() => _error = t('login_vacio'));
      return;
    }
    setState(() { _trabajando = true; _error = null; });
    final error = await AuthService.iniciarSesion(_ip!, _usuario.text.trim(), _contrasena.text);
    if (!mounted) return;
    if (error != null) {
      setState(() { _trabajando = false; _error = error; });
      return;
    }
    _sesionIniciada = true;
    await _descargarYEntrar();
  }

  /// Sincronización completa (baja la lista de usuarios). Si falla, se muestra el error y se puede reintentar.
  Future<void> _descargarYEntrar() async {
    setState(() { _trabajando = true; _error = null; });
    // Con avisos en la cola, primero solo se baja la lista de usuarios: nada se envía antes de decidir.
    final fallo = await Sincronizador.sincronizar(manual: true, soloDescargar: true);
    if (!mounted) return;
    if (fallo != null) {
      final detalle = switch (fallo) {
        'sin_conexion' => t('vinc_fallo_sin_conexion'),
        'sesion_caducada' => t('op_sesion_caducada'),
        'sin_usuarios' => t('vinc_fallo_sin_usuarios'),
        _ => t('vinc_fallo_servidor'),
      };
      setState(() { _trabajando = false; _error = t('vinc_error_sync').replaceAll('{error}', detalle); });
      return;
    }
    // ¿Hay avisos sin enviar de otra vinculación (otro PC u otra empresa)? Se pregunta qué hacer con ellos.
    final pendientes = Sincronizador.cola.value.length;
    if (pendientes > 0 && await Sincronizador.esOtraVinculacion()) {
      if (!mounted) return;
      final enviar = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        barrierColor: colorFondoDialogo,
        builder: (ctx) => AlertDialog(
          content: Text(t('vinc_avisos_anteriores').replaceAll('{n}', '$pendientes')),
          actions: [
            ElevatedButton(onPressed: () => Navigator.pop(ctx, true), child: Text(t('btn_enviar'))),
            ElevatedButton(
              onPressed: () => Navigator.pop(ctx, false),
              style: ElevatedButton.styleFrom(backgroundColor: colorRojo, foregroundColor: Colors.white),
              child: Text(t('btn_borrar')),
            ),
          ],
        ),
      );
      if (enviar == false) await Sincronizador.borrarCola();
    }
    await Sincronizador.olvidarVinculacionAnterior();
    AuthService.confirmarVinculacion();
    unawaited(Sincronizador.sincronizar());
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: idiomaNotifier,
      builder: (context, _, _) {
        final k = TokensTema.de(context);
        return Scaffold(
          body: SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 480),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Align(alignment: Alignment.centerRight, child: BotonIdioma()),
                      Center(child: Image.asset('assets/icono.png', width: 96, height: 96)),
                      const SizedBox(height: 12),
                      Text(t('app_titulo'),
                          textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 1.6 * rem, fontWeight: FontWeight.bold, color: k.texto)),
                      const SizedBox(height: 8),
                      Text(t('vinc_explicacion'),
                          textAlign: TextAlign.center, style: TextStyle(fontSize: tamBase, color: k.textoSuave)),
                      const SizedBox(height: 24),
                      Text(t('vinc_paso1'), style: const TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      OutlinedButton.icon(
                        onPressed: _trabajando ? null : _escanear,
                        icon: const Icon(Icons.qr_code_scanner),
                        label: Text(t('vinc_btn_escanear')),
                      ),
                      if (_ip != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 6),
                          child: Text(t('vinc_pc_vinculado').replaceAll('{ruta}', _ip!),
                              style: TextStyle(fontSize: 13, color: k.textoSuave)),
                        ),
                      const SizedBox(height: 20),
                      Text(t('vinc_paso2'), style: const TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _usuario,
                        enabled: !_trabajando && !_sesionIniciada,
                        autocorrect: false,
                        textInputAction: TextInputAction.next,
                        decoration: InputDecoration(labelText: t('login_usuario'), border: const OutlineInputBorder()),
                      ),
                      const SizedBox(height: 10),
                      TextField(
                        controller: _contrasena,
                        enabled: !_trabajando && !_sesionIniciada,
                        obscureText: _oculta,
                        onSubmitted: (_) => _entrar(),
                        decoration: InputDecoration(
                          labelText: t('login_password'),
                          border: const OutlineInputBorder(),
                          suffixIcon: IconButton(
                            icon: Icon(_oculta ? Icons.visibility : Icons.visibility_off),
                            onPressed: () => setState(() => _oculta = !_oculta),
                          ),
                        ),
                      ),
                      if (_error != null)
                        Container(
                          margin: const EdgeInsets.only(top: 12),
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                          decoration: BoxDecoration(color: k.errorFondo, borderRadius: BorderRadius.circular(4)),
                          child: Text(_error!, style: TextStyle(color: k.error)),
                        ),
                      const SizedBox(height: 16),
                      if (_trabajando)
                        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                          const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5)),
                          const SizedBox(width: 12),
                          Flexible(child: Text(_sesionIniciada ? t('vinc_descargando') : t('vinc_entrando'))),
                        ])
                      else
                        FilledButton(
                          onPressed: _sesionIniciada ? _descargarYEntrar : _entrar,
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            child: Text(_sesionIniciada ? t('btn_reintentar') : t('vinc_btn_vincular')),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
