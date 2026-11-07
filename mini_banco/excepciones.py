"""Excepciones propias del sistema.

Todas heredan de :class:`BancoError`, de modo que se pueden capturar de a una
o todas juntas con ``except BancoError``.
"""


class BancoError(Exception):
    """Error base de la aplicación."""


class DatoInvalidoError(BancoError):
    """Un dato ingresado no cumple el formato esperado."""


class MontoInvalidoError(BancoError):
    """El monto no es un número válido o no es mayor a cero."""


class SaldoInsuficienteError(BancoError):
    """La cuenta no tiene fondos suficientes para la operación."""


class LimiteExtraccionesError(BancoError):
    """Se superó el máximo de extracciones permitidas en el mes."""


class ClienteNoEncontradoError(BancoError):
    """No existe un cliente con el DNI indicado."""


class CuentaNoEncontradaError(BancoError):
    """No existe una cuenta con el número indicado."""


class DuplicadoError(BancoError):
    """Se intentó registrar un dato que ya existe."""


class OperacionInvalidaError(BancoError):
    """La operación no se puede realizar en el estado actual."""


class ReporteError(BancoError):
    """No se pudo generar o guardar el reporte PDF."""
