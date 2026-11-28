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

// Datos que la tablet descarga del servidor y guarda en caché para trabajar sin conexión.
import 'dart:convert';

/// Un usuario de la lista «¿Quién eres?», con el hash de su contraseña para comprobarla en local.
class UsuarioQuiosco {
  final int id;
  final String login;
  final String nombre;
  final bool admin;
  final String hash;
  final String uuid;

  const UsuarioQuiosco({
    required this.id,
    required this.login,
    required this.nombre,
    required this.admin,
    required this.hash,
    this.uuid = '',
  });

  factory UsuarioQuiosco.fromJson(Map<String, dynamic> j) => UsuarioQuiosco(
        id: (j['id'] as num).toInt(),
        login: (j['login'] ?? '').toString(),
        nombre: (j['nombre'] ?? j['login'] ?? '').toString(),
        admin: j['admin'] == true,
        hash: (j['hash'] ?? '').toString(),
        uuid: (j['uuid'] ?? '').toString(),
      );

  Map<String, dynamic> toJson() =>
      {'id': id, 'login': login, 'nombre': nombre, 'admin': admin, 'hash': hash, if (uuid.isNotEmpty) 'uuid': uuid};

  static List<UsuarioQuiosco> listaDeTexto(String? texto) {
    if (texto == null || texto.isEmpty) return [];
    try {
      return (json.decode(texto) as List)
          .map((e) => UsuarioQuiosco.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (_) {
      return [];
    }
  }
}

/// Una especialidad o una sede (id, nombre y, con MantPro Cloud, uuid).
class ElementoCatalogo {
  final int id;
  final String nombre;
  final String uuid;

  const ElementoCatalogo({required this.id, required this.nombre, this.uuid = ''});

  factory ElementoCatalogo.fromJson(Map<String, dynamic> j) =>
      ElementoCatalogo(id: (j['id'] as num).toInt(), nombre: (j['nombre'] ?? '').toString(), uuid: (j['uuid'] ?? '').toString());

  Map<String, dynamic> toJson() => {'id': id, 'nombre': nombre, if (uuid.isNotEmpty) 'uuid': uuid};

  static List<ElementoCatalogo> listaDeTexto(String? texto) {
    if (texto == null || texto.isEmpty) return [];
    try {
      return (json.decode(texto) as List)
          .map((e) => ElementoCatalogo.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (_) {
      return [];
    }
  }
}
