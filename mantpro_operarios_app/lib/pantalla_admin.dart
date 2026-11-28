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

// Panel de administración de la tablet (se abre con «🔒 Cerrar» y la
// contraseña del administrador): estado de la sincronización, sede, idioma,
// tema, actualizaciones y desvinculación.
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'formatos.dart';
import 'i18n/strings.dart';
import 'main.dart' show kAppVersion, comprobarActualizacionGitHub;
import 'modelos.dart';
import 'rutas_servidor.dart';
import 'sincronizador.dart';
import 'tema.dart';

class PantallaAdmin extends StatefulWidget {
  const PantallaAdmin({super.key});
  @override
  State<PantallaAdmin> createState() => _PantallaAdminState();
}

class _PantallaAdminState extends State<PantallaAdmin> {
  Timer? _reloj;

  // 120 s sin tocar la pantalla: vuelve sola al quiosco (que vuelve a fijar la pantalla).
  void _tocado() {
    _reloj?.cancel();
    _reloj = Timer(const Duration(seconds: 120), () {
      if (mounted) Navigator.of(context).maybePop();
    });
  }

  @override
  void dispose() {
    _reloj?.cancel();
    super.dispose();
  }

  // Sede de la tablet: null = ninguna (decide el servidor).
  int? _sedeId;
  // Resultado de la última sincronización lanzada desde aquí (clave de traducción) o null.
  String? _resultado;
  bool _resultadoBueno = false;

  @override
  void initState() {
    super.initState();
    _tocado();
    SharedPreferences.getInstance().then((p) {
      if (mounted) setState(() => _sedeId = p.getInt('sede_id'));
    });
  }

  Future<void> _elegirSede(int? id) async {
    final prefs = await SharedPreferences.getInstance();
    ElementoCatalogo? sede;
    for (final s in Sincronizador.sedes.value) {
      if (s.id == id) sede = s;
    }
    if (sede == null) {
      await prefs.remove('sede_id');
      await prefs.remove('sede_uuid');
    } else {
      await prefs.setInt('sede_id', sede.id);
      await prefs.setString('sede_uuid', sede.uuid);
    }
    if (mounted) setState(() => _sedeId = sede?.id);
  }

  Future<void> _sincronizar() async {
    setState(() => _resultado = null);
    final r = await Sincronizador.sincronizar(manual: true);
    if (!mounted) return;
    setState(() {
      _resultadoBueno = r == null;
      _resultado = switch (r) {
        null => 'adm_sync_ok',
        'sin_conexion' => 'op_sin_conexion',
        'sesion_caducada' => 'op_sesion_caducada',
        'sin_usuarios' => 'vinc_fallo_sin_usuarios',
        _ => 'adm_sync_error',
      };
    });
  }

  Future<void> _desvincular() async {
    final pendientes = Sincronizador.cola.value.length;
    final confirmar = await showDialog<bool>(
      context: context,
      barrierColor: colorFondoDialogo,
      builder: (ctx) => AlertDialog(
        title: Text(t('adm_desvincular')),
        content: Text([
          t('adm_desvincular_confirmar'),
          if (pendientes > 0) t('adm_desvincular_pendientes').replaceAll('{n}', '$pendientes'),
        ].join('\n\n')),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(backgroundColor: colorRojo, foregroundColor: Colors.white),
            child: Text(t('btn_desvincular')),
          ),
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(t('btn_cancelar'))),
        ],
      ),
    );
    if (confirmar != true || !mounted) return;
    final navegador = Navigator.of(context);
    // Cierra la sesión (avisa al servidor), borra token y datos descargados; la cola de avisos NO se borra.
    await Sincronizador.desvincularTablet();
    navegador.popUntil((r) => r.isFirst);
  }

  String _textoEstado(EstadoConexion e) => switch (e) {
        EstadoConexion.pc => t('op_conexion_pc'),
        EstadoConexion.nube => t('op_conexion_nube'),
        EstadoConexion.sinConexion => t('op_sin_conexion'),
        EstadoConexion.sesionCaducada => t('op_sesion_caducada'),
        EstadoConexion.desconocido => t('op_comprobando_conexion'),
      };

  String _textoMotivo(String motivo) {
    if (motivo == 'sin_permiso' || motivo == 'solo_admin') return t('adm_motivo_sin_permiso');
    if (motivo == 'titulo_obligatorio') return t('adm_motivo_titulo');
    final codigo = motivo.startsWith('http_') ? motivo.substring(5) : motivo;
    return t('adm_motivo_otro').replaceAll('{codigo}', codigo);
  }

  Widget _seccion(TokensTema k, String titulo, List<Widget> hijos) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(titulo, style: TextStyle(fontSize: 1.1 * rem, fontWeight: FontWeight.bold, color: k.texto)),
          const SizedBox(height: 8),
          ...hijos,
        ]),
      ),
    );
  }

  Widget _estado(TokensTema k) {
    return ListenableBuilder(
      listenable: Listenable.merge([
        Sincronizador.estado,
        Sincronizador.cola,
        Sincronizador.descartados,
        Sincronizador.ultimaCorrecta,
        RutasServidor.enNube,
      ]),
      builder: (context, _) {
        final idioma = idiomaNotifier.value;
        final ultima = Sincronizador.ultimaCorrecta.value;
        final descartados = Sincronizador.descartados.value;
        final estado = Sincronizador.estado.value;
        return _seccion(k, t('adm_estado'), [
          Text(_textoEstado(estado), style: TextStyle(color: estado == EstadoConexion.sesionCaducada ? k.error : k.texto)),
          const SizedBox(height: 4),
          Text(t('op_avisos_por_enviar').replaceAll('{n}', '${Sincronizador.cola.value.length}')),
          const SizedBox(height: 4),
          Text(ultima == null
              ? t('adm_nunca_sync')
              : t('adm_ultima_sync').replaceAll('{fecha}', formatearFechaHora(ultima, idioma))),
          if (descartados.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(t('adm_descartados'), style: TextStyle(fontWeight: FontWeight.bold, color: k.error)),
            const SizedBox(height: 4),
            for (final d in descartados)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  '• ${d['titulo']} (${d['usuario']}) - ${_textoMotivo('${d['motivo']}')}'
                  '${DateTime.tryParse('${d['fecha']}') != null ? ' - ${formatearFechaHora(DateTime.parse('${d['fecha']}'), idioma)}' : ''}',
                  style: TextStyle(color: k.textoSuave),
                ),
              ),
            Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton(onPressed: Sincronizador.borrarDescartados, child: Text(t('adm_borrar_lista'))),
            ),
          ],
        ]);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: idiomaNotifier,
      builder: (context, idioma, _) {
        final k = TokensTema.de(context);
        return Listener(
          behavior: HitTestBehavior.translucent,
          onPointerDown: (_) => _tocado(),
          child: Scaffold(
          appBar: AppBar(title: Text(t('adm_titulo'))),
          body: SafeArea(
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 720),
                child: ListView(padding: const EdgeInsets.all(16), children: [
                  FilledButton.icon(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.arrow_back),
                    label: Padding(padding: const EdgeInsets.symmetric(vertical: 10), child: Text(t('adm_volver'))),
                  ),
                  const SizedBox(height: 14),
                  _estado(k),
                  ValueListenableBuilder<bool>(
                    valueListenable: Sincronizador.sincronizando,
                    builder: (context, trabajando, _) => _seccion(k, t('adm_sincronizar'), [
                      Align(
                        alignment: Alignment.centerLeft,
                        child: FilledButton.icon(
                          onPressed: trabajando ? null : _sincronizar,
                          icon: trabajando
                              ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                              : const Icon(Icons.sync),
                          label: Text(trabajando ? t('adm_sincronizando') : t('adm_sincronizar')),
                        ),
                      ),
                      if (_resultado != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(t(_resultado!), style: TextStyle(color: _resultadoBueno ? colorVerde : k.error)),
                        ),
                    ]),
                  ),
                  ValueListenableBuilder<List<ElementoCatalogo>>(
                    valueListenable: Sincronizador.sedes,
                    builder: (context, sedes, _) {
                      if (sedes.length < 2) return const SizedBox.shrink();
                      final valor = sedes.any((s) => s.id == _sedeId) ? _sedeId : null;
                      return _seccion(k, t('adm_sede'), [
                        Text(t('adm_sede_ayuda'), style: TextStyle(color: k.textoSuave)),
                        const SizedBox(height: 8),
                        DropdownButton<int?>(
                          value: valor,
                          isExpanded: true,
                          items: [
                            DropdownMenuItem<int?>(value: null, child: Text(t('adm_sede_ninguna'))),
                            for (final s in sedes) DropdownMenuItem<int?>(value: s.id, child: Text(s.nombre)),
                          ],
                          onChanged: _elegirSede,
                        ),
                      ]);
                    },
                  ),
                  _seccion(k, t('dlg_idioma_titulo'), [
                    DropdownButton<String>(
                      value: idioma,
                      isExpanded: true,
                      items: [
                        for (final i in idiomasDisponibles)
                          DropdownMenuItem<String>(value: i['codigo']!, child: Text(i['nombre']!)),
                      ],
                      onChanged: (v) {
                        if (v != null) cambiarIdioma(v);
                      },
                    ),
                  ]),
                  _seccion(k, t('adm_tema'), [
                    ValueListenableBuilder<bool>(
                      valueListenable: temaOscuroNotifier,
                      builder: (context, oscuro, _) => SegmentedButton<bool>(
                        segments: [
                          ButtonSegment<bool>(value: true, icon: const Icon(Icons.dark_mode), label: Text(t('adm_tema_oscuro'))),
                          ButtonSegment<bool>(value: false, icon: const Icon(Icons.light_mode), label: Text(t('adm_tema_claro'))),
                        ],
                        selected: {oscuro},
                        onSelectionChanged: (s) async {
                          temaOscuroNotifier.value = s.first;
                          final prefs = await SharedPreferences.getInstance();
                          await prefs.setBool('tema_oscuro', s.first);
                        },
                      ),
                    ),
                  ]),
                  _seccion(k, t('adm_actualizaciones'), [
                    Align(
                      alignment: Alignment.centerLeft,
                      child: OutlinedButton.icon(
                        onPressed: () => comprobarActualizacionGitHub(context, forzar: true),
                        icon: const Icon(Icons.system_update),
                        label: Text(t('adm_buscar_actualizaciones')),
                      ),
                    ),
                  ]),
                  _seccion(k, t('adm_acerca'), [
                    Text(t('app_titulo'), style: const TextStyle(fontWeight: FontWeight.bold)),
                    Text(t('adm_version').replaceAll('{version}', kAppVersion)),
                    const SizedBox(height: 4),
                    Text(t('adm_licencia'), style: TextStyle(color: k.textoSuave)),
                  ]),
                  const SizedBox(height: 4),
                  OutlinedButton.icon(
                    onPressed: _desvincular,
                    icon: Icon(Icons.link_off, color: k.error),
                    label: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 10),
                        child: Text(t('adm_desvincular'), style: TextStyle(color: k.error))),
                    style: OutlinedButton.styleFrom(side: BorderSide(color: k.error)),
                  ),
                ]),
              ),
            ),
          ),
        ));
      },
    );
  }
}
