"""Pruebas de Cuenta, CajaAhorro y CuentaCorriente."""

import pytest

from mini_banco.cliente import Cliente
from mini_banco.cuenta import CajaAhorro, Cuenta, CuentaCorriente
from mini_banco.excepciones import (
    DatoInvalidoError,
    LimiteExtraccionesError,
    MontoInvalidoError,
    SaldoInsuficienteError,
)
from mini_banco.transaccion import Comision, Interes, Transaccion


@pytest.fixture(autouse=True)
def reiniciar_ids():
    Transaccion.reiniciar_contador()


@pytest.fixture
def titular():
    return Cliente("Ana Gómez", "30123456")


@pytest.fixture
def ahorro(titular):
    return CajaAhorro("AH-0001", titular, 1000)


@pytest.fixture
def corriente(titular):
    return CuentaCorriente("CC-0001", titular, 1000)


class TestCuentaAbstracta:
    def test_no_se_puede_instanciar(self, titular):
        with pytest.raises(TypeError):
            Cuenta("X-1", titular)

    def test_las_subclases_son_cuentas(self, ahorro, corriente):
        assert isinstance(ahorro, Cuenta)
        assert isinstance(corriente, Cuenta)


class TestCreacion:
    def test_datos_iniciales(self, ahorro, titular):
        assert ahorro.get_numero() == "AH-0001"
        assert ahorro.get_titular() is titular
        assert ahorro.get_saldo() == 1000.0
        assert ahorro.get_movimientos() == []

    def test_saldo_inicial_por_defecto_es_cero(self, titular):
        assert CajaAhorro("AH-0002", titular).get_saldo() == 0.0

    def test_numero_numerico_se_convierte_a_texto(self, titular):
        assert CajaAhorro(123, titular).get_numero() == "123"

    def test_rechaza_titular_none(self):
        with pytest.raises(DatoInvalidoError):
            CajaAhorro("AH-1", None)

    def test_rechaza_numero_vacio(self, titular):
        with pytest.raises(DatoInvalidoError):
            CajaAhorro("  ", titular)

    def test_rechaza_saldo_inicial_negativo(self, titular):
        with pytest.raises(MontoInvalidoError):
            CajaAhorro("AH-1", titular, -5)


class TestSettersComunes:
    def test_set_numero(self, ahorro):
        ahorro.set_numero(" AH-9 ")
        assert ahorro.get_numero() == "AH-9"

    def test_set_numero_invalido(self, ahorro):
        with pytest.raises(DatoInvalidoError):
            ahorro.set_numero("")

    def test_set_titular(self, ahorro):
        otro = Cliente("Luis", "28456789")
        ahorro.set_titular(otro)
        assert ahorro.get_titular() is otro

    def test_set_titular_none(self, ahorro, titular):
        with pytest.raises(DatoInvalidoError):
            ahorro.set_titular(None)
        assert ahorro.get_titular() is titular

    def test_set_saldo(self, ahorro):
        ahorro.set_saldo(55.5)
        assert ahorro.get_saldo() == 55.5

    def test_set_saldo_invalido(self, ahorro):
        with pytest.raises(MontoInvalidoError):
            ahorro.set_saldo("mucho")

    def test_set_movimientos(self, ahorro):
        ahorro.set_movimientos(["a", "b"])
        assert ahorro.get_movimientos() == ["a", "b"]

    def test_set_movimientos_rechaza_no_lista(self, ahorro):
        with pytest.raises(DatoInvalidoError):
            ahorro.set_movimientos("x")

    def test_get_movimientos_devuelve_copia(self, ahorro):
        ahorro.get_movimientos().append("intruso")
        assert ahorro.get_movimientos() == []


class TestOperacionesComunes:
    def test_acreditar(self, ahorro):
        ahorro.acreditar(250.5)
        assert ahorro.get_saldo() == 1250.5

    def test_acreditar_rechaza_monto_invalido(self, ahorro):
        with pytest.raises(MontoInvalidoError):
            ahorro.acreditar(0)

    def test_debitar(self, ahorro):
        ahorro.debitar(400)
        assert ahorro.get_saldo() == 600.0

    def test_debitar_rechaza_monto_invalido(self, ahorro):
        with pytest.raises(MontoInvalidoError):
            ahorro.debitar(-1)

    def test_aplicar_cargo_puede_dejar_saldo_negativo(self, ahorro):
        ahorro.aplicar_cargo(1500)
        assert ahorro.get_saldo() == -500.0

    def test_aplicar_cargo_rechaza_monto_invalido(self, ahorro):
        with pytest.raises(MontoInvalidoError):
            ahorro.aplicar_cargo(0)

    def test_aplicar_cargo_no_cuenta_como_extraccion(self, ahorro):
        ahorro.aplicar_cargo(10)
        assert ahorro.get_extracciones_mes() == 0

    def test_registrar_movimiento(self, ahorro):
        ahorro.registrar_movimiento("mov")
        assert ahorro.get_movimientos() == ["mov"]

    def test_str(self, ahorro):
        assert str(ahorro) == "Caja de Ahorro AH-0001 - saldo 1000.00"


class TestCajaAhorro:
    def test_valores_por_defecto(self, ahorro):
        assert ahorro.get_tasa_interes() == 0.01
        assert ahorro.get_limite_extracciones() == 5
        assert ahorro.get_extracciones_mes() == 0

    def test_tipo_y_saldo_disponible(self, ahorro):
        assert ahorro.get_tipo() == "Caja de Ahorro"
        assert ahorro.get_saldo_disponible() == 1000.0

    def test_condiciones(self, ahorro):
        assert ahorro.get_condiciones() == "Interés mensual 1.0 %, hasta 5 extracciones por mes"

    def test_set_tasa_interes(self, ahorro):
        ahorro.set_tasa_interes(0.02)
        assert ahorro.get_tasa_interes() == 0.02

    def test_set_tasa_interes_negativa(self, ahorro):
        with pytest.raises(MontoInvalidoError):
            ahorro.set_tasa_interes(-0.1)

    def test_tasa_inicial_negativa(self, titular):
        with pytest.raises(MontoInvalidoError):
            CajaAhorro("AH-1", titular, tasa_interes=-1)

    def test_set_limite_extracciones(self, ahorro):
        ahorro.set_limite_extracciones(3)
        assert ahorro.get_limite_extracciones() == 3

    @pytest.mark.parametrize("limite", [0, -1, 2.5, "3", True, None])
    def test_limite_invalido(self, ahorro, limite):
        with pytest.raises(DatoInvalidoError):
            ahorro.set_limite_extracciones(limite)

    def test_limite_inicial_invalido(self, titular):
        with pytest.raises(DatoInvalidoError):
            CajaAhorro("AH-1", titular, limite_extracciones=0)

    def test_set_extracciones_mes(self, ahorro):
        ahorro.set_extracciones_mes(2)
        assert ahorro.get_extracciones_mes() == 2

    @pytest.mark.parametrize("cantidad", [-1, 1.5, "2", True])
    def test_extracciones_mes_invalidas(self, ahorro, cantidad):
        with pytest.raises(DatoInvalidoError):
            ahorro.set_extracciones_mes(cantidad)

    def test_debitar_cuenta_una_extraccion(self, ahorro):
        ahorro.debitar(100)
        assert ahorro.get_extracciones_mes() == 1

    def test_no_permite_saldo_negativo(self, ahorro):
        with pytest.raises(SaldoInsuficienteError):
            ahorro.debitar(1000.01)
        assert ahorro.get_saldo() == 1000.0
        assert ahorro.get_extracciones_mes() == 0

    def test_permite_extraer_todo_el_saldo(self, ahorro):
        ahorro.debitar(1000)
        assert ahorro.get_saldo() == 0.0

    def test_supera_el_limite_de_extracciones(self, ahorro):
        for _ in range(5):
            ahorro.debitar(10)
        with pytest.raises(LimiteExtraccionesError):
            ahorro.debitar(10)
        assert ahorro.get_saldo() == 950.0

    def test_cierre_mensual_acredita_interes(self, ahorro):
        interes = ahorro.cierre_mensual()
        assert isinstance(interes, Interes)
        assert interes.get_monto() == 10.0
        assert ahorro.get_saldo() == 1010.0
        assert ahorro.get_movimientos() == [interes]

    def test_cierre_mensual_reinicia_extracciones(self, ahorro):
        ahorro.debitar(10)
        ahorro.cierre_mensual()
        assert ahorro.get_extracciones_mes() == 0

    def test_cierre_mensual_sin_saldo_no_genera_interes(self, titular):
        vacia = CajaAhorro("AH-2", titular)
        assert vacia.cierre_mensual() is None
        assert vacia.get_movimientos() == []


class TestCuentaCorriente:
    def test_valores_por_defecto(self, corriente):
        assert corriente.get_descubierto() == 5000.0
        assert corriente.get_comision_mensual() == 150.0

    def test_tipo(self, corriente):
        assert corriente.get_tipo() == "Cuenta Corriente"

    def test_saldo_disponible_incluye_descubierto(self, corriente):
        assert corriente.get_saldo_disponible() == 6000.0

    def test_condiciones(self, corriente):
        assert corriente.get_condiciones() == "Descubierto de 5000.00, comisión mensual de 150.00"

    def test_set_descubierto(self, corriente):
        corriente.set_descubierto(100)
        assert corriente.get_descubierto() == 100.0

    def test_set_descubierto_negativo(self, corriente):
        with pytest.raises(MontoInvalidoError):
            corriente.set_descubierto(-1)

    def test_set_comision(self, corriente):
        corriente.set_comision_mensual(99)
        assert corriente.get_comision_mensual() == 99.0

    def test_set_comision_negativa(self, corriente):
        with pytest.raises(MontoInvalidoError):
            corriente.set_comision_mensual(-1)

    def test_puede_quedar_en_descubierto(self, corriente):
        corriente.debitar(5000)
        assert corriente.get_saldo() == -4000.0

    def test_no_supera_el_descubierto(self, corriente):
        with pytest.raises(SaldoInsuficienteError):
            corriente.debitar(6000.01)
        assert corriente.get_saldo() == 1000.0

    def test_sin_limite_de_extracciones(self, corriente):
        for _ in range(20):
            corriente.debitar(10)
        assert corriente.get_saldo() == 800.0

    def test_cierre_mensual_cobra_comision(self, corriente):
        comision = corriente.cierre_mensual()
        assert isinstance(comision, Comision)
        assert corriente.get_saldo() == 850.0
        assert corriente.get_movimientos() == [comision]

    def test_cierre_mensual_sin_comision(self, titular):
        gratis = CuentaCorriente("CC-2", titular, 100, comision_mensual=0)
        assert gratis.cierre_mensual() is None
        assert gratis.get_saldo() == 100.0

    def test_comision_puede_dejar_saldo_en_descubierto(self, titular):
        cuenta = CuentaCorriente("CC-3", titular, 0)
        cuenta.cierre_mensual()
        assert cuenta.get_saldo() == -150.0


class TestPolimorfismo:
    def test_mismo_mensaje_distinto_resultado(self, ahorro, corriente):
        resultados = [cuenta.cierre_mensual() for cuenta in (ahorro, corriente)]
        assert isinstance(resultados[0], Interes)
        assert isinstance(resultados[1], Comision)
        assert ahorro.get_saldo() > 1000
        assert corriente.get_saldo() < 1000

    def test_saldo_disponible_cambia_segun_el_tipo(self, ahorro, corriente):
        assert ahorro.get_saldo_disponible() != corriente.get_saldo_disponible()