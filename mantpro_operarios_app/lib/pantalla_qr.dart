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

// Lector del QR de vinculación del PC (devuelve el texto leído).
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'i18n/strings.dart';

class PantallaQr extends StatefulWidget {
  const PantallaQr({super.key});
  @override
  State<PantallaQr> createState() => _PantallaQrState();
}

class _PantallaQrState extends State<PantallaQr> {
  bool _leido = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(t('title_qr'))),
      body: MobileScanner(onDetect: (captura) {
        if (!_leido && captura.barcodes.isNotEmpty && captura.barcodes.first.rawValue != null) {
          setState(() => _leido = true);
          Navigator.pop(context, captura.barcodes.first.rawValue!);
        }
      }),
    );
  }
}
