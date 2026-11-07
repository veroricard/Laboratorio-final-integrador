"""Clase ``Banco``: coordina clientes, cuentas y transacciones.

Los datos se guardan en listas (arreglos) en memoria.
"""

from mini_banco.cliente import Cliente
from mini_banco.cuenta import CajaAhorro, CuentaCorriente
from mini_banco.excepciones import (
    ClienteNoEncontradoError,
    CuentaNoEncontradaError,
    DatoInvalidoError,
    DuplicadoError,
)
from mini_banco.transaccion import Deposito, Extraccion, Transferencia
from mini_banco.validaciones import validar_dni, validar_no_negativo, validar_texto

TIPOS_CUENTA = {
    "ahorro": ("AH", CajaAhorro),
    "corriente": ("CC", CuentaCorriente),
}


class Banco:
    """Entidad principal del sistema."""

    def __init__(self, nombre="Mini Banco"):
        self.__nombre = validar_texto(nombre, "El nombre del banco")
        self.__clientes = []
        self.__cuentas = []
        self.__transacciones = []

    # ---------- getters y setters ----------
    def get_nombre(self):
        return self.__nombre

    def set_nombre(self, nombre):
        self.__nombre = validar_texto(nombre, "El nombre del banco")

    def get_clientes(self):
        return list(self.__clientes)

    def get_cuentas(self):
        return list(self.__cuentas)

    def get_transacciones(self):
        return list(self.__transacciones)

    def set_clientes(self, clientes):
        if not isinstance(clientes, list):
            raise DatoInvalidoError("Los clientes deben indicarse como lista.")
        self.__clientes = list(clientes)

    def set_cuentas(self, cuentas):
        if not isinstance(cuentas, list):
            raise DatoInvalidoError("Las cuentas deben indicarse como lista.")
        self.__cuentas = list(cuentas)

    def set_transacciones(self, transacciones):
        if not isinstance(transacciones, list):
            raise DatoInvalidoError("Las transacciones deben indicarse como lista.")
        self.__transacciones = list(transacciones)

    # ---------- clientes ----------
    def registrar_cliente(self, nombre, dni):
        """Crea y guarda un cliente nuevo. El DNI no puede repetirse."""
        cliente = Cliente(nombre, dni)
        if any(c.get_dni() == cliente.get_dni() for c in self.__clientes):
            raise DuplicadoError(f"Ya existe un cliente con el DNI {cliente.get_dni()}.")
        self.__clientes.append(cliente)
        return cliente

    def buscar_cliente(self, dni):
        """Devuelve el cliente con ese DNI o lanza ``ClienteNoEncontradoError``."""
        dni = validar_dni(dni)
        for cliente in self.__clientes:
            if cliente.get_dni() == dni:
                return cliente
        raise ClienteNoEncontradoError(f"No existe un cliente con el DNI {dni}.")

    # ---------- cuentas ----------
    def abrir_cuenta(self, dni, tipo, saldo_inicial=0.0):
        """Abre una cuenta ('ahorro' o 'corriente') para el cliente indicado."""
        cliente = self.buscar_cliente(dni)
        tipo = validar_texto(tipo, "El tipo de cuenta").lower()
        if tipo not in TIPOS_CUENTA:
            raise DatoInvalidoError("El tipo de cuenta debe ser 'ahorro' o 'corriente'.")
        saldo_inicial = validar_no_negativo(saldo_inicial)
        prefijo, clase = TIPOS_CUENTA[tipo]
        numero = f"{prefijo}-{len(self.__cuentas) + 1:04d}"
        cuenta = clase(numero, cliente)
        cliente.agregar_cuenta(cuenta)
        self.__cuentas.append(cuenta)
        if saldo_inicial > 0:
            self.depositar(numero, saldo_inicial)
        return cuenta

    def buscar_cuenta(self, numero):
        """Devuelve la cuenta con ese número o lanza ``CuentaNoEncontradaError``."""
        numero = validar_texto(str(numero), "El número de cuenta").upper()
        for cuenta in self.__cuentas:
            if cuenta.get_numero() == numero:
                return cuenta
        raise CuentaNoEncontradaError(f"No existe la cuenta {numero}.")

    # ---------- transacciones ----------
    def _ejecutar_y_guardar(self, transaccion):
        transaccion.ejecutar()
        self.__transacciones.append(transaccion)
        return transaccion

    def depositar(self, numero, monto):
        return self._ejecutar_y_guardar(Deposito(self.buscar_cuenta(numero), monto))

    def extraer(self, numero, monto):
        return self._ejecutar_y_guardar(Extraccion(self.buscar_cuenta(numero), monto))

    def transferir(self, numero_origen, numero_destino, monto):
        origen = self.buscar_cuenta(numero_origen)
        destino = self.buscar_cuenta(numero_destino)
        return self._ejecutar_y_guardar(Transferencia(origen, destino, monto))

    def cierre_mensual(self):
        """Aplica el cierre mensual a todas las cuentas y devuelve las transacciones generadas."""
        generadas = []
        for cuenta in self.__cuentas:
            transaccion = cuenta.cierre_mensual()
            if transaccion is not None:
                self.__transacciones.append(transaccion)
                generadas.append(transaccion)
        return generadas

    def movimientos_de(self, numero):
        """Historial de movimientos de una cuenta."""
        return self.buscar_cuenta(numero).get_movimientos()

    # ---------- consultas ----------
    def get_saldo_total(self):
        return round(sum(c.get_saldo() for c in self.__cuentas), 2)

    def resumen(self):
        """Datos generales del sistema."""
        return {
            "clientes": len(self.__clientes),
            "cuentas": len(self.__cuentas),
            "transacciones": len(self.__transacciones),
            "saldo_total": self.get_saldo_total(),
        }
