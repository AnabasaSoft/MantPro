# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# MantPro - Sistema de Mantenimiento Preventivo
# Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft) <anabasasoft@gmail.com>
# https://github.com/AnabasaSoft/MantPro
#
# Este programa es software libre: puedes redistribuirlo y/o modificarlo bajo
# los términos de la Licencia Pública General Affero de GNU publicada por la
# Free Software Foundation, ya sea la versión 3 de la Licencia o (a tu
# elección) cualquier versión posterior.
#
# Este programa se distribuye con la esperanza de que sea útil, pero SIN
# NINGUNA GARANTÍA; ni siquiera la garantía implícita de COMERCIABILIDAD o
# IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Consulta la Licencia Pública
# General Affero de GNU para más detalles.
#
# Deberías haber recibido una copia de la Licencia Pública General Affero de
# GNU junto con este programa. Si no, consulta <https://www.gnu.org/licenses/>.

"""
certificado.py — Certificado TLS propio del servidor de sincronización.

La primera vez que arranca, MantPro genera un certificado autofirmado y su
clave en la carpeta de datos. Los móviles no lo validan contra ninguna
autoridad: confían en él porque su huella (SHA-256) les llega en el QR de
vinculación y la comparan en cada conexión («pinning»). Así la conexión va
cifrada y nadie en la red puede hacerse pasar por el PC.
"""

import datetime
import hashlib
import ipaddress
import os
import socket

from .rutas import DATA_DIR
from .seguridad import escribir_atomico

RUTA_CERTIFICADO = os.path.join(DATA_DIR, "servidor_cert.pem")
RUTA_CLAVE = os.path.join(DATA_DIR, "servidor_clave.pem")


def _generar():
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    clave = ec.generate_private_key(ec.SECP256R1())
    nombre = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, f"MantPro ({socket.gethostname()})"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MantPro"),
    ])
    ahora = datetime.datetime.now(datetime.timezone.utc)
    certificado = (
        x509.CertificateBuilder()
        .subject_name(nombre).issuer_name(nombre)
        .public_key(clave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora - datetime.timedelta(days=1))
        # La validez no se comprueba (va fijado por la huella); larga para no
        # tener que volver a vincular los móviles.
        .not_valid_after(ahora + datetime.timedelta(days=365 * 30))
        .add_extension(x509.SubjectAlternativeName([
            x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False)
        .sign(clave, hashes.SHA256())
    )
    escribir_atomico(RUTA_CLAVE, clave.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()), modo="wb")
    try:
        os.chmod(RUTA_CLAVE, 0o600)   # la clave privada, solo para el usuario
    except OSError:
        pass
    escribir_atomico(RUTA_CERTIFICADO, certificado.public_bytes(serialization.Encoding.PEM), modo="wb")


def asegurar_certificado():
    """Rutas (certificado, clave), generándolos si todavía no existen."""
    if not (os.path.exists(RUTA_CERTIFICADO) and os.path.exists(RUTA_CLAVE)):
        _generar()
    return RUTA_CERTIFICADO, RUTA_CLAVE


def huella_certificado(ruta=RUTA_CERTIFICADO):
    """Huella SHA-256 del certificado (de su forma DER), en hexadecimal en
    minúsculas y sin separadores: es lo que va en el QR."""
    import ssl
    with open(ruta, encoding="ascii") as f:
        der = ssl.PEM_cert_to_DER_cert(f.read())
    return hashlib.sha256(der).hexdigest()
