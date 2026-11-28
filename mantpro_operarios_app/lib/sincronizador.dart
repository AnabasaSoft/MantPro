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

// Cola de avisos pendientes y sincronización con el servidor (PC o MantPro
// Cloud). Mismo patrón que las otras apps: el aviso se guarda al instante
// en local, se encola, y cuando hay conexión se recorre la cola, se envía
// cada aviso y se retira de la cola lo que tiene éxito. Después se descarga
// de nuevo la lista de usuarios, las especialidades y las sedes.
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api.dart';
import 'cola.dart';
import 'conexion_segura.dart';
import 'modelos.dart';
import 'rutas_servidor.dart';

/// Cómo está la tablet con el servidor, para el indicador de la cabecera.
enum EstadoConexion { desconocido, pc, nube, sinConexion, sesionCaducada }

/// Resultado de enviar un aviso.
enum _Envio { ok, descartado, caducada, fallo }

/// Qué hacer con la respuesta del servidor a un aviso.
enum ResultadoAviso { ok, descartar, sesionCaducada, reintentar }

/// 200 (también «duplicado») = hecho. 400 y 403 `sin_permiso` = se descarta el aviso. Cualquier otro 403
/// (`solo_admin`, `no_autorizado`, sin JSON reconocible) y el 401 son problema de la tablet: sesión caducada y
/// el aviso se conserva. 409 (en curso, usuario no sincronizado), 5xx y demás: se reintenta más tarde.
(ResultadoAviso, String) clasificarRespuestaAviso(int estado, String cuerpo) {
  String? error;
  try {
    final e = (json.decode(cuerpo) as Map)['error'];
    if (e is String && e.isNotEmpty) error = e;
  } catch (_) {}
  if (estado == 200) return (ResultadoAviso.ok, '');
  if (estado == 401) return (ResultadoAviso.sesionCaducada, 'http_401');
  if (estado == 400) return (ResultadoAviso.descartar, error ?? 'http_400');
  if (estado == 403) {
    return error == 'sin_permiso'
        ? (ResultadoAviso.descartar, error!)
        : (ResultadoAviso.sesionCaducada, error ?? 'http_403');
  }
  return (ResultadoAviso.reintentar, error ?? 'http_$estado');
}

class Sincronizador {
  Sincronizador._();

  static const _claveCola = 'cola_avisos';
  static const _claveDescartados = 'avisos_descartados';
  static const _claveUsuarios = 'quiosco_usuarios';
  static const _claveSerie = 'clave_serie_bloqueada';
  static const _claveEspecialidades = 'especialidades_cache';
  static const _claveSedes = 'sedes_cache';
  static const _claveUltima = 'ultima_sincronizacion';
  static const intervalo = Duration(seconds: 30);

  /// Avisos por enviar (fuente de verdad en memoria; se guarda en SharedPreferences tras cada cambio).
  static final ValueNotifier<List<AvisoPendiente>> cola = ValueNotifier([]);

  /// Avisos que el servidor ha rechazado y se han descartado: {titulo, usuario, motivo, fecha}.
  static final ValueNotifier<List<Map<String, dynamic>>> descartados = ValueNotifier([]);

  static final ValueNotifier<List<UsuarioQuiosco>> usuarios = ValueNotifier([]);
  static final ValueNotifier<bool> claveSerieBloqueada = ValueNotifier(false);
  static final ValueNotifier<List<ElementoCatalogo>> especialidades = ValueNotifier([]);
  static final ValueNotifier<List<ElementoCatalogo>> sedes = ValueNotifier([]);

  static final ValueNotifier<EstadoConexion> estado = ValueNotifier(EstadoConexion.desconocido);
  static final ValueNotifier<bool> sincronizando = ValueNotifier(false);
  static final ValueNotifier<DateTime?> ultimaCorrecta = ValueNotifier(null);

  static Future<String?>? _enCurso;
  static Timer? _reloj;

  /// Lee de SharedPreferences la cola y las cachés. Llamar una vez al arrancar.
  static Future<void> cargar() async {
    final prefs = await SharedPreferences.getInstance();
    cola.value = AvisoPendiente.colaDeTexto(prefs.getString(_claveCola));
    try {
      descartados.value = (json.decode(prefs.getString(_claveDescartados) ?? '[]') as List)
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
    } catch (_) {
      descartados.value = [];
    }
    usuarios.value = UsuarioQuiosco.listaDeTexto(prefs.getString(_claveUsuarios));
    claveSerieBloqueada.value = prefs.getBool(_claveSerie) ?? false;
    especialidades.value = ElementoCatalogo.listaDeTexto(prefs.getString(_claveEspecialidades));
    sedes.value = ElementoCatalogo.listaDeTexto(prefs.getString(_claveSedes));
    final ultima = DateTime.tryParse(prefs.getString(_claveUltima) ?? '');
    ultimaCorrecta.value = ultima;
  }

  /// Sincroniza al arrancar y cada 30 s mientras la app está abierta.
  static void iniciarPeriodico() {
    _reloj?.cancel();
    unawaited(sincronizar());
    _reloj = Timer.periodic(intervalo, (_) {
      if (AuthService.autenticado) unawaited(sincronizar());
    });
  }

  /// Mete un aviso en la cola (queda guardado al momento).
  static Future<void> agregar(AvisoPendiente aviso) async {
    cola.value = [...cola.value, aviso];
    await _guardarCola();
  }

  static Future<void> _guardarCola() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_claveCola, AvisoPendiente.colaATexto(cola.value));
  }

  static Future<void> _quitarDeCola(AvisoPendiente aviso) async {
    cola.value = cola.value.where((a) => a.op != aviso.op).toList();
    await _guardarCola();
    for (final ruta in aviso.fotos) {
      try {
        final f = File(ruta);
        if (await f.exists()) await f.delete();
      } catch (_) {}
    }
  }

  static Future<void> _apuntarDescartado(AvisoPendiente aviso, String motivo) async {
    final lista = [
      ...descartados.value,
      {
        'titulo': aviso.titulo,
        'usuario': aviso.usuarioNombre,
        'motivo': motivo,
        'fecha': DateTime.now().toIso8601String(),
      }
    ];
    descartados.value = lista;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_claveDescartados, json.encode(lista));
  }

  /// Borra todos los avisos de la cola y sus fotos (cuando el administrador decide no enviarlos a otra vinculación).
  static Future<void> borrarCola() async {
    final antiguos = cola.value;
    cola.value = [];
    await _guardarCola();
    for (final a in antiguos) {
      for (final ruta in a.fotos) {
        try {
          final f = File(ruta);
          if (await f.exists()) await f.delete();
        } catch (_) {}
      }
    }
  }

  /// Al arrancar: borra las fotos de documentos/avisos que no usa ninguna entrada de la cola.
  static Future<void> limpiarHuerfanas() async {
    try {
      final base = await getApplicationDocumentsDirectory();
      await borrarFicherosHuerfanos(Directory(p.join(base.path, 'avisos')), cola.value);
    } catch (_) {}
  }

  /// Desvincula la tablet: apunta a qué PC/empresa estaba vinculada ('vinculacion_anterior'), cierra la sesión
  /// y borra los datos descargados (usuarios, especialidades, sedes). La cola de avisos se CONSERVA.
  static Future<void> desvincularTablet() async {
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString(RutasServidor.claveActiva);
    await prefs.setString('vinculacion_anterior',
        json.encode({'huella': prefs.getString('pc_huella') ?? '', 'nube': prefs.getString('ruta_nube') ?? ''}));
    await AuthService.cerrarSesion(ip: ip);
    for (final c in [_claveUsuarios, _claveSerie, _claveEspecialidades, _claveSedes, _claveUltima, 'sede_id', 'sede_uuid']) {
      await prefs.remove(c);
    }
    usuarios.value = [];
    claveSerieBloqueada.value = false;
    especialidades.value = [];
    sedes.value = [];
    ultimaCorrecta.value = null;
    estado.value = EstadoConexion.desconocido;
  }

  /// true si la vinculación actual es de otro PC o de otra empresa que la que se apuntó al desvincular.
  static Future<bool> esOtraVinculacion() async {
    final prefs = await SharedPreferences.getInstance();
    final texto = prefs.getString('vinculacion_anterior');
    if (texto == null) return false;
    try {
      final a = json.decode(texto) as Map;
      return (a['huella'] ?? '') != (prefs.getString('pc_huella') ?? '') ||
          (a['nube'] ?? '') != (prefs.getString('ruta_nube') ?? '');
    } catch (_) {
      return false;
    }
  }

  static Future<void> olvidarVinculacionAnterior() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('vinculacion_anterior');
  }

  static Future<void> borrarDescartados() async {
    descartados.value = [];
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_claveDescartados);
  }

  /// Una sola sincronización a la vez: si ya hay una en curso, se espera a esa. Devuelve null si todo ha ido
  /// bien o un código de error: 'sin_ruta', 'sin_conexion', 'sesion_caducada', 'servidor' o 'sin_usuarios'.
  /// [manual] (botón, vinculación) vuelve a decidir entre el PC y la nube antes de empezar.
  static Future<String?> sincronizar({bool manual = false, bool soloDescargar = false}) {
    return _enCurso ??= _sincronizar(manual, soloDescargar).whenComplete(() {
      _enCurso = null;
      sincronizando.value = false;
    });
  }

  static Future<String?> _sincronizar(bool manual, bool soloDescargar) async {
    sincronizando.value = true;
    if (!AuthService.autenticado) return 'sin_ruta';
    // Con la nube activa, cada tictac vuelve a probar el PC; si se pide a mano se decide de nuevo.
    if (manual) {
      await RutasServidor.resolver();
    } else {
      await RutasServidor.tictac();
    }
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString(RutasServidor.claveActiva);
    if (ip == null || ip.isEmpty) return 'sin_ruta';

    var huboRespuesta = false;
    String? error;

    // 1. ENVIAR los avisos en orden; ante el primer fallo se para (se conserva el orden).
    for (final aviso in soloDescargar ? <AvisoPendiente>[] : List<AvisoPendiente>.from(cola.value)) {
      final r = await _enviar(ip, aviso);
      if (r == _Envio.fallo) {
        error = estado.value == EstadoConexion.sinConexion ? 'sin_conexion' : 'servidor';
        if (error == 'servidor') huboRespuesta = true;
        break;
      }
      huboRespuesta = true;
      if (r == _Envio.caducada) {
        error = 'sesion_caducada';
        break;
      }
    }

    // 2. DESCARGAR usuarios, especialidades y sedes (si la descarga falla se queda la caché).
    if (error == null) {
      final r = await _descargar(ip, prefs);
      huboRespuesta = huboRespuesta || r != 'sin_conexion';
      error = r;
    }

    if (error == null) {
      final ahora = DateTime.now();
      ultimaCorrecta.value = ahora;
      await prefs.setString(_claveUltima, ahora.toIso8601String());
      _marcarConectado();
      return usuarios.value.isEmpty ? 'sin_usuarios' : null;
    }
    if (error == 'sesion_caducada') {
      estado.value = EstadoConexion.sesionCaducada;
    } else if (error == 'sin_conexion') {
      estado.value = EstadoConexion.sinConexion;
    } else if (huboRespuesta) {
      _marcarConectado();
    }
    return error;
  }

  static void _marcarConectado() => estado.value = RutasServidor.enNube.value ? EstadoConexion.nube : EstadoConexion.pc;

  /// Marca el estado según una respuesta: devuelve true si es un 401 real (sesión caducada). Un 401 recién
  /// iniciada la sesión, estando en la otra ruta (PC/nube), puede ser solo que esa ruta aún no la conoce.
  static Future<bool> _es401Real(int codigo) async {
    if (RutasServidor.esFalloDeRuta(codigo)) unawaited(RutasServidor.alFallar());
    if (codigo != 401) return false;
    if (await RutasServidor.sesionEnGracia()) {
      unawaited(RutasServidor.alFallar());
      return false;
    }
    return true;
  }

  static Future<_Envio> _enviar(String ip, AvisoPendiente aviso) async {
    try {
      final req = http.MultipartRequest('POST', Uri.parse('$esquemaPC://$ip/api/quiosco/aviso'));
      req.headers.addAll(AuthService.cabeceras());
      if (aviso.op.isNotEmpty) req.headers['X-MantPro-Op'] = aviso.op;
      req.fields['usuario_id'] = '${aviso.usuarioId}';
      if (aviso.usuarioIdUuid.isNotEmpty) req.fields['usuario_id_uuid'] = aviso.usuarioIdUuid;
      req.fields['titulo'] = aviso.titulo;
      req.fields['detalles'] = AvisoPendiente.conReferencia(aviso.detalles, aviso.op);
      req.fields['prioridad'] = aviso.prioridad;
      if (aviso.especialidadId != null) req.fields['especialidad_id'] = '${aviso.especialidadId}';
      if (aviso.especialidadIdUuid.isNotEmpty) req.fields['especialidad_id_uuid'] = aviso.especialidadIdUuid;
      if (aviso.sedeId != null) req.fields['sede_id'] = '${aviso.sedeId}';
      if (aviso.sedeIdUuid.isNotEmpty) req.fields['sede_id_uuid'] = aviso.sedeIdUuid;
      for (final ruta in aviso.fotos) {
        if (File(ruta).existsSync()) req.files.add(await http.MultipartFile.fromPath('fotos_extra', ruta));
      }
      // Plazo proporcional al tamaño: 60 s más 30 s por MB de fotos.
      var bytes = 0;
      for (final f in req.files) {
        bytes += f.length;
      }
      final plazo = Duration(seconds: 60 + 30 * (bytes / (1024 * 1024)).ceil());
      final streamed = await req.send().timeout(plazo);
      final res = await http.Response.fromStream(streamed);
      final (resultado, motivo) = clasificarRespuestaAviso(res.statusCode, res.body);
      if (resultado == ResultadoAviso.ok) {
        await _quitarDeCola(aviso);
        return _Envio.ok;
      }
      if (res.statusCode == 401 && !await _es401Real(401)) return _Envio.fallo;
      if (resultado == ResultadoAviso.sesionCaducada) {
        if (RutasServidor.esFalloDeRuta(res.statusCode)) unawaited(RutasServidor.alFallar());
        return _Envio.caducada;
      }
      if (resultado == ResultadoAviso.descartar) {
        await _quitarDeCola(aviso);
        await _apuntarDescartado(aviso, motivo);
        return _Envio.descartado;
      }
      if (RutasServidor.esFalloDeRuta(res.statusCode)) unawaited(RutasServidor.alFallar());
      // 409 (en curso), 5xx y demás: se queda en la cola para el siguiente intento.
      estado.value = EstadoConexion.desconocido;
      return _Envio.fallo;
    } catch (e) {
      if (_esErrorDeRed(e)) {
        estado.value = EstadoConexion.sinConexion;
        unawaited(RutasServidor.alFallar());
      }
      return _Envio.fallo;
    }
  }

  static bool _esErrorDeRed(Object e) =>
      e is SocketException || e is TimeoutException || e is http.ClientException || e is HandshakeException;

  /// Descarga usuarios, especialidades y sedes. null = bien; si no, el código de error.
  static Future<String?> _descargar(String ip, SharedPreferences prefs) async {
    try {
      final base = '$esquemaPC://$ip/api';
      final ru = await http.get(Uri.parse('$base/quiosco/usuarios'), headers: AuthService.cabeceras())
          .timeout(const Duration(seconds: 15));
      if (await _es401Real(ru.statusCode)) return 'sesion_caducada';
      if (ru.statusCode != 200) return 'servidor';
      final du = json.decode(ru.body) as Map<String, dynamic>;
      if (du['status'] != 'ok') return 'servidor';
      final listaUsuarios = (du['usuarios'] as List).map((e) => UsuarioQuiosco.fromJson(Map<String, dynamic>.from(e as Map))).toList();
      await prefs.setString(_claveUsuarios, json.encode(listaUsuarios.map((u) => u.toJson()).toList()));
      await prefs.setBool(_claveSerie, du['clave_serie_bloqueada'] == true);
      usuarios.value = listaUsuarios;
      claveSerieBloqueada.value = du['clave_serie_bloqueada'] == true;

      final re = await http.get(Uri.parse('$base/especialidades'), headers: AuthService.cabeceras())
          .timeout(const Duration(seconds: 15));
      if (re.statusCode == 200) {
        final lista = (json.decode(re.body) as List).map((e) => ElementoCatalogo.fromJson(Map<String, dynamic>.from(e as Map))).toList();
        await prefs.setString(_claveEspecialidades, json.encode(lista.map((e) => e.toJson()).toList()));
        especialidades.value = lista;
      }

      final rs = await http.get(Uri.parse('$base/sedes'), headers: AuthService.cabeceras())
          .timeout(const Duration(seconds: 15));
      if (rs.statusCode == 200) {
        final ds = json.decode(rs.body) as Map<String, dynamic>;
        final lista = (ds['sedes'] as List).map((e) => ElementoCatalogo.fromJson(Map<String, dynamic>.from(e as Map))).toList();
        await prefs.setString(_claveSedes, json.encode(lista.map((e) => e.toJson()).toList()));
        sedes.value = lista;
      }
      return null;
    } catch (e) {
      if (_esErrorDeRed(e)) {
        unawaited(RutasServidor.alFallar());
        return 'sin_conexion';
      }
      return 'servidor';
    }
  }
}
