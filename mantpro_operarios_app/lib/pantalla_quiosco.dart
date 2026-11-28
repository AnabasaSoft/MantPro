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

// La «ventana de avisos» de la tablet: réplica de la página /quiosco de la
// web (MantPro-Cloud/app_web/plantillas/web/quiosco.html). Cada operario
// elige su nombre, rellena el aviso, pone SU contraseña (se comprueba en
// local contra el hash descargado) y pulsa «Añadir»: el aviso queda en la
// cola local y se envía en cuanto hay conexión. Todo funciona sin red.
import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api.dart';
import 'cola.dart';
import 'contrasenas.dart';
import 'i18n/strings.dart';
import 'modelos.dart';
import 'pantalla_admin.dart';
import 'rutas_servidor.dart';
import 'sincronizador.dart';
import 'tema.dart';

/// Fijar pantalla de Android (la tablet no sale de la app con los botones del sistema).
const _canalQuiosco = MethodChannel('mantpro/quiosco');

const int _maxFotos = 20;
const int _segundosInactividad = 120;
const int _segundosMensaje = 5;
const double _anchoListaDefecto = 280;
const double _anchoMinimoLista = 160;

/// (valor que se envía al servidor, clave de su texto traducido)
const List<(String, String)> _prioridades = [
  ('Baja', 'prioridad_baja'),
  ('Media', 'prioridad_media'),
  ('Alta', 'prioridad_alta'),
  ('Crítica', 'prioridad_critica'),
];

/// Mensaje por clave de traducción (se traduce al pintarlo, así sigue al idioma activo).
class _Mensaje {
  final String clave;
  final Map<String, String> params;
  const _Mensaje(this.clave, [this.params = const {}]);

  String texto() {
    var s = t(clave);
    params.forEach((k, v) => s = s.replaceAll('{$k}', v));
    return s;
  }
}

enum _ResultadoClave { ok, mal, bloqueado }

class PantallaQuiosco extends StatefulWidget {
  const PantallaQuiosco({super.key});
  @override
  State<PantallaQuiosco> createState() => _PantallaQuioscoState();
}

class _PantallaQuioscoState extends State<PantallaQuiosco> {
  final _titulo = TextEditingController();
  final _detalles = TextEditingController();
  final _scrollLista = ScrollController();
  final _limite = LimiteIntentos();

  int? _usuarioId;
  int? _especialidadId;
  // Para volver a encontrar la elección cuando cambian las listas (los ids cambian entre PC y nube).
  String _usuarioUuid = '';
  String _usuarioLogin = '';
  String _especialidadUuid = '';
  String _prioridad = 'Media';
  final List<String> _fotos = [];

  _Mensaje? _mensaje;
  bool _exito = false;
  Timer? _temporizadorExito;
  Timer? _relojInactividad;
  // Mientras hay un diálogo (contraseña, fotos...) no se limpia el formulario por inactividad.
  int _dialogosAbiertos = 0;

  double _ancho = _anchoListaDefecto;
  double _anchoMaximo = 600;
  bool _arrastrando = false;
  int _contadorFotos = 0;

  @override
  void initState() {
    super.initState();
    _titulo.addListener(_tocado);
    _detalles.addListener(_tocado);
    Sincronizador.usuarios.addListener(_reResolver);
    Sincronizador.especialidades.addListener(_reResolver);
    _cargarAncho();
    _bloquear();
    _tocado();
  }

  @override
  void dispose() {
    Sincronizador.usuarios.removeListener(_reResolver);
    Sincronizador.especialidades.removeListener(_reResolver);
    _temporizadorExito?.cancel();
    _relojInactividad?.cancel();
    _limite.dispose();
    _titulo.dispose();
    _detalles.dispose();
    _scrollLista.dispose();
    _desbloquear();
    super.dispose();
  }

  // ---------------------------------------------------------------- bloqueo de la tablet

  Future<void> _bloquear() async {
    try {
      await _canalQuiosco.invokeMethod('bloquear');
    } catch (_) {}
  }

  Future<void> _desbloquear() async {
    try {
      await _canalQuiosco.invokeMethod('desbloquear');
    } catch (_) {}
  }

  // ---------------------------------------------------------------- ancho de la lista

  Future<void> _cargarAncho() async {
    final prefs = await SharedPreferences.getInstance();
    final guardado = prefs.getDouble('quiosco_ancho');
    if (guardado != null && mounted) setState(() => _ancho = guardado);
  }

  Future<void> _guardarAncho() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble('quiosco_ancho', _ancho);
  }

  /// Tras una sincronización, vuelve a buscar al usuario y la especialidad elegidos por uuid (o login); si ya no existen, los deselecciona.
  void _reResolver() {
    if (!mounted) return;
    var cambio = false;
    if (_usuarioId != null) {
      UsuarioQuiosco? nuevo;
      for (final u in Sincronizador.usuarios.value) {
        final coincide = _usuarioUuid.isNotEmpty ? u.uuid == _usuarioUuid : u.login.toLowerCase() == _usuarioLogin.toLowerCase();
        if (coincide) nuevo = u;
      }
      if (nuevo?.id != _usuarioId) {
        _usuarioId = nuevo?.id;
        cambio = true;
      }
    }
    if (_especialidadId != null) {
      ElementoCatalogo? nueva;
      for (final e in Sincronizador.especialidades.value) {
        final coincide = _especialidadUuid.isNotEmpty ? e.uuid == _especialidadUuid : e.id == _especialidadId;
        if (coincide) nueva = e;
      }
      if (nueva?.id != _especialidadId) {
        _especialidadId = nueva?.id;
        cambio = true;
      }
    }
    if (cambio) setState(() {});
  }

  // ---------------------------------------------------------------- inactividad

  void _tocado() {
    _relojInactividad?.cancel();
    _relojInactividad = Timer(const Duration(seconds: _segundosInactividad), _alInactividad);
  }

  bool get _hayAlgo =>
      _usuarioId != null || _titulo.text.trim().isNotEmpty || _detalles.text.trim().isNotEmpty || _fotos.isNotEmpty;

  void _alInactividad() {
    if (!mounted) return;
    if (_dialogosAbiertos > 0) {
      _tocado();
      return;
    }
    if (_hayAlgo) _limpiar(borrarFotos: true);
  }

  /// Ejecuta [f] (un diálogo, el selector de fotos...) sin que el formulario se limpie por inactividad.
  Future<T> _conDialogo<T>(Future<T> Function() f) async {
    _dialogosAbiertos++;
    try {
      return await f();
    } finally {
      _dialogosAbiertos--;
      _tocado();
    }
  }

  // ---------------------------------------------------------------- formulario

  UsuarioQuiosco? get _usuario {
    for (final u in Sincronizador.usuarios.value) {
      if (u.id == _usuarioId) return u;
    }
    return null;
  }

  Future<void> _borrarFicheros(List<String> rutas) async {
    for (final r in rutas) {
      try {
        final f = File(r);
        if (await f.exists()) await f.delete();
      } catch (_) {}
    }
  }

  /// Deja el formulario como nuevo (también desmarca el usuario). [borrarFotos]: false cuando las fotos
  /// ya pertenecen a un aviso de la cola.
  Future<void> _limpiar({required bool borrarFotos}) async {
    final fotos = List<String>.from(_fotos);
    if (!mounted) return;
    setState(() {
      _usuarioId = null;
      _titulo.clear();
      _detalles.clear();
      _especialidadId = null;
      _prioridad = 'Media';
      _fotos.clear();
      _mensaje = null;
    });
    if (borrarFotos) await _borrarFicheros(fotos);
  }

  void _mostrarExito() {
    _temporizadorExito?.cancel();
    setState(() => _exito = true);
    _temporizadorExito = Timer(const Duration(seconds: _segundosMensaje), () {
      if (mounted) setState(() => _exito = false);
    });
  }

  // ---------------------------------------------------------------- fotos

  Future<void> _anadirFotos() async {
    final origen = await _conDialogo(() => showModalBottomSheet<String>(
          context: context,
          builder: (ctx) => SafeArea(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              ListTile(
                  leading: const Icon(Icons.photo_camera),
                  title: Text(t('op_foto_camara')),
                  onTap: () => Navigator.pop(ctx, 'camara')),
              ListTile(
                  leading: const Icon(Icons.photo_library),
                  title: Text(t('op_foto_galeria')),
                  onTap: () => Navigator.pop(ctx, 'galeria')),
            ]),
          ),
        ));
    if (origen == null || !mounted) return;
    if (_fotos.length >= _maxFotos) {
      setState(() => _mensaje = _Mensaje('op_fotos_maximo', {'n': '$_maxFotos'}));
      return;
    }
    final picker = ImagePicker();
    final elegidas = <String>[];
    try {
      if (origen == 'camara') {
        final f = await _conDialogo(() => picker.pickImage(source: ImageSource.camera, imageQuality: 60, maxWidth: 1920, maxHeight: 1920));
        if (f != null) elegidas.add(f.path);
      } else {
        final fs = await _conDialogo(() => picker.pickMultiImage(imageQuality: 60, maxWidth: 1920, maxHeight: 1920));
        elegidas.addAll(fs.map((f) => f.path));
      }
    } catch (_) {
      return;
    }
    if (elegidas.isEmpty || !mounted) return;
    final libres = _maxFotos - _fotos.length;
    final admitidas = elegidas.take(libres).toList();
    final copiadas = await _copiarFotos(admitidas);
    if (!mounted) {
      await _borrarFicheros(copiadas);
      return;
    }
    setState(() {
      _fotos.addAll(copiadas);
      _mensaje = elegidas.length > libres ? _Mensaje('op_fotos_maximo', {'n': '$_maxFotos'}) : null;
    });
  }

  /// Copia cada foto a la carpeta de la app (avisos/) con nombre único: la caché del selector se puede vaciar.
  Future<List<String>> _copiarFotos(List<String> origenes) async {
    final base = await getApplicationDocumentsDirectory();
    final dir = Directory(p.join(base.path, 'avisos'));
    await dir.create(recursive: true);
    final copiadas = <String>[];
    for (final origen in origenes) {
      var ext = p.extension(origen);
      if (ext.isEmpty) ext = '.jpg';
      final destino = p.join(dir.path, 'aviso_${DateTime.now().microsecondsSinceEpoch}_${_contadorFotos++}$ext');
      try {
        await File(origen).copy(destino);
        copiadas.add(destino);
      } catch (_) {}
    }
    return copiadas;
  }

  Future<void> _quitarFoto(String ruta) async {
    setState(() => _fotos.remove(ruta));
    await _borrarFicheros([ruta]);
  }

  // ---------------------------------------------------------------- añadir

  Future<_ResultadoClave> _comprobar(String contrasena, List<String> hashes) async {
    var correcta = false;
    for (final h in hashes) {
      if (await comprobarContrasena(contrasena, h, claveSerieBloqueada: Sincronizador.claveSerieBloqueada.value)) {
        correcta = true;
        break;
      }
    }
    if (correcta) {
      _limite.registrarAcierto();
      return _ResultadoClave.ok;
    }
    _limite.registrarFallo();
    return _limite.bloqueado ? _ResultadoClave.bloqueado : _ResultadoClave.mal;
  }

  Future<AvisoPendiente> _construirAviso(UsuarioQuiosco u) async {
    final prefs = await SharedPreferences.getInstance();
    ElementoCatalogo? esp;
    for (final e in Sincronizador.especialidades.value) {
      if (e.id == _especialidadId) esp = e;
    }
    final op = nuevaOperacion();
    return AvisoPendiente(
      op: op,
      usuarioId: u.id,
      usuarioIdUuid: u.uuid,
      usuarioNombre: u.nombre,
      titulo: _titulo.text.trim(),
      detalles: AvisoPendiente.conReferencia(_detalles.text.trim(), op),
      prioridad: _prioridad,
      especialidadId: esp?.id,
      especialidadIdUuid: esp?.uuid ?? '',
      sedeId: prefs.getInt('sede_id'),
      sedeIdUuid: prefs.getString('sede_uuid') ?? '',
      fotos: List<String>.from(_fotos),
      creado: DateTime.now(),
    );
  }

  Future<void> _anadir() async {
    if (_limite.bloqueado) return;
    final u = _usuario;
    if (u == null) {
      setState(() => _mensaje = const _Mensaje('quiosco_sin_usuario'));
      return;
    }
    if (_titulo.text.trim().isEmpty) {
      setState(() => _mensaje = const _Mensaje('quiosco_falta_titulo'));
      return;
    }
    setState(() {
      _mensaje = null;
      _exito = false;
    });
    final aviso = await _construirAviso(u);
    if (!mounted) return;
    final correcta = await _conDialogo(() => showDialog<bool>(
          context: context,
          barrierColor: colorFondoDialogo,
          builder: (_) => _DialogoContrasena(
            titulo: t('quiosco_pide_contrasena').replaceAll('{nombre}', u.nombre),
            textoBoton: t('btn_aceptar'),
            colorBoton: colorVerde,
            verificar: (c) => _comprobar(c, [u.hash]),
          ),
        ));
    if (correcta != true || !mounted) return;
    // Aplicar en local al instante: el aviso entra en la cola persistida y se limpia el formulario.
    await Sincronizador.agregar(aviso);
    await _limpiar(borrarFotos: false);
    if (!mounted) return;
    _mostrarExito();
    unawaited(Sincronizador.sincronizar());
  }

  // ---------------------------------------------------------------- cerrar (administrador)

  /// Hash del administrador que vinculó la tablet (se busca por login, sin distinguir mayúsculas, porque los ids
  /// cambian entre el PC y la nube) y siempre siendo administrador; si no está, los de todos los administradores.
  List<String> _hashesAdmin() {
    final lista = Sincronizador.usuarios.value.where((u) => u.admin && u.hash.isNotEmpty).toList();
    final login = (AuthService.login ?? '').toLowerCase();
    if (login.isNotEmpty) {
      for (final u in lista) {
        if (u.login.toLowerCase() == login) return [u.hash];
      }
    }
    return lista.map((u) => u.hash).toList();
  }

  /// Sin lista de usuarios no hay contraseña que pedir: se ofrece sincronizar o volver a vincular.
  Future<void> _avisarSinLista() async {
    final accion = await _conDialogo(() => showDialog<String>(
          context: context,
          barrierColor: colorFondoDialogo,
          builder: (ctx) => AlertDialog(
            content: Text(t('op_sin_lista_cerrar')),
            actions: [
              ElevatedButton(onPressed: () => Navigator.pop(ctx, 'sincronizar'), child: Text(t('adm_sincronizar'))),
              ElevatedButton(onPressed: () => Navigator.pop(ctx, 'vincular'), child: Text(t('op_volver_vincular'))),
              TextButton(onPressed: () => Navigator.pop(ctx), child: Text(t('btn_cancelar'))),
            ],
          ),
        ));
    if (accion == 'sincronizar') {
      unawaited(Sincronizador.sincronizar(manual: true));
    } else if (accion == 'vincular') {
      await Sincronizador.desvincularTablet();
    }
  }

  Future<void> _cerrar() async {
    if (_limite.bloqueado) return;
    final hashes = _hashesAdmin();
    if (hashes.isEmpty) {
      await _avisarSinLista();
      return;
    }
    final correcta = await _conDialogo(() => showDialog<bool>(
          context: context,
          barrierColor: colorFondoDialogo,
          builder: (_) => _DialogoContrasena(
            titulo: t('quiosco_pide_contrasena_admin').replaceAll('{nombre}', AuthService.nombre ?? ''),
            textoBoton: t('quiosco_btn_cerrar'),
            colorBoton: colorRojo,
            verificar: (c) => _comprobar(c, hashes),
          ),
        ));
    if (correcta != true || !mounted) return;
    await _desbloquear();
    if (!mounted) return;
    await _conDialogo(() => Navigator.push(context, MaterialPageRoute(builder: (_) => const PantallaAdmin())));
    // Si se ha desvinculado, esta pantalla ya no existe; si no, se vuelve a fijar la pantalla.
    if (!mounted || !AuthService.autenticado) return;
    await _bloquear();
  }

  // ---------------------------------------------------------------- aspecto

  InputDecoration _decoracion(TokensTema k, {String? hint}) {
    OutlineInputBorder borde(Color c, [double ancho = 1]) =>
        OutlineInputBorder(borderRadius: BorderRadius.circular(4), borderSide: BorderSide(color: c, width: ancho));
    return InputDecoration(
      hintText: hint,
      hintStyle: TextStyle(color: k.textoSuave, fontSize: tamControl),
      filled: true,
      fillColor: k.campo,
      isDense: true,
      counterText: '',
      contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      border: borde(k.borde),
      enabledBorder: borde(k.borde),
      focusedBorder: borde(k.acento, 2),
    );
  }

  Widget _boton(TokensTema k, String texto, VoidCallback? alPulsar,
      {Color? fondo, Color? colorTexto, double tamano = tamControl, EdgeInsets? relleno, FontWeight? peso}) {
    return ElevatedButton(
      onPressed: alPulsar,
      style: ElevatedButton.styleFrom(
        backgroundColor: fondo ?? k.superficie,
        foregroundColor: colorTexto ?? k.texto,
        disabledBackgroundColor: (fondo ?? k.superficie).withValues(alpha: 0.5),
        disabledForegroundColor: (colorTexto ?? k.texto).withValues(alpha: 0.6),
        elevation: 0,
        padding: relleno ?? const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(5), side: BorderSide(color: fondo ?? k.borde)),
        textStyle: TextStyle(fontSize: tamano, fontWeight: peso),
      ),
      child: Text(texto),
    );
  }

  Widget _indicador(TokensTema k) {
    return ListenableBuilder(
      listenable: Listenable.merge([Sincronizador.estado, Sincronizador.cola, RutasServidor.enNube]),
      builder: (context, _) {
        final estado = Sincronizador.estado.value;
        final (texto, color) = switch (estado) {
          EstadoConexion.pc => (t('op_conexion_pc'), colorVerde),
          EstadoConexion.nube => (t('op_conexion_nube'), colorVerde),
          EstadoConexion.sinConexion => (t('op_sin_conexion'), k.textoSuave),
          EstadoConexion.sesionCaducada => (t('op_sesion_caducada_corto'), k.error),
          EstadoConexion.desconocido => (t('op_comprobando_conexion'), k.textoSuave),
        };
        final pendientes = Sincronizador.cola.value.length;
        return Column(crossAxisAlignment: CrossAxisAlignment.end, mainAxisSize: MainAxisSize.min, children: [
          Row(mainAxisSize: MainAxisSize.min, children: [
            Container(width: 10, height: 10, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
            const SizedBox(width: 6),
            Flexible(child: Text(texto, style: TextStyle(fontSize: 0.85 * rem, color: k.textoSuave))),
          ]),
          if (pendientes > 0)
            Text(t('op_avisos_por_enviar').replaceAll('{n}', '$pendientes'),
                style: TextStyle(fontSize: 0.85 * rem, color: k.textoSuave)),
          if (estado == EstadoConexion.sesionCaducada)
            Text(t('op_sesion_caducada'),
                textAlign: TextAlign.end, style: TextStyle(fontSize: 0.8 * rem, color: k.error)),
        ]);
      },
    );
  }

  Widget _cabecera(TokensTema k, bool estrecho) {
    final titulos = Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(t('quiosco_titulo'), style: TextStyle(fontSize: 1.6 * rem, fontWeight: FontWeight.bold, color: k.texto)),
      const SizedBox(height: 3),
      Text(t('quiosco_ayuda'), style: TextStyle(fontSize: tamBase, color: k.textoSuave)),
    ]);
    final cerrar = ListenableBuilder(
      listenable: _limite,
      builder: (context, _) => Opacity(
        opacity: 0.7,
        child: _boton(k, t('quiosco_btn_cerrar'), _limite.bloqueado ? null : _cerrar,
            tamano: 0.85 * rem, relleno: const EdgeInsets.symmetric(horizontal: 10, vertical: 3)),
      ),
    );
    if (estrecho) {
      return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        titulos,
        const SizedBox(height: 8),
        Row(children: [Expanded(child: Align(alignment: Alignment.centerLeft, child: _indicador(k))), cerrar]),
      ]);
    }
    return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Expanded(child: titulos),
      const SizedBox(width: 12.8),
      ConstrainedBox(constraints: const BoxConstraints(maxWidth: 320), child: _indicador(k)),
      const SizedBox(width: 12.8),
      cerrar,
    ]);
  }

  Widget _lista(TokensTema k, bool estrecho) {
    final usuarios = Sincronizador.usuarios.value;
    final contenido = usuarios.isEmpty
        ? Padding(
            padding: const EdgeInsets.all(12.8),
            child: Text(t('op_sin_lista_usuarios'), style: TextStyle(color: k.textoSuave)),
          )
        : Scrollbar(
            controller: _scrollLista,
            thumbVisibility: true,
            child: ListView.builder(
              controller: _scrollLista,
              shrinkWrap: estrecho,
              itemCount: usuarios.length,
              itemBuilder: (context, i) {
                final u = usuarios[i];
                final elegido = u.id == _usuarioId;
                final colorTexto = elegido ? k.sobreAcento : k.texto;
                return Material(
                  color: elegido ? k.acento : Colors.transparent,
                  child: InkWell(
                    onTap: () {
                      setState(() {
                        _usuarioId = u.id;
                        _usuarioUuid = u.uuid;
                        _usuarioLogin = u.login;
                      });
                      _tocado();
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12.8, vertical: 11.2),
                      decoration: BoxDecoration(border: Border(bottom: BorderSide(color: k.bordeSuave))),
                      child: Row(children: [
                        Icon(elegido ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                            size: 1.2 * rem, color: colorTexto),
                        const SizedBox(width: 9.6),
                        Expanded(child: Text(u.nombre, style: TextStyle(fontSize: rem, color: colorTexto))),
                      ]),
                    ),
                  ),
                );
              },
            ),
          );
    final caja = Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: k.campo,
        border: Border.all(color: k.borde),
        borderRadius: BorderRadius.circular(6),
      ),
      child: contenido,
    );
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, mainAxisSize: MainAxisSize.min, children: [
      Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(t('quiosco_elige_usuario'),
            style: TextStyle(fontSize: 1.1 * rem, fontWeight: FontWeight.bold, color: k.texto)),
      ),
      if (estrecho) ConstrainedBox(constraints: const BoxConstraints(maxHeight: 224), child: caja) else Expanded(child: caja),
    ]);
  }

  Widget _tirador(TokensTema k) {
    return MouseRegion(
      cursor: SystemMouseCursors.resizeColumn,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onHorizontalDragStart: (_) => setState(() => _arrastrando = true),
        onHorizontalDragUpdate: (d) => setState(
            () => _ancho = (_ancho + d.delta.dx).clamp(_anchoMinimoLista, _anchoMaximo).toDouble()),
        onHorizontalDragEnd: (_) {
          setState(() => _arrastrando = false);
          _guardarAncho();
        },
        child: SizedBox(
          width: 12,
          child: Center(
            child: Container(
              width: 4,
              decoration: BoxDecoration(
                color: _arrastrando ? k.acento : k.borde,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _mensajes(TokensTema k) {
    return ListenableBuilder(
      listenable: _limite,
      builder: (context, _) {
        final widgets = <Widget>[];
        if (_exito) {
          widgets.add(Container(
            padding: const EdgeInsets.symmetric(horizontal: 12.8, vertical: 9.6),
            decoration: BoxDecoration(color: colorVerde, borderRadius: BorderRadius.circular(4)),
            child: Text(t('quiosco_aviso_anadido'),
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 1.15 * rem)),
          ));
        }
        String? error;
        if (_limite.bloqueado) {
          error = t('quiosco_demasiados_intentos').replaceAll('{segundos}', '${_limite.segundosRestantes}');
        } else if (_mensaje != null) {
          error = _mensaje!.texto();
        }
        if (error != null) {
          widgets.add(Container(
            padding: const EdgeInsets.symmetric(horizontal: 12.8, vertical: 9.6),
            decoration: BoxDecoration(color: k.errorFondo, borderRadius: BorderRadius.circular(4)),
            child: Text(error, style: TextStyle(color: k.error, fontSize: tamBase)),
          ));
        }
        return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [for (final w in widgets) Padding(padding: const EdgeInsets.only(bottom: 8), child: w)]);
      },
    );
  }

  Widget _selector<T>(TokensTema k, String etiqueta, T valor, List<DropdownMenuItem<T>> items, ValueChanged<T?> alCambiar) {
    return Row(children: [
      Text('$etiqueta:', style: TextStyle(fontSize: tamControl, color: k.texto)),
      const SizedBox(width: 9.6),
      Expanded(
        child: InputDecorator(
          decoration: _decoracion(k).copyWith(contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8)),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<T>(
              value: valor,
              isExpanded: true,
              isDense: true,
              dropdownColor: k.superficie,
              style: TextStyle(fontSize: tamControl, color: k.texto),
              items: items,
              onChanged: (v) {
                alCambiar(v);
                _tocado();
              },
            ),
          ),
        ),
      ),
    ]);
  }

  Widget _miniatura(TokensTema k, String ruta) {
    return SizedBox(
      width: 120,
      child: Column(children: [
        Container(
          width: 120,
          height: 120,
          clipBehavior: Clip.antiAlias,
          decoration: BoxDecoration(border: Border.all(color: k.borde), borderRadius: BorderRadius.circular(4)),
          child: Image.file(File(ruta),
              fit: BoxFit.cover,
              cacheWidth: 240,
              errorBuilder: (_, _, _) => Icon(Icons.broken_image, color: k.textoSuave)),
        ),
        const SizedBox(height: 4),
        _boton(k, t('btn_quitar_foto_coleccion'), () => _quitarFoto(ruta),
            tamano: 0.85 * rem, relleno: const EdgeInsets.symmetric(horizontal: 8, vertical: 2.4)),
      ]),
    );
  }

  Widget _formulario(TokensTema k, UsuarioQuiosco? usuario) {
    final estiloControl = TextStyle(fontSize: tamControl, color: k.texto);
    final especialidades = Sincronizador.especialidades.value;
    final espValida = especialidades.any((e) => e.id == _especialidadId) ? _especialidadId : null;
    final grupo = Container(
      padding: const EdgeInsets.all(0.8 * rem),
      decoration: BoxDecoration(
        color: k.fondo,
        border: Border.all(color: k.bordeSuave),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(t('lbl_avisar_pendiente'), style: estiloControl),
        const SizedBox(height: 9.6),
        TextField(
          controller: _titulo,
          maxLength: 300,
          style: estiloControl,
          textInputAction: TextInputAction.next,
          decoration: _decoracion(k, hint: t('ph_titulo')),
        ),
        const SizedBox(height: 9.6),
        TextField(
          controller: _detalles,
          minLines: 6,
          maxLines: 6,
          style: estiloControl,
          keyboardType: TextInputType.multiline,
          decoration: _decoracion(k, hint: t('ph_detalles')),
        ),
        const SizedBox(height: 9.6),
        _selector<int?>(k, t('usuarios_col_especialidad'), espValida, [
          DropdownMenuItem<int?>(value: null, child: Text(t('especialidades_ninguna'))),
          for (final e in especialidades) DropdownMenuItem<int?>(value: e.id, child: Text(e.nombre)),
        ], (v) => setState(() {
              _especialidadId = v;
              _especialidadUuid = especialidades.where((e) => e.id == v).map((e) => e.uuid).firstOrNull ?? '';
            })),
        const SizedBox(height: 9.6),
        _selector<String>(k, t('lbl_prioridad'), _prioridad, [
          for (final (valor, clave) in _prioridades) DropdownMenuItem<String>(value: valor, child: Text(t(clave))),
        ], (v) => setState(() => _prioridad = v ?? 'Media')),
        const SizedBox(height: 9.6),
        Row(children: [
          Expanded(child: Text(t('lbl_coleccion_fotos'), style: estiloControl)),
          _boton(k, t('btn_anadir_fotos'), _anadirFotos),
        ]),
        const SizedBox(height: 6.4),
        Container(
          width: double.infinity,
          constraints: const BoxConstraints(minHeight: 7 * rem),
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: k.campo,
            border: Border.all(color: k.borde),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Wrap(spacing: 9.6, runSpacing: 9.6, children: [for (final f in _fotos) _miniatura(k, f)]),
        ),
        const SizedBox(height: 9.6),
        Align(
          alignment: Alignment.centerRight,
          child: ListenableBuilder(
            listenable: _limite,
            builder: (context, _) => _boton(k, t('btn_anadir'), _limite.bloqueado ? null : _anadir,
                fondo: colorVerde,
                colorTexto: Colors.white,
                tamano: 1.15 * rem,
                peso: FontWeight.bold,
                relleno: const EdgeInsets.symmetric(horizontal: 28, vertical: 12)),
          ),
        ),
      ]),
    );
    // Sin usuario elegido el formulario está desactivado (opacidad .55), como en la web.
    return Opacity(opacity: usuario == null ? 0.55 : 1, child: IgnorePointer(ignoring: usuario == null, child: grupo));
  }

  Widget _contenidoAviso(TokensTema k) {
    final usuario = _usuario;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      _mensajes(k),
      Text(
        usuario == null ? t('quiosco_sin_usuario') : t('quiosco_avisa').replaceAll('{nombre}', usuario.nombre),
        style: TextStyle(fontSize: 1.15 * rem, fontWeight: FontWeight.bold, color: k.texto),
      ),
      const SizedBox(height: 8),
      _formulario(k, usuario),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: idiomaNotifier,
      builder: (context, _, _) {
        final k = TokensTema.de(context);
        return PopScope(
          canPop: false,
          child: Scaffold(
            body: SafeArea(
              child: Listener(
                behavior: HitTestBehavior.translucent,
                onPointerDown: (_) => _tocado(),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 9.6, 16, 16),
                  child: ListenableBuilder(
                    listenable: Listenable.merge([Sincronizador.usuarios, Sincronizador.especialidades]),
                    builder: (context, _) => LayoutBuilder(builder: (context, c) {
                      final estrecho = c.maxWidth < 720;
                      _anchoMaximo = (c.maxWidth * 0.6).floorToDouble().clamp(200, double.infinity);
                      final ancho = _ancho.clamp(_anchoMinimoLista, _anchoMaximo).toDouble();
                      return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                        _cabecera(k, estrecho),
                        const SizedBox(height: 9.6),
                        Expanded(
                          child: estrecho
                              ? SingleChildScrollView(
                                  child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                                    _lista(k, true),
                                    const SizedBox(height: 9.6),
                                    _contenidoAviso(k),
                                  ]),
                                )
                              : Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                                  SizedBox(width: ancho, child: _lista(k, false)),
                                  _tirador(k),
                                  Expanded(child: SingleChildScrollView(child: _contenidoAviso(k))),
                                ]),
                        ),
                      ]);
                    }),
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

/// Diálogo de contraseña (la de quien avisa o la del administrador). La comprobación se hace aquí dentro,
/// en un isolate y con un indicador de espera. Se cierra con true si es correcta, con false si hay bloqueo.
class _DialogoContrasena extends StatefulWidget {
  final String titulo;
  final String textoBoton;
  final Color colorBoton;
  final Future<_ResultadoClave> Function(String contrasena) verificar;

  const _DialogoContrasena({
    required this.titulo,
    required this.textoBoton,
    required this.colorBoton,
    required this.verificar,
  });

  @override
  State<_DialogoContrasena> createState() => _DialogoContrasenaState();
}

class _DialogoContrasenaState extends State<_DialogoContrasena> {
  final _campo = TextEditingController();
  final _foco = FocusNode();
  bool _verificando = false;
  String? _error;

  @override
  void dispose() {
    _campo.dispose();
    _foco.dispose();
    super.dispose();
  }

  Future<void> _aceptar() async {
    if (_verificando) return;
    final contrasena = _campo.text;
    setState(() {
      _verificando = true;
      _error = null;
    });
    final r = await widget.verificar(contrasena);
    if (!mounted) return;
    switch (r) {
      case _ResultadoClave.ok:
        Navigator.pop(context, true);
      case _ResultadoClave.bloqueado:
        Navigator.pop(context, false);
      case _ResultadoClave.mal:
        setState(() {
          _verificando = false;
          _error = t('quiosco_contrasena_mal');
          _campo.clear();
        });
        _foco.requestFocus();
    }
  }

  @override
  Widget build(BuildContext context) {
    final k = TokensTema.de(context);
    return AlertDialog(
      content: SizedBox(
        width: 26 * rem,
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(widget.titulo, style: TextStyle(fontSize: tamBase, color: k.texto)),
          const SizedBox(height: 9.6),
          TextField(
            controller: _campo,
            focusNode: _foco,
            autofocus: true,
            obscureText: true,
            enabled: !_verificando,
            enableSuggestions: false,
            autocorrect: false,
            onSubmitted: (_) => _aceptar(),
            style: TextStyle(fontSize: 16 * 96 / 72, color: k.texto),
            decoration: InputDecoration(
              hintText: t('login_password'),
              filled: true,
              fillColor: k.campo,
              isDense: true,
              contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(4), borderSide: BorderSide(color: k.borde)),
              focusedBorder:
                  OutlineInputBorder(borderRadius: BorderRadius.circular(4), borderSide: BorderSide(color: k.acento, width: 2)),
            ),
          ),
          if (_verificando)
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Row(children: [
                const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2.5)),
                const SizedBox(width: 10),
                Flexible(child: Text(t('op_verificando'), style: TextStyle(color: k.textoSuave))),
              ]),
            ),
          if (_error != null)
            Padding(padding: const EdgeInsets.only(top: 10), child: Text(_error!, style: TextStyle(color: k.error))),
        ]),
      ),
      actions: [
        ElevatedButton(
          onPressed: _verificando ? null : _aceptar,
          style: ElevatedButton.styleFrom(
            backgroundColor: widget.colorBoton,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(5)),
          ),
          child: Text(widget.textoBoton),
        ),
        TextButton(
          onPressed: _verificando ? null : () => Navigator.pop(context, null),
          child: Text(t('btn_cancelar')),
        ),
      ],
    );
  }
}
