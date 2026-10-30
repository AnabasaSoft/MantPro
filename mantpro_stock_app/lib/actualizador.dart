// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later

/// Descarga e instalación de una actualización desde la propia app: baja el
/// APK de la release de GitHub con una barra de progreso y abre el
/// instalador de Android (MainActivity, canal "mantpro/actualizador").
/// Android siempre pide al usuario que confirme la instalación, y la primera
/// vez, que permita a la app instalar aplicaciones.
///
/// Este fichero es igual en mantenimiento_app y mantpro_stock_app.
library;

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:url_launcher/url_launcher.dart';
import 'i18n/strings.dart';

const _canal = MethodChannel('mantpro/actualizador');

/// Descarga [nombreApk] de la release ([datosRelease], el JSON de la API de
/// GitHub) y lo instala. Si la release no trae ese APK o algo falla, ofrece
/// abrir la página de la release como antes.
Future<void> descargarEInstalar(BuildContext context, Map<String, dynamic> datosRelease, String nombreApk) async {
  final urlRelease = (datosRelease['html_url'] ?? '').toString();
  final asset = ((datosRelease['assets'] as List?) ?? [])
      .whereType<Map>()
      .firstWhere((a) => a['name'] == nombreApk, orElse: () => {});
  final urlApk = (asset['browser_download_url'] ?? '').toString();
  if (urlApk.isEmpty) {
    if (urlRelease.isNotEmpty) await launchUrl(Uri.parse(urlRelease), mode: LaunchMode.externalApplication);
    return;
  }

  final progreso = ValueNotifier<double?>(null);
  var cancelado = false;
  final navegador = Navigator.of(context, rootNavigator: true);
  showDialog(
    context: context,
    barrierDismissible: false,
    builder: (ctx) => PopScope(
      canPop: false,
      child: AlertDialog(
        title: Text(t('msg_descargando_actualizacion')),
        content: ValueListenableBuilder<double?>(
          valueListenable: progreso,
          builder: (_, valor, __) => Column(mainAxisSize: MainAxisSize.min, children: [
            LinearProgressIndicator(value: valor),
            const SizedBox(height: 8),
            Text(valor == null ? '' : '${(valor * 100).round()} %'),
          ]),
        ),
        actions: [
          TextButton(onPressed: () { cancelado = true; navegador.pop(); }, child: Text(t('btn_cancelar'))),
        ],
      ),
    ),
  );

  final cliente = http.Client();
  try {
    final dir = Directory('${(await getTemporaryDirectory()).path}/actualizaciones');
    if (await dir.exists()) await dir.delete(recursive: true); // APK de actualizaciones anteriores
    await dir.create(recursive: true);
    final fichero = File('${dir.path}/$nombreApk');
    final respuesta = await cliente.send(http.Request('GET', Uri.parse(urlApk)));
    if (respuesta.statusCode != 200) throw HttpException('HTTP ${respuesta.statusCode}');
    final total = respuesta.contentLength ?? 0;
    var recibidos = 0;
    final salida = fichero.openWrite();
    try {
      await for (final trozo in respuesta.stream) {
        if (cancelado) break;
        salida.add(trozo);
        recibidos += trozo.length;
        if (total > 0) progreso.value = recibidos / total;
      }
    } finally {
      await salida.close();
    }
    if (cancelado) return;
    navegador.pop();
    final estado = await _canal.invokeMethod<String>('instalar', {'ruta': fichero.path});
    if (estado == 'permiso' && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          duration: const Duration(seconds: 8), content: Text(t('msg_permiso_instalar_actualizacion'))));
    }
  } catch (e) {
    if (!cancelado) navegador.pop();
    if (!cancelado && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        duration: const Duration(seconds: 10),
        content: Text(t('msg_error_descarga_actualizacion')),
        action: urlRelease.isEmpty ? null : SnackBarAction(
            label: t('btn_abrir_github'),
            onPressed: () => launchUrl(Uri.parse(urlRelease), mode: LaunchMode.externalApplication)),
      ));
    }
  } finally {
    cliente.close();
  }
}
