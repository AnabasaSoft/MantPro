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

/// Botón «🌐 ES» para cambiar el idioma (los 8 de MantPro) desde la ventana de avisos y la vinculación, sin
/// tener que abrir el panel del administrador: cada operario puede ponerla en el suyo.
library;

import 'package:flutter/material.dart';
import 'i18n/strings.dart';
import 'tema.dart';

class BotonIdioma extends StatelessWidget {
  const BotonIdioma({super.key, this.alAbrir, this.alCerrar});

  /// Para que el quiosco no limpie el formulario por inactividad mientras el menú está abierto.
  final VoidCallback? alAbrir;
  final VoidCallback? alCerrar;

  @override
  Widget build(BuildContext context) {
    final k = TokensTema.de(context);
    return ValueListenableBuilder<String>(
      valueListenable: idiomaNotifier,
      builder: (context, idioma, _) => PopupMenuButton<String>(
        tooltip: t('dlg_idioma_titulo'),
        initialValue: idioma,
        color: k.superficie,
        onOpened: alAbrir,
        onCanceled: alCerrar,
        onSelected: (codigo) {
          alCerrar?.call();
          cambiarIdioma(codigo);
        },
        itemBuilder: (_) => [
          for (final i in idiomasDisponibles)
            PopupMenuItem<String>(
              value: i['codigo']!,
              child: Text(i['nombre']!,
                  style: TextStyle(
                      color: k.texto, fontWeight: i['codigo'] == idioma ? FontWeight.bold : FontWeight.normal)),
            ),
        ],
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
          decoration: BoxDecoration(
            color: k.superficie,
            border: Border.all(color: k.borde),
            borderRadius: BorderRadius.circular(5),
          ),
          child: Text('🌐 ${idioma.toUpperCase()}', style: TextStyle(fontSize: 0.85 * rem, color: k.texto)),
        ),
      ),
    );
  }
}
