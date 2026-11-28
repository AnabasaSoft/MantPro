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

/// Formato de fechas: el euskera escribe la fecha corta como AAAA/MM/DD; el
/// resto de idiomas, como DD/MM/AAAA.
String _dos(int n) => n.toString().padLeft(2, '0');

String formatearFecha(DateTime f, String idioma) => idioma == 'eu'
    ? '${f.year}/${_dos(f.month)}/${_dos(f.day)}'
    : '${_dos(f.day)}/${_dos(f.month)}/${f.year}';

String formatearFechaHora(DateTime f, String idioma) => '${formatearFecha(f, idioma)} ${_dos(f.hour)}:${_dos(f.minute)}';
