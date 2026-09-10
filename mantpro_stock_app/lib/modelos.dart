// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later

import 'package:flutter/material.dart';

class Seccion {
  final int id;
  final String nombre;
  Seccion({required this.id, required this.nombre});
  factory Seccion.fromJson(Map<String, dynamic> j) =>
      Seccion(id: j['id'], nombre: j['nombre'] ?? '');
}

class Balda {
  final int id;
  final int numero; // 0 = hueco de suelo
  final List<Seccion> secciones;
  Balda({required this.id, required this.numero, required this.secciones});
  factory Balda.fromJson(Map<String, dynamic> j) => Balda(
        id: j['id'],
        numero: j['numero'] ?? 0,
        secciones: ((j['secciones'] as List?) ?? [])
            .map((s) => Seccion.fromJson(s))
            .toList(),
      );
}

class Estanteria {
  final int id;
  final String nombre;
  final String estiloBaldas; // 'numero' o 'letra': cómo se numeran sus baldas
  final List<Balda> baldas;
  Estanteria({required this.id, required this.nombre, required this.estiloBaldas, required this.baldas});
  factory Estanteria.fromJson(Map<String, dynamic> j) => Estanteria(
        id: j['id'],
        nombre: j['nombre'] ?? '',
        estiloBaldas: j['estilo_baldas'] ?? 'numero',
        baldas: ((j['baldas'] as List?) ?? []).map((b) => Balda.fromJson(b)).toList(),
      );
}

/// Convierte un índice (1, 2, 3...) en letras estilo columnas de hoja de
/// cálculo (A, B, ..., Z, AA, AB...), igual que _letra_seccion en almacen.py.
String letraDesdeIndice(int indice) {
  var letras = '';
  while (indice > 0) {
    final resto = (indice - 1) % 26;
    indice = (indice - 1) ~/ 26;
    letras = String.fromCharCode('A'.codeUnitAt(0) + resto) + letras;
  }
  return letras;
}

/// Texto de una balda (sin el prefijo "Balda"/"Suelo") según el estilo de su
/// estantería: "1", "2"... o "A", "B"...
String textoBalda(int numero, String estiloBaldas) =>
    estiloBaldas == 'letra' ? letraDesdeIndice(numero) : numero.toString();

class Articulo {
  final int id;
  final String codigo;
  final String nombre;
  final String descripcion;
  final String unidad;
  final double stockActual;
  final double stockMinimo;
  final int? seccionId;
  final String? foto;
  final String ubicacion;

  Articulo({
    required this.id,
    required this.codigo,
    required this.nombre,
    required this.descripcion,
    required this.unidad,
    required this.stockActual,
    required this.stockMinimo,
    required this.seccionId,
    required this.foto,
    required this.ubicacion,
  });

  bool get bajoMinimo => stockActual <= 0 || stockActual < stockMinimo;

  factory Articulo.fromJson(Map<String, dynamic> j) => Articulo(
        id: j['id'],
        codigo: j['codigo'] ?? '',
        nombre: j['nombre'] ?? '',
        descripcion: j['descripcion'] ?? '',
        unidad: j['unidad'] ?? '',
        stockActual: (j['stock_actual'] as num?)?.toDouble() ?? 0,
        stockMinimo: (j['stock_minimo'] as num?)?.toDouble() ?? 0,
        seccionId: j['seccion_id'],
        foto: (j['foto'] as String?)?.isEmpty == true ? null : j['foto'],
        ubicacion: j['ubicacion'] ?? '',
      );

  /// Copia con la cantidad actual ajustada en [delta]. Se usa para reflejar en
  /// pantalla, sin esperar al PC, un movimiento registrado sin conexión.
  Articulo conStockAjustado(double delta) => Articulo(
        id: id,
        codigo: codigo,
        nombre: nombre,
        descripcion: descripcion,
        unidad: unidad,
        stockActual: stockActual + delta,
        stockMinimo: stockMinimo,
        seccionId: seccionId,
        foto: foto,
        ubicacion: ubicacion,
      );
}

class Movimiento {
  final String fecha;
  final String tipo; // entrada | salida
  final double cantidad;
  final String usuarioNombre;
  final String motivo;

  Movimiento({
    required this.fecha,
    required this.tipo,
    required this.cantidad,
    required this.usuarioNombre,
    required this.motivo,
  });

  factory Movimiento.fromJson(Map<String, dynamic> j) => Movimiento(
        fecha: j['fecha'] ?? '',
        tipo: j['tipo'] ?? '',
        cantidad: (j['cantidad'] as num?)?.toDouble() ?? 0,
        usuarioNombre: j['usuario_nombre'] ?? '',
        motivo: j['motivo'] ?? '',
      );
}

/// Formatea una cantidad sin decimales sobrantes (3.0 -> "3", 3.5 -> "3.5").
String formatearCantidad(double v) {
  if (v == v.roundToDouble()) return v.toInt().toString();
  return v.toString();
}

/// Color del stock: rojo por debajo del mínimo, verde por encima, color por
/// defecto (null) si coincide exactamente con el mínimo.
Color? colorStock(double actual, double minimo) {
  if (actual < minimo) return Colors.redAccent;
  if (actual > minimo) return Colors.greenAccent;
  return null;
}
