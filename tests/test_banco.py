"""Pruebas de la clase Banco."""

import pytest

from mini_banco.banco import Banco
from mini_banco.cliente import Cliente
from mini_banco.cuenta import CajaAhorro, CuentaCorriente
from mini_banco.excepciones import (
    ClienteNoEncontradoError,
    CuentaNoEncontradaError,
    DatoInvalidoError,
    DuplicadoError,
    LimiteExtraccionesError,
    MontoInvalidoError,
    SaldoInsuficienteError,
)
from mini_banco.transaccion import Comision, Deposito, Interes, Transaccion


@pytest.fixture(autouse=True)
def reiniciar_ids():
    Transaccion.reiniciar_contador()


@pytest.fixture
def banco():
    b = Banco("Banco Test")
    b.registrar_cliente("Ana Gómez", "30123456")
    b.registrar_cliente("Luis Pérez", "28456789")
    return b


class TestBasicos:
    def test_nombre_por_defecto(self):
        assert Banco().get_nombre() == "Mini Banco"

    def test_nombre_invalido(self):
        with pytest.raises(DatoInvalidoError):
            Banco("  ")

    def test_set_nombre(self):
        b = Banco()
        b.set_nombre(" Otro ")
        assert b.get_nombre() == "Otro"

    def test_set_nombre_invalido(self):
        with pytest.raises(DatoInvalidoError):
            Banco().set_nombre("")

    def test_empieza_vacio(self):
        b = Banco()
        assert b.get_clientes() == []
        assert b.get_cuentas() == []
        assert b.get_transacciones() == []

    def test_getters_devuelven_copias(self, banco):
        banco.get_clientes().append("x")
        banco.get_cuentas().append("x")
        banco.get_transacciones().append("x")
        assert len(banco.get_clientes()) == 2
        assert banco.get_cuentas() == []
        assert banco.get_transacciones() == []

    def test_set_clientes(self):
        b = Banco()
        cliente = Cliente("Ana", "30123456")
        b.set_clientes([cliente])
        assert b.get_clientes() == [cliente]

    def test_set_cuentas(self, banco):
        cuenta = CajaAhorro("AH-1", banco.buscar_cliente("30123456"))
        banco.set_cuentas([cuenta])
        assert banco.get_cuentas() == [cuenta]

    def test_set_transacciones(self, banco):
        banco.set_transacciones([])
        assert banco.get_transacciones() == []

    @pytest.mark.parametrize("setter", ["set_clientes", "set_cuentas", "set_transacciones"])
    def test_setters_rechazan_no_listas(self, setter):
        with pytest.raises(DatoInvalidoError):
            getattr(Banco(), setter)("no es lista")


class TestClientes:
    def test_registrar(self):
        b = Banco()
        cliente = b.registrar_cliente("Ana", "30123456")
        assert b.get_clientes() == [cliente]

    def test_dni_duplicado(self, banco):
        with pytest.raises(DuplicadoError):
            banco.registrar_cliente("Otra Ana", "30.123.456")
        assert len(banco.get_clientes()) == 2

    def test_datos_invalidos_no_se_guardan(self, banco):
        with pytest.raises(DatoInvalidoError):
            banco.registrar_cliente("", "11111111")
        with pytest.raises(DatoInvalidoError):
            banco.registrar_cliente("Ok", "123")
        assert len(banco.get_clientes()) == 2

    def test_buscar_cliente(self, banco):
        assert banco.buscar_cliente("30123456").get_nombre() == "Ana Gómez"

    def test_buscar_cliente_con_puntos(self, banco):
        assert banco.buscar_cliente("30.123.456").get_nombre() == "Ana Gómez"

    def test_buscar_cliente_inexistente(self, banco):
        with pytest.raises(ClienteNoEncontradoError):
            banco.buscar_cliente("11111111")

    def test_buscar_cliente_dni_invalido(self, banco):
        with pytest.raises(DatoInvalidoError):
            banco.buscar_cliente("abc")


class TestCuentas:
    def test_abrir_caja_ahorro(self, banco):
        cuenta = banco.abrir_cuenta("30123456", "ahorro")
        assert isinstance(cuenta, CajaAhorro)
        assert cuenta.get_numero() == "AH-0001"

    def test_abrir_cuenta_corriente(self, banco):
        cuenta = banco.abrir_cuenta("30123456", "corriente")
        assert isinstance(cuenta, CuentaCorriente)
        assert cuenta.get_numero() == "CC-0001"

    def test_tipo_no_distingue_mayusculas(self, banco):
        assert isinstance(banco.abrir_cuenta("30123456", " AHORRO "), CajaAhorro)

    def test_numeracion_correlativa(self, banco):
        banco.abrir_cuenta("30123456", "ahorro")
        segunda = banco.abrir_cuenta("28456789", "corriente")
        assert segunda.get_numero() == "CC-0002"

    def test_se_asocia_al_cliente(self, banco):
        cuenta = banco.abrir_cuenta("30123456", "ahorro")
        assert banco.buscar_cliente("30123456").get_cuentas() == [cuenta]

    def test_con_saldo_inicial_genera_deposito(self, banco):
        cuenta = banco.abrir_cuenta("30123456", "ahorro", 5000)
        assert cuenta.get_saldo() == 5000.0
        assert len(banco.get_transacciones()) == 1
        assert isinstance(banco.get_transacciones()[0], Deposito)

    def test_sin_saldo_inicial_no_genera_transaccion(self, banco):
        banco.abrir_cuenta("30123456", "ahorro")
        assert banco.get_transacciones() == []

    def test_tipo_desconocido(self, banco):
        with pytest.raises(DatoInvalidoError):
            banco.abrir_cuenta("30123456", "plazo fijo")
        assert banco.get_cuentas() == []

    def test_tipo_vacio(self, banco):
        with pytest.raises(DatoInvalidoError):
            banco.abrir_cuenta("30123456", "")

    def test_cliente_inexistente(self, banco):
        with pytest.raises(ClienteNoEncontradoError):
            banco.abrir_cuenta("11111111", "ahorro")

    def test_saldo_inicial_negativo(self, banco):
        with pytest.raises(MontoInvalidoError):
            banco.abrir_cuenta("30123456", "ahorro", -1)
        assert banco.get_cuentas() == []

    def test_buscar_cuenta(self, banco):
        cuenta = banco.abrir_cuenta("30123456", "ahorro")
        assert banco.buscar_cuenta("AH-0001") is cuenta

    def test_buscar_cuenta_ignora_mayusculas_y_espacios(self, banco):
        cuenta = banco.abrir_cuenta("30123456", "ahorro")
        assert banco.buscar_cuenta(" ah-0001 ") is cuenta

    def test_buscar_cuenta_inexistente(self, banco):
        with pytest.raises(CuentaNoEncontradaError):
            banco.buscar_cuenta("AH-9999")

    def test_buscar_cuenta_vacia(self, banco):
        with pytest.raises(DatoInvalidoError):
            banco.buscar_cuenta("")


class TestTransacciones:
    @pytest.fixture
    def con_cuentas(self, banco):
        banco.abrir_cuenta("30123456", "ahorro", 1000)
        banco.abrir_cuenta("28456789", "corriente", 500)
        banco.set_transacciones([])
        return banco

    def test_depositar(self, con_cuentas):
        con_cuentas.depositar("AH-0001", 250)
        assert con_cuentas.buscar_cuenta("AH-0001").get_saldo() == 1250.0
        assert len(con_cuentas.get_transacciones()) == 1

    def test_extraer(self, con_cuentas):
        con_cuentas.extraer("AH-0001", 250)
        assert con_cuentas.buscar_cuenta("AH-0001").get_saldo() == 750.0

    def test_transferir(self, con_cuentas):
        con_cuentas.transferir("AH-0001", "CC-0002", 400)
        assert con_cuentas.buscar_cuenta("AH-0001").get_saldo() == 600.0
        assert con_cuentas.buscar_cuenta("CC-0002").get_saldo() == 900.0

    def test_devuelven_la_transaccion(self, con_cuentas):
        assert con_cuentas.depositar("AH-0001", 10).fue_ejecutada()

    def test_operacion_fallida_no_se_guarda(self, con_cuentas):
        with pytest.raises(SaldoInsuficienteError):
            con_cuentas.extraer("AH-0001", 99999)
        assert con_cuentas.get_transacciones() == []

    def test_transferencia_fallida_no_se_guarda(self, con_cuentas):
        with pytest.raises(SaldoInsuficienteError):
            con_cuentas.transferir("AH-0001", "CC-0002", 99999)
        assert con_cuentas.get_transacciones() == []
        assert con_cuentas.buscar_cuenta("CC-0002").get_saldo() == 500.0

    def test_cuenta_inexistente(self, con_cuentas):
        with pytest.raises(CuentaNoEncontradaError):
            con_cuentas.depositar("XX-1", 10)
        with pytest.raises(CuentaNoEncontradaError):
            con_cuentas.transferir("AH-0001", "XX-1", 10)

    def test_monto_invalido(self, con_cuentas):
        with pytest.raises(MontoInvalidoError):
            con_cuentas.depositar("AH-0001", 0)

    def test_limite_de_extracciones_de_caja_de_ahorro(self, con_cuentas):
        for _ in range(5):
            con_cuentas.extraer("AH-0001", 1)
        with pytest.raises(LimiteExtraccionesError):
            con_cuentas.extraer("AH-0001", 1)

    def test_movimientos_de(self, con_cuentas):
        dep = con_cuentas.depositar("AH-0001", 10)
        movimientos = con_cuentas.movimientos_de("AH-0001")
        assert movimientos[-1] is dep
        assert len(movimientos) == 2

    def test_movimientos_de_cuenta_inexistente(self, con_cuentas):
        with pytest.raises(CuentaNoEncontradaError):
            con_cuentas.movimientos_de("XX-1")


class TestCierreMensual:
    def test_aplica_intereses_y_comisiones(self, banco):
        banco.abrir_cuenta("30123456", "ahorro", 1000)
        banco.abrir_cuenta("28456789", "corriente", 1000)
        banco.set_transacciones([])
        generadas = banco.cierre_mensual()
        assert len(generadas) == 2
        assert isinstance(generadas[0], Interes)
        assert isinstance(generadas[1], Comision)
        assert banco.get_transacciones() == generadas
        assert banco.buscar_cuenta("AH-0001").get_saldo() == 1010.0
        assert banco.buscar_cuenta("CC-0002").get_saldo() == 850.0

    def test_sin_cuentas_no_genera_nada(self, banco):
        assert banco.cierre_mensual() == []

    def test_cuentas_sin_efecto_no_generan_transacciones(self, banco):
        banco.abrir_cuenta("30123456", "ahorro")
        assert banco.cierre_mensual() == []


class TestConsultas:
    def test_saldo_total(self, banco):
        banco.abrir_cuenta("30123456", "ahorro", 1000.25)
        banco.abrir_cuenta("28456789", "corriente", 500.50)
        assert banco.get_saldo_total() == 1500.75

    def test_saldo_total_vacio(self):
        assert Banco().get_saldo_total() == 0

    def test_resumen(self, banco):
        banco.abrir_cuenta("30123456", "ahorro", 1000)
        assert banco.resumen() == {
            "clientes": 2,
            "cuentas": 1,
            "transacciones": 1,
            "saldo_total": 1000.0,
        }