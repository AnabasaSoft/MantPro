// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// MantPro Stock - Gestión de almacén
// Copyright (C) 2026 AnabasaSoft <anabasasoft@gmail.com>
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

// Mantiene la app viva en segundo plano (sincronizando y con el PC viéndola
// "En línea") mientras no se cierre del todo. Android congela las apps en
// segundo plano a los pocos segundos; la única forma fiable de seguir
// trabajando es un servicio en primer plano, que obliga a mostrar una
// notificación permanente ("MantPro Stock · Conectado al PC"). Al cerrar la app
// desde recientes el servicio se detiene solo (stopWithTask) y deja de gastar.
// El aviso diario de las 8:00 no depende de esto.

import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';

import 'i18n/strings.dart';

const String _idBotonCerrar = 'cerrar';

/// Punto de entrada del servicio (se ejecuta en su propio isolate). No hace
/// trabajo propio: la sincronización sigue en la app, a la que el servicio
/// solo mantiene viva. Reenvía a la app el botón "Cerrar" de la notificación.
@pragma('vm:entry-point')
void iniciarManejadorServicio() => FlutterForegroundTask.setTaskHandler(_ManejadorServicio());

class _ManejadorServicio extends TaskHandler {
  @override
  Future<void> onStart(DateTime timestamp, TaskStarter starter) async {}

  @override
  void onRepeatEvent(DateTime timestamp) {}

  @override
  Future<void> onDestroy(DateTime timestamp, bool isTimeout) async {}

  @override
  void onNotificationButtonPressed(String id) => FlutterForegroundTask.sendDataToMain(id);

  @override
  void onNotificationPressed() => FlutterForegroundTask.launchApp();
}

class ServicioConexion {
  static bool get _soportado => Platform.isAndroid;

  /// Llamar una vez en main(), antes de runApp().
  static void inicializar() {
    if (!_soportado) return;
    FlutterForegroundTask.initCommunicationPort();
    FlutterForegroundTask.init(
      androidNotificationOptions: AndroidNotificationOptions(
        channelId: 'conexion_pc',
        channelName: t('canal_conexion_pc'),
        channelDescription: t('canal_conexion_pc_desc'),
        channelImportance: NotificationChannelImportance.LOW,
        priority: NotificationPriority.LOW,
        onlyAlertOnce: true,
      ),
      iosNotificationOptions: const IOSNotificationOptions(showNotification: false),
      foregroundTaskOptions: ForegroundTaskOptions(
        eventAction: ForegroundTaskEventAction.nothing(),
        allowWakeLock: true,
        allowWifiLock: true,
        allowAutoRestart: false,
        stopWithTask: true,
      ),
    );
  }

  static String _texto(bool conectado) => conectado ? t('lbl_conectado_pc') : t('lbl_desconectado_pc');

  /// Arranca el servicio (o actualiza su texto si ya estaba en marcha).
  static Future<void> iniciar({required bool conectado}) async {
    if (!_soportado) return;
    if (await FlutterForegroundTask.isRunningService) {
      await actualizar(conectado);
      return;
    }
    await FlutterForegroundTask.startService(
      serviceId: 4102,
      serviceTypes: [ForegroundServiceTypes.connectedDevice],
      notificationTitle: 'MantPro Stock',
      notificationText: _texto(conectado),
      notificationButtons: [NotificationButton(id: _idBotonCerrar, text: t('btn_cerrar_app'))],
      callback: iniciarManejadorServicio,
    );
  }

  /// Cambia el texto de la notificación según haya o no conexión con el PC.
  static Future<void> actualizar(bool conectado) async {
    if (!_soportado || !await FlutterForegroundTask.isRunningService) return;
    await FlutterForegroundTask.updateService(notificationText: _texto(conectado));
  }

  static Future<void> detener() async {
    if (!_soportado || !await FlutterForegroundTask.isRunningService) return;
    await FlutterForegroundTask.stopService();
  }

  /// Escucha el botón "Cerrar" de la notificación: [alCerrar] avisa al PC de
  /// la desconexión; después se detiene el servicio y se cierra la app.
  static DataCallback? _escucha;

  static void escucharCerrar(Future<void> Function() alCerrar) {
    if (!_soportado) return;
    dejarDeEscuchar();
    _escucha = (dato) async {
      if (dato != _idBotonCerrar) return;
      await alCerrar();
      await detener();
      await SystemNavigator.pop();
    };
    FlutterForegroundTask.addTaskDataCallback(_escucha!);
  }

  static void dejarDeEscuchar() {
    if (_escucha != null) FlutterForegroundTask.removeTaskDataCallback(_escucha!);
    _escucha = null;
  }
}
