"""Pruebas de la carga de datos de ejemplo."""

import pytest

from mini_banco.banco import Banco
from mini_banco.datos_demo import cargar_datos_demo
from mini_banco.excepciones import DuplicadoError
from mini_banco.transaccion import Transaccion


@pytest.fixture(autouse=True)
def reiniciar_ids():
    Transaccion.reiniciar_contador()


def test_carga_clientes_y_cuentas():
    banco = Banco()
    resumen = cargar_datos_demo(banco)
    assert resumen["clientes"] == 3
    assert resumen["cuentas"] == 4


def test_genera_movimientos():
    banco = Banco()
    resumen = cargar_datos_demo(banco)
    assert resumen["transacciones"] == 7


def test_devuelve_el_resumen_del_banco():
    banco = Banco()
    assert cargar_datos_demo(banco) == banco.resumen()


def test_saldos_esperados():
    banco = Banco()
    cargar_datos_demo(banco)
    assert banco.buscar_cuenta("AH-0001").get_saldo() == 46500.0
    assert banco.buscar_cuenta("CC-0002").get_saldo() == 16000.0
    assert banco.buscar_cuenta("AH-0003").get_saldo() == 20000.0
    assert banco.buscar_cuenta("CC-0004").get_saldo() == 12000.0


def test_no_se_puede_cargar_dos_veces():
    banco = Banco()
    cargar_datos_demo(banco)
    with pytest.raises(DuplicadoError):
        cargar_datos_demo(banco)