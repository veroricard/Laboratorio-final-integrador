import pytest

from mini_banco.cliente import Cliente
from mini_banco.excepciones import DatoInvalidoError


def test_crear_cliente_valido(cliente):
    assert cliente.get_nombre() == "Ana Gómez"
    assert cliente.get_dni() == "30123456"
    assert cliente.get_cuentas() == []


@pytest.mark.parametrize("nombre, dni", [("", "30123456"), ("Ana", "abc"), ("  ", "30123456")])
def test_crear_cliente_invalido(nombre, dni):
    with pytest.raises(DatoInvalidoError):
        Cliente(nombre, dni)


def test_set_nombre(cliente):
    cliente.set_nombre("  Ana María  ")
    assert cliente.get_nombre() == "Ana María"


def test_set_nombre_vacio(cliente):
    with pytest.raises(DatoInvalidoError):
        cliente.set_nombre("")


def test_set_dni(cliente):
    cliente.set_dni("40.111.222")
    assert cliente.get_dni() == "40111222"


def test_set_dni_invalido(cliente):
    with pytest.raises(DatoInvalidoError):
        cliente.set_dni("12")


def test_agregar_cuenta_y_get_cuentas(cliente, ahorro):
    cliente.agregar_cuenta(ahorro)
    assert cliente.get_cuentas() == [ahorro]


def test_get_cuentas_devuelve_copia(cliente, ahorro):
    cliente.agregar_cuenta(ahorro)
    cliente.get_cuentas().clear()
    assert len(cliente.get_cuentas()) == 1


def test_agregar_cuenta_none(cliente):
    with pytest.raises(DatoInvalidoError):
        cliente.agregar_cuenta(None)


def test_set_cuentas(cliente, ahorro, corriente):
    cliente.set_cuentas([ahorro, corriente])
    assert cliente.get_cuentas() == [ahorro, corriente]


def test_set_cuentas_no_lista(cliente):
    with pytest.raises(DatoInvalidoError):
        cliente.set_cuentas("no es lista")


def test_get_saldo_total(cliente, ahorro, corriente):
    cliente.set_cuentas([ahorro, corriente])
    assert cliente.get_saldo_total() == 1500


def test_get_saldo_total_sin_cuentas(cliente):
    assert cliente.get_saldo_total() == 0


def test_str(cliente):
    assert str(cliente) == "Ana Gómez (DNI 30123456)"


def test_atributos_privados(cliente):
    for atributo in ("nombre", "dni", "cuentas", "__nombre", "__dni", "__cuentas"):
        assert not hasattr(cliente, atributo)
