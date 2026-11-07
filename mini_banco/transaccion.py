"""Jerarquía de transacciones.

``Transaccion`` es una clase abstracta (abstracción) de la que heredan
``Deposito``, ``Extraccion``, ``Transferencia``, ``Interes`` y ``Comision``.
Cada subclase redefine ``_aplicar``, ``get_tipo``, ``descripcion`` y
``efecto_sobre`` (polimorfismo).
"""

from abc import ABC, abstractmethod
from datetime import datetime

from mini_banco.excepciones import DatoInvalidoError, OperacionInvalidaError
from mini_banco.validaciones import validar_monto


class Transaccion(ABC):
    """Operación que modifica el saldo de una o más cuentas."""

    __siguiente_id = 1

    def __init__(self, cuenta_origen, monto, fecha=None):
        if cuenta_origen is None:
            raise DatoInvalidoError("La transacción necesita una cuenta.")
        self.__id = Transaccion._nuevo_id()
        self.__cuenta_origen = cuenta_origen
        self.__monto = validar_monto(monto)
        self.__fecha = fecha if fecha is not None else datetime.now()
        self.__ejecutada = False

    # ---------- contador de ids ----------
    @classmethod
    def _nuevo_id(cls):
        """Devuelve el próximo id correlativo."""
        nuevo = Transaccion.__siguiente_id
        Transaccion.__siguiente_id += 1
        return nuevo

    @classmethod
    def reiniciar_contador(cls):
        """Vuelve el contador de ids a 1 (útil para las pruebas)."""
        Transaccion.__siguiente_id = 1

    # ---------- getters y setters ----------
    def get_id(self):
        return self.__id

    def get_cuenta_origen(self):
        return self.__cuenta_origen

    def set_cuenta_origen(self, cuenta):
        self._verificar_no_ejecutada()
        if cuenta is None:
            raise DatoInvalidoError("La transacción necesita una cuenta.")
        self.__cuenta_origen = cuenta

    def get_monto(self):
        return self.__monto

    def set_monto(self, monto):
        self._verificar_no_ejecutada()
        self.__monto = validar_monto(monto)

    def get_fecha(self):
        return self.__fecha

    def set_fecha(self, fecha):
        if not isinstance(fecha, datetime):
            raise DatoInvalidoError("La fecha debe ser un objeto datetime.")
        self.__fecha = fecha

    def fue_ejecutada(self):
        return self.__ejecutada

    # ---------- comportamiento común ----------
    def _verificar_no_ejecutada(self):
        if self.__ejecutada:
            raise OperacionInvalidaError("No se puede modificar una transacción ya ejecutada.")

    def cuentas_involucradas(self):
        """Cuentas que participan de la transacción (por defecto, solo la de origen)."""
        return [self.__cuenta_origen]

    def ejecutar(self):
        """Aplica la transacción y la registra en el historial de las cuentas (método plantilla)."""
        if self.__ejecutada:
            raise OperacionInvalidaError("La transacción ya fue ejecutada.")
        self._aplicar()
        self.__ejecutada = True
        for cuenta in self.cuentas_involucradas():
            cuenta.registrar_movimiento(self)

    def a_fila(self):
        """Datos de la transacción listos para mostrar en una tabla."""
        return [
            self.__id,
            self.__fecha.strftime("%d/%m/%Y %H:%M"),
            self.get_tipo(),
            self.descripcion(),
            self.__monto,
        ]

    # ---------- métodos que redefine cada subclase ----------
    @abstractmethod
    def get_tipo(self):
        """Nombre legible del tipo de transacción."""

    @abstractmethod
    def descripcion(self):
        """Texto que describe la operación."""

    @abstractmethod
    def efecto_sobre(self, cuenta):
        """Variación (con signo) que la transacción produce en ``cuenta``."""

    @abstractmethod
    def _aplicar(self):
        """Modifica los saldos de las cuentas."""


class Deposito(Transaccion):
    """Ingreso de dinero en una cuenta."""

    def get_tipo(self):
        return "Depósito"

    def descripcion(self):
        return f"Depósito en {self.get_cuenta_origen().get_numero()}"

    def efecto_sobre(self, cuenta):
        return self.get_monto() if cuenta is self.get_cuenta_origen() else 0.0

    def _aplicar(self):
        self.get_cuenta_origen().acreditar(self.get_monto())


class Extraccion(Transaccion):
    """Retiro de dinero de una cuenta."""

    def get_tipo(self):
        return "Extracción"

    def descripcion(self):
        return f"Extracción de {self.get_cuenta_origen().get_numero()}"

    def efecto_sobre(self, cuenta):
        return -self.get_monto() if cuenta is self.get_cuenta_origen() else 0.0

    def _aplicar(self):
        self.get_cuenta_origen().debitar(self.get_monto())


class Transferencia(Transaccion):
    """Movimiento de dinero entre dos cuentas."""

    def __init__(self, cuenta_origen, cuenta_destino, monto, fecha=None):
        super().__init__(cuenta_origen, monto, fecha)
        if cuenta_destino is None:
            raise DatoInvalidoError("La transferencia necesita una cuenta de destino.")
        if cuenta_destino is cuenta_origen:
            raise DatoInvalidoError("La cuenta de origen y la de destino deben ser distintas.")
        self.__cuenta_destino = cuenta_destino

    def get_cuenta_destino(self):
        return self.__cuenta_destino

    def set_cuenta_destino(self, cuenta):
        self._verificar_no_ejecutada()
        if cuenta is None or cuenta is self.get_cuenta_origen():
            raise DatoInvalidoError("La cuenta de destino debe existir y ser distinta de la de origen.")
        self.__cuenta_destino = cuenta

    def get_tipo(self):
        return "Transferencia"

    def descripcion(self):
        origen = self.get_cuenta_origen().get_numero()
        destino = self.__cuenta_destino.get_numero()
        return f"Transferencia de {origen} a {destino}"

    def cuentas_involucradas(self):
        return [self.get_cuenta_origen(), self.__cuenta_destino]

    def efecto_sobre(self, cuenta):
        if cuenta is self.get_cuenta_origen():
            return -self.get_monto()
        if cuenta is self.__cuenta_destino:
            return self.get_monto()
        return 0.0

    def _aplicar(self):
        # Primero se debita: si falla, el destino no recibe nada.
        self.get_cuenta_origen().debitar(self.get_monto())
        self.__cuenta_destino.acreditar(self.get_monto())


class Interes(Transaccion):
    """Interés acreditado por el banco (cajas de ahorro)."""

    def get_tipo(self):
        return "Interés"

    def descripcion(self):
        return f"Interés mensual en {self.get_cuenta_origen().get_numero()}"

    def efecto_sobre(self, cuenta):
        return self.get_monto() if cuenta is self.get_cuenta_origen() else 0.0

    def _aplicar(self):
        self.get_cuenta_origen().acreditar(self.get_monto())


class Comision(Transaccion):
    """Cargo de mantenimiento cobrado por el banco (cuentas corrientes)."""

    def get_tipo(self):
        return "Comisión"

    def descripcion(self):
        return f"Comisión de mantenimiento de {self.get_cuenta_origen().get_numero()}"

    def efecto_sobre(self, cuenta):
        return -self.get_monto() if cuenta is self.get_cuenta_origen() else 0.0

    def _aplicar(self):
        self.get_cuenta_origen().aplicar_cargo(self.get_monto())
