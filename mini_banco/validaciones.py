"""Funciones de validación reutilizables."""

import math

from mini_banco.excepciones import DatoInvalidoError, MontoInvalidoError


def validar_numero(valor):
    """Verifica que ``valor`` sea un número finito (int o float) y lo devuelve como float redondeado."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise MontoInvalidoError("El valor debe ser un número.")
    if not math.isfinite(valor):
        raise MontoInvalidoError("El valor debe ser un número finito.")
    return round(float(valor), 2)


def validar_monto(monto):
    """Verifica que ``monto`` sea un número mayor a cero."""
    monto = validar_numero(monto)
    if monto <= 0:
        raise MontoInvalidoError("El monto debe ser mayor a cero.")
    return monto


def validar_no_negativo(valor):
    """Verifica que ``valor`` sea un número mayor o igual a cero."""
    valor = validar_numero(valor)
    if valor < 0:
        raise MontoInvalidoError("El valor no puede ser negativo.")
    return valor


def validar_texto(texto, campo="El campo"):
    """Verifica que ``texto`` sea un string no vacío y lo devuelve sin espacios sobrantes."""
    if not isinstance(texto, str) or not texto.strip():
        raise DatoInvalidoError(f"{campo} no puede estar vacío.")
    return texto.strip()


def validar_dni(dni):
    """Verifica que el DNI tenga 7 u 8 dígitos (se aceptan puntos como separador)."""
    if isinstance(dni, int) and not isinstance(dni, bool):
        dni = str(dni)
    if not isinstance(dni, str):
        raise DatoInvalidoError("El DNI debe ser un texto o un número.")
    limpio = dni.strip().replace(".", "")
    if not limpio.isdigit() or len(limpio) not in (7, 8):
        raise DatoInvalidoError("El DNI debe tener 7 u 8 dígitos numéricos.")
    return limpio
