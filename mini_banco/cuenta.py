"""Jerarquía de cuentas.

``Cuenta`` es abstracta; ``CajaAhorro`` y ``CuentaCorriente`` la especializan
redefiniendo ``get_tipo``, ``get_saldo_disponible``, ``get_condiciones``,
``validar_debito`` y ``cierre_mensual`` (polimorfismo).
"""

from abc import ABC, abstractmethod

from mini_banco.excepciones import (
    DatoInvalidoError,
    LimiteExtraccionesError,
    SaldoInsuficienteError,
)
from mini_banco.transaccion import Comision, Interes
from mini_banco.validaciones import (
    validar_monto,
    validar_no_negativo,
    validar_numero,
    validar_texto,
)


class Cuenta(ABC):
    """Cuenta bancaria genérica."""

    def __init__(self, numero, titular, saldo_inicial=0.0):
        if titular is None:
            raise DatoInvalidoError("La cuenta necesita un titular.")
        self.__numero = validar_texto(str(numero), "El número de cuenta")
        self.__titular = titular
        self.__saldo = validar_no_negativo(saldo_inicial)
        self.__movimientos = []

    # ---------- getters y setters ----------
    def get_numero(self):
        return self.__numero

    def set_numero(self, numero):
        self.__numero = validar_texto(str(numero), "El número de cuenta")

    def get_titular(self):
        return self.__titular

    def set_titular(self, titular):
        if titular is None:
            raise DatoInvalidoError("La cuenta necesita un titular.")
        self.__titular = titular

    def get_saldo(self):
        return self.__saldo

    def set_saldo(self, saldo):
        self.__saldo = validar_numero(saldo)

    def get_movimientos(self):
        """Devuelve una copia del historial de movimientos."""
        return list(self.__movimientos)

    def set_movimientos(self, movimientos):
        if not isinstance(movimientos, list):
            raise DatoInvalidoError("Los movimientos deben indicarse como lista.")
        self.__movimientos = list(movimientos)

    # ---------- operaciones comunes ----------
    def acreditar(self, monto):
        """Suma ``monto`` al saldo."""
        monto = validar_monto(monto)
        self.__saldo = round(self.__saldo + monto, 2)

    def debitar(self, monto):
        """Resta ``monto`` del saldo, respetando las reglas de cada tipo de cuenta."""
        monto = validar_monto(monto)
        self.validar_debito(monto)
        self.__saldo = round(self.__saldo - monto, 2)
        self._despues_de_debitar()

    def aplicar_cargo(self, monto):
        """Descuenta un cargo del banco (comisión) sin aplicar los controles de extracción."""
        monto = validar_monto(monto)
        self.__saldo = round(self.__saldo - monto, 2)

    def registrar_movimiento(self, transaccion):
        """Agrega una transacción ejecutada al historial."""
        self.__movimientos.append(transaccion)

    def validar_debito(self, monto):
        """Lanza un error si no se puede debitar ``monto`` (las subclases agregan reglas)."""
        if monto > self.get_saldo_disponible():
            raise SaldoInsuficienteError(
                f"Saldo insuficiente en {self.__numero}: disponible {self.get_saldo_disponible():.2f}."
            )

    def _despues_de_debitar(self):
        """Gancho que se ejecuta tras un débito exitoso (las subclases pueden redefinirlo)."""

    def __str__(self):
        return f"{self.get_tipo()} {self.__numero} - saldo {self.__saldo:.2f}"

    # ---------- métodos que redefine cada subclase ----------
    @abstractmethod
    def get_tipo(self):
        """Nombre legible del tipo de cuenta."""

    @abstractmethod
    def get_saldo_disponible(self):
        """Dinero que realmente se puede retirar."""

    @abstractmethod
    def get_condiciones(self):
        """Texto con las condiciones particulares de la cuenta."""

    @abstractmethod
    def cierre_mensual(self):
        """Aplica el proceso de fin de mes y devuelve la transacción generada (o ``None``)."""


class CajaAhorro(Cuenta):
    """Caja de ahorro: paga interés y limita las extracciones mensuales."""

    def __init__(self, numero, titular, saldo_inicial=0.0, tasa_interes=0.01, limite_extracciones=5):
        super().__init__(numero, titular, saldo_inicial)
        self.__tasa_interes = validar_no_negativo(tasa_interes)
        self.__limite_extracciones = self._validar_limite(limite_extracciones)
        self.__extracciones_mes = 0

    @staticmethod
    def _validar_limite(limite):
        if isinstance(limite, bool) or not isinstance(limite, int) or limite < 1:
            raise DatoInvalidoError("El límite de extracciones debe ser un entero mayor o igual a 1.")
        return limite

    def get_tasa_interes(self):
        return self.__tasa_interes

    def set_tasa_interes(self, tasa):
        self.__tasa_interes = validar_no_negativo(tasa)

    def get_limite_extracciones(self):
        return self.__limite_extracciones

    def set_limite_extracciones(self, limite):
        self.__limite_extracciones = self._validar_limite(limite)

    def get_extracciones_mes(self):
        return self.__extracciones_mes

    def set_extracciones_mes(self, cantidad):
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad < 0:
            raise DatoInvalidoError("La cantidad de extracciones debe ser un entero no negativo.")
        self.__extracciones_mes = cantidad

    def get_tipo(self):
        return "Caja de Ahorro"

    def get_saldo_disponible(self):
        return self.get_saldo()

    def get_condiciones(self):
        return (
            f"Interés mensual {self.__tasa_interes * 100:.1f} %, "
            f"hasta {self.__limite_extracciones} extracciones por mes"
        )

    def validar_debito(self, monto):
        if self.__extracciones_mes >= self.__limite_extracciones:
            raise LimiteExtraccionesError(
                f"Se alcanzó el límite de {self.__limite_extracciones} extracciones mensuales."
            )
        super().validar_debito(monto)

    def _despues_de_debitar(self):
        self.__extracciones_mes += 1

    def cierre_mensual(self):
        """Acredita el interés del mes y reinicia el contador de extracciones."""
        self.__extracciones_mes = 0
        monto = round(self.get_saldo() * self.__tasa_interes, 2)
        if monto <= 0:
            return None
        interes = Interes(self, monto)
        interes.ejecutar()
        return interes


class CuentaCorriente(Cuenta):
    """Cuenta corriente: permite sobregiro y cobra una comisión mensual."""

    def __init__(self, numero, titular, saldo_inicial=0.0, descubierto=5000.0, comision_mensual=150.0):
        super().__init__(numero, titular, saldo_inicial)
        self.__descubierto = validar_no_negativo(descubierto)
        self.__comision_mensual = validar_no_negativo(comision_mensual)

    def get_descubierto(self):
        return self.__descubierto

    def set_descubierto(self, descubierto):
        self.__descubierto = validar_no_negativo(descubierto)

    def get_comision_mensual(self):
        return self.__comision_mensual

    def set_comision_mensual(self, comision):
        self.__comision_mensual = validar_no_negativo(comision)

    def get_tipo(self):
        return "Cuenta Corriente"

    def get_saldo_disponible(self):
        return round(self.get_saldo() + self.__descubierto, 2)

    def get_condiciones(self):
        return (
            f"Descubierto de {self.__descubierto:.2f}, "
            f"comisión mensual de {self.__comision_mensual:.2f}"
        )

    def cierre_mensual(self):
        """Cobra la comisión de mantenimiento (si es mayor a cero)."""
        if self.__comision_mensual <= 0:
            return None
        comision = Comision(self, self.__comision_mensual)
        comision.ejecutar()
        return comision
