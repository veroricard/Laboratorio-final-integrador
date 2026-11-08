"""Fixtures compartidas por todas las pruebas."""

import pytest

from mini_banco.banco import Banco
from mini_banco.cliente import Cliente
from mini_banco.cuenta import CajaAhorro, CuentaCorriente
from mini_banco.transaccion import Transaccion


@pytest.fixture(autouse=True)
def reiniciar_ids():
    """Cada prueba arranca con el contador de transacciones en 1."""
    Transaccion.reiniciar_contador()


@pytest.fixture
def cliente():
    return Cliente("Ana Gómez", "30123456")


@pytest.fixture
def ahorro(cliente):
    return CajaAhorro("AH-0001", cliente, saldo_inicial=1000)


@pytest.fixture
def corriente(cliente):
    return CuentaCorriente("CC-0001", cliente, saldo_inicial=500)


@pytest.fixture
def banco():
    return Banco("Banco de prueba")


@pytest.fixture
def banco_con_datos(banco):
    banco.registrar_cliente("Ana Gómez", "30123456")
    banco.registrar_cliente("Luis Pérez", "28456789")
    banco.abrir_cuenta("30123456", "ahorro", 1000)
    banco.abrir_cuenta("28456789", "corriente", 500)
    return banco
