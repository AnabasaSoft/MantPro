// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// MantPro Stock - Gestión de almacén
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

/// Pruebas de las rutas del móvil (PC y nube): elección, respaldo, vuelta al PC, regla del 401 y QR.
/// Este fichero es igual en mantenimiento_app y mantpro_stock_app (solo cambia el paquete importado).
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:mantpro_stock_app/conexion_segura.dart';
import 'package:mantpro_stock_app/rutas_servidor.dart';

const pc = '192.168.1.20:5001';
const nube = 'mantpro-cloud.com/m/0123456789abcdef0123456789abcdef';
final qrNuevo = 'https://192.168.1.20:5001/?h=${'a' * 64}&p=5000&n=mantpro-cloud.com&e=0123456789abcdef0123456789abcdef';

void main() {
  late Map<String, bool> responde;
  late List<String> sondeos;
  late DateTime reloj;

  Future<String?> activa() async => (await SharedPreferences.getInstance()).getString('pc_ip_url');

  setUp(() async {
    SharedPreferences.setMockInitialValues({'pc_ip_url': pc, 'ruta_pc': pc, 'ruta_nube': nube});
    RutasServidor.reiniciarParaPruebas();
    responde = {pc: true, nube: true};
    sondeos = [];
    reloj = DateTime(2026, 11, 11, 10, 0, 0);
    RutasServidor.ahora = () => reloj;
    RutasServidor.sonda = (esquema, ruta, limite) async {
      sondeos.add(ruta);
      return responde[ruta] ?? false;
    };
  });

  group('elección de ruta', () {
    test('sin ruta de nube no se sondea nada ni se cambia nada (comportamiento de siempre)', () async {
      SharedPreferences.setMockInitialValues({'pc_ip_url': pc});
      await RutasServidor.resolver(forzar: true);
      await RutasServidor.alFallar();
      expect(sondeos, isEmpty);
      expect(await activa(), pc);
      expect(RutasServidor.enNube.value, false);
    });

    test('si el PC responde se usa el PC aunque la nube también', () async {
      await RutasServidor.resolver();
      expect(await activa(), pc);
      expect(RutasServidor.enNube.value, false);
      expect(sondeos, [pc]);                       // ni siquiera se molesta a la nube
    });

    test('si el PC no responde y la nube sí, se usa la nube y se recuerda el PC', () async {
      responde[pc] = false;
      await RutasServidor.resolver();
      expect(await activa(), nube);
      expect(RutasServidor.enNube.value, true);
      expect((await SharedPreferences.getInstance()).getString('ruta_pc'), pc);
    });

    test('si no responde ninguna no cambia nada y no insiste durante 20 s', () async {
      responde = {pc: false, nube: false};
      await RutasServidor.resolver();
      expect(await activa(), pc);
      final llamadas = sondeos.length;
      reloj = reloj.add(const Duration(seconds: 10));
      await RutasServidor.resolver();
      expect(sondeos.length, llamadas, reason: 'dentro de los 20 s no vuelve a sondear');
      reloj = reloj.add(const Duration(seconds: 11));
      await RutasServidor.resolver();
      expect(sondeos.length, greaterThan(llamadas), reason: 'pasados los 20 s sí');
    });

    test('con la nube activa, el PC se vuelve a probar cada minuto y se vuelve a él', () async {
      responde[pc] = false;
      await RutasServidor.resolver();
      expect(RutasServidor.enNube.value, true);
      responde[pc] = true;
      sondeos.clear();
      reloj = reloj.add(const Duration(seconds: 30));
      await RutasServidor.tictac();
      expect(sondeos, isEmpty, reason: 'antes del minuto no se sondea');
      expect(RutasServidor.enNube.value, true);
      reloj = reloj.add(const Duration(seconds: 31));
      await RutasServidor.tictac();
      expect(await activa(), pc);
      expect(RutasServidor.enNube.value, false);
    });

    test('con el PC activo, tictac no hace nada', () async {
      await RutasServidor.tictac();
      expect(sondeos, isEmpty);
    });

    test('al fallar la ruta activa: de la nube vuelve al PC si responde, o se queda en la nube', () async {
      responde[pc] = false;
      await RutasServidor.resolver();                 // nube activa
      reloj = reloj.add(const Duration(seconds: 30));
      responde[pc] = true;
      await RutasServidor.alFallar();
      expect(await activa(), pc, reason: 'el PC ha vuelto');
      responde = {pc: false, nube: true};
      reloj = reloj.add(const Duration(seconds: 30));
      await RutasServidor.alFallar();
      expect(await activa(), nube);
    });

    test('alFallar no se repite más de una vez cada 5 s', () async {
      responde = {pc: false, nube: false};
      await RutasServidor.alFallar();
      final llamadas = sondeos.length;
      reloj = reloj.add(const Duration(seconds: 2));
      await RutasServidor.alFallar();
      expect(sondeos.length, llamadas);
    });

    test('si otra parte de la app reescribe la ruta del PC (p. ej. al pasar a HTTPS) se respeta', () async {
      SharedPreferences.setMockInitialValues({'pc_ip_url': '192.168.1.20:5002', 'ruta_pc': pc, 'ruta_nube': nube});
      responde = {'192.168.1.20:5002': true, pc: false, nube: true};
      await RutasServidor.resolver();
      expect(await activa(), '192.168.1.20:5002');
    });
  });

  group('códigos que significan «esta ruta no puede ahora»', () {
    test('402, 502, 503 y 504 sí', () {
      for (final c in [402, 502, 503, 504]) {
        expect(RutasServidor.esFalloDeRuta(c), true, reason: '$c');
      }
    });
    test('403 (sin permiso: la cola se descartaría), 501 (fotos), 401, 400, 404, 500 y 200 no', () {
      for (final c in [403, 501, 401, 400, 404, 500, 200]) {
        expect(RutasServidor.esFalloDeRuta(c), false, reason: '$c');
      }
    });
  });

  group('un 401 de la nube justo después de entrar', () {
    test('en el PC nunca está en gracia', () async {
      await RutasServidor.marcarInicioSesion();
      expect(await RutasServidor.sesionEnGracia(), false);
    });

    test('en la nube, entrando con el PC hace 5 min: en gracia; hace 16 min: ya no', () async {
      await RutasServidor.marcarInicioSesion();       // entra con el PC
      responde[pc] = false;
      await RutasServidor.resolver();                 // pasa a la nube
      reloj = reloj.add(const Duration(minutes: 5));
      expect(await RutasServidor.sesionEnGracia(), true);
      reloj = reloj.add(const Duration(minutes: 11));
      expect(await RutasServidor.sesionEnGracia(), false, reason: 'pasado el cuarto de hora un 401 es real');
    });

    test('si se entró en la propia nube, un 401 es real desde el primer momento', () async {
      responde[pc] = false;
      await RutasServidor.resolver();
      await RutasServidor.marcarInicioSesion();       // entra con la nube
      expect(await RutasServidor.sesionEnGracia(), false);
    });
  });

  group('QR de vinculación', () {
    test('el QR nuevo guarda el PC y la nube, y empieza por el PC', () async {
      final ruta = await guardarVinculacion(qrNuevo);
      expect(ruta, pc);
      final p = await SharedPreferences.getInstance();
      expect(p.getString('ruta_nube'), nube);
      expect(p.getString('pc_ip_url'), pc);
      expect(RutasServidor.enNube.value, false);
      expect(await RutasServidor.hayNube(), true);
    });

    test('un QR sin ruta de nube (PC sin sesión o antiguo) olvida la nube anterior', () async {
      expect(await RutasServidor.hayNube(), true);
      final ruta = await guardarVinculacion('https://192.168.1.30:5001/?h=${'b' * 64}&p=5000');
      expect(ruta, '192.168.1.30:5001');
      expect(await RutasServidor.hayNube(), false);
    });

    test('rutaNubeDelQr solo admite un dominio y un uuid de 32 hexadecimales', () {
      Uri u(String q) => Uri.parse('https://x:1/?h=a&$q');
      expect(rutaNubeDelQr(u('n=mantpro-cloud.com&e=0123456789abcdef0123456789abcdef')), nube);
      expect(rutaNubeDelQr(u('n=mantpro-cloud.com')), null);
      expect(rutaNubeDelQr(u('e=0123456789abcdef0123456789abcdef')), null);
      expect(rutaNubeDelQr(u('n=evil.com/x&e=0123456789abcdef0123456789abcdef')), null, reason: 'un camino en el dominio no vale');
      expect(rutaNubeDelQr(u('n=a@evil.com&e=0123456789abcdef0123456789abcdef')), null);
      expect(rutaNubeDelQr(u('n=mantpro-cloud.com&e=0123456789ABCDEF0123456789abcdef')), null);
      expect(rutaNubeDelQr(u('n=mantpro-cloud.com&e=../../etc')), null);
    });
  });
}
