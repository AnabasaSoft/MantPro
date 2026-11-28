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

// Un aviso de trabajo pendiente rellenado en la tablet y aún sin enviar al
// servidor (PC o MantPro Cloud). La cola de estos avisos se guarda en
// SharedPreferences ('cola_avisos') y se vacía al sincronizar.
import 'dart:convert';
import 'dart:io';
import 'package:path/path.dart' as p;

class AvisoPendiente {
  /// Identificador de la operación (cabecera X-MantPro-Op): evita duplicados si el envío se repite.
  final String op;
  final int usuarioId;
  final String usuarioIdUuid;
  final String usuarioNombre;
  final String titulo;
  final String detalles;

  /// Texto en español que entiende el servidor: Baja, Media, Alta o Crítica.
  final String prioridad;
  final int? especialidadId;
  final String especialidadIdUuid;
  final int? sedeId;
  final String sedeIdUuid;

  /// Rutas de las fotos copiadas en la carpeta de la app.
  final List<String> fotos;
  final DateTime creado;

  const AvisoPendiente({
    required this.op,
    required this.usuarioId,
    this.usuarioIdUuid = '',
    required this.usuarioNombre,
    required this.titulo,
    this.detalles = '',
    this.prioridad = 'Media',
    this.especialidadId,
    this.especialidadIdUuid = '',
    this.sedeId,
    this.sedeIdUuid = '',
    this.fotos = const [],
    required this.creado,
  });

  Map<String, dynamic> toJson() => {
        'op': op,
        'usuario_id': usuarioId,
        'usuario_id_uuid': usuarioIdUuid,
        'usuario_nombre': usuarioNombre,
        'titulo': titulo,
        'detalles': detalles,
        'prioridad': prioridad,
        'especialidad_id': especialidadId,
        'especialidad_id_uuid': especialidadIdUuid,
        'sede_id': sedeId,
        'sede_id_uuid': sedeIdUuid,
        'fotos': fotos,
        'creado': creado.toIso8601String(),
      };

  factory AvisoPendiente.fromJson(Map<String, dynamic> j) => AvisoPendiente(
        op: (j['op'] ?? '').toString(),
        usuarioId: (j['usuario_id'] as num?)?.toInt() ?? 0,
        usuarioIdUuid: (j['usuario_id_uuid'] ?? '').toString(),
        usuarioNombre: (j['usuario_nombre'] ?? '').toString(),
        titulo: (j['titulo'] ?? '').toString(),
        detalles: (j['detalles'] ?? '').toString(),
        prioridad: (j['prioridad'] ?? 'Media').toString(),
        especialidadId: (j['especialidad_id'] as num?)?.toInt(),
        especialidadIdUuid: (j['especialidad_id_uuid'] ?? '').toString(),
        sedeId: (j['sede_id'] as num?)?.toInt(),
        sedeIdUuid: (j['sede_id_uuid'] ?? '').toString(),
        fotos: ((j['fotos'] as List?) ?? const []).map((f) => f.toString()).toList(),
        creado: DateTime.tryParse((j['creado'] ?? '').toString()) ?? DateTime.now(),
      );

  /// La cola entera a texto JSON (lo que se guarda en SharedPreferences).
  static String colaATexto(List<AvisoPendiente> cola) => json.encode(cola.map((a) => a.toJson()).toList());

  /// Lee la cola guardada; un texto roto da una cola vacía y las entradas ilegibles se saltan.
  static List<AvisoPendiente> colaDeTexto(String? texto) {
    if (texto == null || texto.isEmpty) return [];
    try {
      final lista = json.decode(texto) as List;
      final resultado = <AvisoPendiente>[];
      for (final e in lista) {
        try {
          resultado.add(AvisoPendiente.fromJson(Map<String, dynamic>.from(e as Map)));
        } catch (_) {}
      }
      return resultado;
    } catch (_) {
      return [];
    }
  }

  /// Referencia de antiduplicado del aviso: el servidor la busca en los detalles para no repetir el aviso si
  /// se reenvía por otra ruta (PC/nube). Solo admite [0-9A-Za-z_-] y hasta 40 caracteres.
  static String referenciaDe(String op) {
    final limpia = op.replaceAll(RegExp(r'[^0-9A-Za-z_-]'), '_');
    return limpia.length > 40 ? limpia.substring(0, 40) : limpia;
  }

  /// Añade « [REF:op]» al final de [detalles] si aún no lo lleva (idempotente; entradas antiguas incluidas).
  static String conReferencia(String detalles, String op) {
    if (op.isEmpty || detalles.contains('[REF:')) return detalles;
    final ref = '[REF:${referenciaDe(op)}]';
    return detalles.isEmpty ? ref : '$detalles $ref';
  }
}

/// Borra de [carpeta] los ficheros que no usa ninguna entrada de la cola (fotos huérfanas de avisos
/// cancelados o de una caída de la app). Devuelve las rutas borradas.
Future<List<String>> borrarFicherosHuerfanos(Directory carpeta, Iterable<AvisoPendiente> cola) async {
  final borrados = <String>[];
  if (!await carpeta.exists()) return borrados;
  final usadas = {for (final a in cola) for (final f in a.fotos) p.normalize(p.absolute(f))};
  await for (final e in carpeta.list()) {
    if (e is! File) continue;
    if (usadas.contains(p.normalize(p.absolute(e.path)))) continue;
    try {
      await e.delete();
      borrados.add(e.path);
    } catch (_) {}
  }
  return borrados;
}
