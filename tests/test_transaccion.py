"""Pruebas de Transaccion y sus subclases."""

from datetime import datetime

import pytest

from mini_banco.cliente import Cliente
from mini_banco.cuenta import CajaAhorro, CuentaCorriente
from mini_banco.excepciones import (
    DatoInvalidoError,
    MontoInvalidoError,
    OperacionInvalidaError,
    SaldoInsuficienteError,
)
from mini_banco.transaccion import (
    Comision,
    Deposito,
    Extraccion,
    Interes,
    Transaccion,
    Transferencia,
)


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
    return CuentaCorriente("CC-0001", titular, 500)


class TestTransaccionBase:
    def test_es_abstracta(self, ahorro):
        with pytest.raises(TypeError):
            Transaccion(ahorro, 10)

    def test_ids_correlativos(self, ahorro):
        a = Deposito(ahorro, 10)
        b = Deposito(ahorro, 10)
        assert (a.get_id(), b.get_id()) == (1, 2)

    def test_reiniciar_contador(self, ahorro):
        Deposito(ahorro, 10)
        Transaccion.reiniciar_contador()
        assert Deposito(ahorro, 10).get_id() == 1

    def test_datos_iniciales(self, ahorro):
        dep = Deposito(ahorro, 10.5)
        assert dep.get_cuenta_origen() is ahorro
        assert dep.get_monto() == 10.5
        assert isinstance(dep.get_fecha(), datetime)
        assert dep.fue_ejecutada() is False

    def test_fecha_personalizada(self, ahorro):
        fecha = datetime(2026, 1, 15, 10, 30)
        assert Deposito(ahorro, 10, fecha).get_fecha() == fecha

    def test_rechaza_cuenta_none(self):
        with pytest.raises(DatoInvalidoError):
            Deposito(None, 10)

    @pytest.mark.parametrize("monto", [0, -5, "abc", None])
    def test_rechaza_monto_invalido(self, ahorro, monto):
        with pytest.raises(MontoInvalidoError):
            Deposito(ahorro, monto)

    def test_set_cuenta_origen(self, ahorro, corriente):
        dep = Deposito(ahorro, 10)
        dep.set_cuenta_origen(corriente)
        assert dep.get_cuenta_origen() is corriente

    def test_set_cuenta_origen_none(self, ahorro):
        with pytest.raises(DatoInvalidoError):
            Deposito(ahorro, 10).set_cuenta_origen(None)

    def test_set_monto(self, ahorro):
        dep = Deposito(ahorro, 10)
        dep.set_monto(99)
        assert dep.get_monto() == 99.0

    def test_set_monto_invalido(self, ahorro):
        with pytest.raises(MontoInvalidoError):
            Deposito(ahorro, 10).set_monto(0)

    def test_set_fecha(self, ahorro):
        dep = Deposito(ahorro, 10)
        nueva = datetime(2025, 5, 5)
        dep.set_fecha(nueva)
        assert dep.get_fecha() == nueva

    def test_set_fecha_invalida(self, ahorro):
        with pytest.raises(DatoInvalidoError):
            Deposito(ahorro, 10).set_fecha("hoy")

    def test_cuentas_involucradas_por_defecto(self, ahorro):
        assert Deposito(ahorro, 10).cuentas_involucradas() == [ahorro]

    def test_a_fila(self, ahorro):
        fecha = datetime(2026, 3, 9, 14, 5)
        fila = Deposito(ahorro, 10, fecha).a_fila()
        assert fila == [1, "09/03/2026 14:05", "Depósito", "Depósito en AH-0001", 10.0]


class TestEjecucion:
    def test_ejecutar_marca_y_registra(self, ahorro):
        dep = Deposito(ahorro, 10)
        dep.ejecutar()
        assert dep.fue_ejecutada() is True
        assert ahorro.get_movimientos() == [dep]

    def test_no_se_ejecuta_dos_veces(self, ahorro):
        dep = Deposito(ahorro, 10)
        dep.ejecutar()
        with pytest.raises(OperacionInvalidaError):
            dep.ejecutar()
        assert ahorro.get_saldo() == 1010.0

    def test_no_se_modifica_tras_ejecutar(self, ahorro, corriente):
        dep = Deposito(ahorro, 10)
        dep.ejecutar()
        with pytest.raises(OperacionInvalidaError):
            dep.set_monto(5)
        with pytest.raises(OperacionInvalidaError):
            dep.set_cuenta_origen(corriente)

    def test_si_falla_no_queda_ejecutada_ni_registrada(self, ahorro):
        ext = Extraccion(ahorro, 5000)
        with pytest.raises(SaldoInsuficienteError):
            ext.ejecutar()
        assert ext.fue_ejecutada() is False
        assert ahorro.get_movimientos() == []


class TestDeposito:
    def test_efecto(self, ahorro, corriente):
        dep = Deposito(ahorro, 100)
        dep.ejecutar()
        assert ahorro.get_saldo() == 1100.0
        assert dep.get_tipo() == "Depósito"
        assert dep.efecto_sobre(ahorro) == 100.0
        assert dep.efecto_sobre(corriente) == 0.0


class TestExtraccion:
    def test_efecto(self, ahorro, corriente):
        ext = Extraccion(ahorro, 100)
        ext.ejecutar()
        assert ahorro.get_saldo() == 900.0
        assert ext.get_tipo() == "Extracción"
        assert ext.descripcion() == "Extracción de AH-0001"
        assert ext.efecto_sobre(ahorro) == -100.0
        assert ext.efecto_sobre(corriente) == 0.0


class TestTransferencia:
    def test_mueve_dinero(self, ahorro, corriente):
        tr = Transferencia(ahorro, corriente, 300)
        tr.ejecutar()
        assert ahorro.get_saldo() == 700.0
        assert corriente.get_saldo() == 800.0

    def test_se_registra_en_ambas_cuentas(self, ahorro, corriente):
        tr = Transferencia(ahorro, corriente, 300)
        tr.ejecutar()
        assert ahorro.get_movimientos() == [tr]
        assert corriente.get_movimientos() == [tr]

    def test_descripcion_y_tipo(self, ahorro, corriente):
        tr = Transferencia(ahorro, corriente, 1)
        assert tr.get_tipo() == "Transferencia"
        assert tr.descripcion() == "Transferencia de AH-0001 a CC-0001"

    def test_efecto_segun_la_cuenta(self, ahorro, corriente, titular):
        tr = Transferencia(ahorro, corriente, 300)
        ajena = CajaAhorro("AH-9", titular)
        assert tr.efecto_sobre(ahorro) == -300.0
        assert tr.efecto_sobre(corriente) == 300.0
        assert tr.efecto_sobre(ajena) == 0.0

    def test_cuentas_involucradas(self, ahorro, corriente):
        assert Transferencia(ahorro, corriente, 1).cuentas_involucradas() == [ahorro, corriente]

    def test_destino_none(self, ahorro):
        with pytest.raises(DatoInvalidoError):
            Transferencia(ahorro, None, 10)

    def test_origen_igual_a_destino(self, ahorro):
        with pytest.raises(DatoInvalidoError):
            Transferencia(ahorro, ahorro, 10)

    def test_set_cuenta_destino(self, ahorro, corriente, titular):
        tr = Transferencia(ahorro, corriente, 10)
        otra = CajaAhorro("AH-5", titular)
        tr.set_cuenta_destino(otra)
        assert tr.get_cuenta_destino() is otra

    def test_set_cuenta_destino_invalida(self, ahorro, corriente):
        tr = Transferencia(ahorro, corriente, 10)
        with pytest.raises(DatoInvalidoError):
            tr.set_cuenta_destino(None)
        with pytest.raises(DatoInvalidoError):
            tr.set_cuenta_destino(ahorro)

    def test_set_cuenta_destino_tras_ejecutar(self, ahorro, corriente, titular):
        tr = Transferencia(ahorro, corriente, 10)
        tr.ejecutar()
        with pytest.raises(OperacionInvalidaError):
            tr.set_cuenta_destino(CajaAhorro("AH-5", titular))

    def test_si_falla_el_debito_el_destino_no_recibe(self, ahorro, corriente):
        tr = Transferencia(ahorro, corriente, 5000)
        with pytest.raises(SaldoInsuficienteError):
            tr.ejecutar()
        assert corriente.get_saldo() == 500.0
        assert corriente.get_movimientos() == []


class TestInteres:
    def test_efecto(self, ahorro, corriente):
        interes = Interes(ahorro, 10)
        interes.ejecutar()
        assert ahorro.get_saldo() == 1010.0
        assert interes.get_tipo() == "Interés"
        assert interes.descripcion() == "Interés mensual en AH-0001"
        assert interes.efecto_sobre(ahorro) == 10.0
        assert interes.efecto_sobre(corriente) == 0.0


class TestComision:
    def test_efecto(self, corriente, ahorro):
        comision = Comision(corriente, 150)
        comision.ejecutar()
        assert corriente.get_saldo() == 350.0
        assert comision.get_tipo() == "Comisión"
        assert comision.descripcion() == "Comisión de mantenimiento de CC-0001"
        assert comision.efecto_sobre(corriente) == -150.0
        assert comision.efecto_sobre(ahorro) == 0.0

    def test_no_cuenta_como_extraccion(self, ahorro):
        Comision(ahorro, 10).ejecutar()
        assert ahorro.get_extracciones_mes() == 0


class TestPolimorfismo:
    def test_cada_tipo_responde_distinto(self, ahorro, corriente):
        transacciones = [
            Deposito(ahorro, 10),
            Extraccion(ahorro, 10),
            Transferencia(ahorro, corriente, 10),
            Interes(ahorro, 10),
            Comision(ahorro, 10),
        ]
        tipos = [t.get_tipo() for t in transacciones]
        assert len(set(tipos)) == 5
        efectos = [t.efecto_sobre(ahorro) for t in transacciones]
        assert efectos == [10.0, -10.0, -10.0, 10.0, -10.0]