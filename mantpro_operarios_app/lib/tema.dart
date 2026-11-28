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

// Colores y medidas de la ventana de avisos: los mismos tokens que la web
// (MantPro-Cloud/app_web/estaticos/web.css), que a su vez son los de los
// temas del PC. Oscuro por defecto.
import 'package:flutter/material.dart';

/// Tamaño del «rem» de la web (el del navegador, 16 px). El cuerpo usa 14 px.
const double rem = 16;
const double tamBase = 14;

/// Los 13 pt de los controles del formulario del quiosco (13 * 96 / 72).
const double tamControl = 13 * 96 / 72;

/// Colores que no cambian con el tema.
const Color colorVerde = Color(0xFF27AE60);
const Color colorRojo = Color(0xFFC0392B);
const Color colorFondoDialogo = Color(0x99000000);

/// Notificador del tema (true = oscuro). Lo escucha MaterialApp.
final ValueNotifier<bool> temaOscuroNotifier = ValueNotifier(true);

@immutable
class TokensTema extends ThemeExtension<TokensTema> {
  final Color fondo, texto, textoSuave, campo, superficie, superficieHover;
  final Color borde, bordeSuave, acento, sobreAcento, error, errorFondo;

  const TokensTema({
    required this.fondo,
    required this.texto,
    required this.textoSuave,
    required this.campo,
    required this.superficie,
    required this.superficieHover,
    required this.borde,
    required this.bordeSuave,
    required this.acento,
    required this.sobreAcento,
    required this.error,
    required this.errorFondo,
  });

  static const oscuro = TokensTema(
    fondo: Color(0xFF2B2B2B),
    texto: Color(0xFFE0E0E0),
    textoSuave: Color(0xFFB0B0B0),
    campo: Color(0xFF1E1E1E),
    superficie: Color(0xFF3C3C3C),
    superficieHover: Color(0xFF505050),
    borde: Color(0xFF555555),
    bordeSuave: Color(0xFF444444),
    acento: Color(0xFF3DAEE9),
    sobreAcento: Color(0xFFFFFFFF),
    error: Color(0xFFFF8A80),
    errorFondo: Color(0xFF4A2626),
  );

  static const claro = TokensTema(
    fondo: Color(0xFFF3F3F3),
    texto: Color(0xFF1E1E1E),
    textoSuave: Color(0xFF444444),
    campo: Color(0xFFFFFFFF),
    superficie: Color(0xFFE6E6E6),
    superficieHover: Color(0xFFD4D4D4),
    borde: Color(0xFFC0C0C0),
    bordeSuave: Color(0xFFD0D0D0),
    acento: Color(0xFF0078D4),
    sobreAcento: Color(0xFFFFFFFF),
    error: Color(0xFFB00020),
    errorFondo: Color(0xFFFDE7EA),
  );

  /// Los tokens del tema activo.
  static TokensTema de(BuildContext context) => Theme.of(context).extension<TokensTema>() ?? oscuro;

  @override
  TokensTema copyWith() => this;

  @override
  TokensTema lerp(ThemeExtension<TokensTema>? other, double t) => t < 0.5 ? this : (other as TokensTema? ?? this);
}

/// El ThemeData completo a partir de los tokens (oscuro o claro).
ThemeData construirTema(bool oscuro) {
  final k = oscuro ? TokensTema.oscuro : TokensTema.claro;
  final esquema = ColorScheme(
    brightness: oscuro ? Brightness.dark : Brightness.light,
    primary: k.acento,
    onPrimary: k.sobreAcento,
    secondary: k.acento,
    onSecondary: k.sobreAcento,
    error: k.error,
    onError: Colors.white,
    surface: k.superficie,
    onSurface: k.texto,
  );
  return ThemeData(
    useMaterial3: true,
    brightness: esquema.brightness,
    colorScheme: esquema,
    scaffoldBackgroundColor: k.fondo,
    canvasColor: k.fondo,
    extensions: [k],
    appBarTheme: AppBarTheme(
      backgroundColor: k.superficie,
      foregroundColor: k.texto,
      surfaceTintColor: Colors.transparent,
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: k.superficie,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8), side: BorderSide(color: k.borde)),
    ),
    cardTheme: CardThemeData(
      color: k.superficie,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6), side: BorderSide(color: k.bordeSuave)),
    ),
    dividerColor: k.bordeSuave,
    textTheme: ThemeData(brightness: esquema.brightness).textTheme.apply(bodyColor: k.texto, displayColor: k.texto),
    scrollbarTheme: ScrollbarThemeData(
      thumbColor: WidgetStatePropertyAll(k.borde),
      thickness: const WidgetStatePropertyAll(16),
      radius: const Radius.circular(10),
      thumbVisibility: const WidgetStatePropertyAll(true),
    ),
    snackBarTheme: SnackBarThemeData(backgroundColor: k.superficieHover, contentTextStyle: TextStyle(color: k.texto)),
  );
}
