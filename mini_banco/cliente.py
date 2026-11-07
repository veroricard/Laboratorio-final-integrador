"""Clase ``Cliente``: persona titular de una o más cuentas."""

from mini_banco.excepciones import DatoInvalidoError
from mini_banco.validaciones import validar_dni, validar_texto


class Cliente:
    """Cliente del banco."""

    def __init__(self, nombre, dni):
        self.__nombre = validar_texto(nombre, "El nombre")
        self.__dni = validar_dni(dni)
        self.__cuentas = []

    # ---------- getters y setters ----------
    def get_nombre(self):
        return self.__nombre

    def set_nombre(self, nombre):
        self.__nombre = validar_texto(nombre, "El nombre")

    def get_dni(self):
        return self.__dni

    def set_dni(self, dni):
        self.__dni = validar_dni(dni)

    def get_cuentas(self):
        """Devuelve una copia de la lista de cuentas del cliente."""
        return list(self.__cuentas)

    def set_cuentas(self, cuentas):
        if not isinstance(cuentas, list):
            raise DatoInvalidoError("Las cuentas deben indicarse como lista.")
        self.__cuentas = list(cuentas)

    # ---------- comportamiento ----------
    def agregar_cuenta(self, cuenta):
        """Asocia una cuenta al cliente."""
        if cuenta is None:
            raise DatoInvalidoError("No se puede agregar una cuenta vacía.")
        self.__cuentas.append(cuenta)

    def get_saldo_total(self):
        """Suma de los saldos de todas las cuentas del cliente."""
        return round(sum(cuenta.get_saldo() for cuenta in self.__cuentas), 2)

    def __str__(self):
        return f"{self.__nombre} (DNI {self.__dni})"
