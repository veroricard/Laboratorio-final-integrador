"""Menú interactivo por consola."""

import os
from datetime import datetime

from mini_banco.datos_demo import cargar_datos_demo
from mini_banco.excepciones import BancoError, MontoInvalidoError
from mini_banco.reportes import formatear_monto, generar_pdf

LINEA = "=" * 52


class Menu:
    """Interfaz de texto para usar el banco.

    ``entrada`` y ``salida`` se pueden reemplazar para probar el menú sin teclado.
    """

    def __init__(self, banco, entrada=None, salida=None, carpeta_reportes="reportes"):
        self.__banco = banco
        # Se resuelven al usarse (no al definir la clase) para poder reemplazarlos en pruebas.
        self.__entrada = entrada if entrada is not None else (lambda mensaje: input(mensaje))
        self.__salida = salida if salida is not None else (lambda texto: print(texto))
        self.__carpeta_reportes = carpeta_reportes

    # ---------- getters y setters ----------
    def get_banco(self):
        return self.__banco

    def set_banco(self, banco):
        self.__banco = banco

    def get_carpeta_reportes(self):
        return self.__carpeta_reportes

    def set_carpeta_reportes(self, carpeta):
        self.__carpeta_reportes = carpeta

    # ---------- entrada y salida ----------
    def mostrar(self, texto=""):
        self.__salida(texto)

    def leer_texto(self, mensaje):
        """Lee una línea de texto sin espacios sobrantes."""
        return self.__entrada(mensaje).strip()

    def leer_monto(self, mensaje):
        """Lee un monto; acepta coma o punto decimal."""
        texto = self.leer_texto(mensaje).replace(",", ".")
        try:
            return float(texto)
        except ValueError:
            raise MontoInvalidoError(f"'{texto}' no es un monto válido.") from None

    def mostrar_opciones(self):
        self.mostrar(f"\n{LINEA}\n  {self.__banco.get_nombre().upper()}\n{LINEA}")
        for clave, (titulo, _) in self._opciones().items():
            self.mostrar(f"  {clave:>2}. {titulo}")
        self.mostrar(LINEA)

    # ---------- opciones ----------
    def opcion_registrar_cliente(self):
        nombre = self.leer_texto("Nombre completo: ")
        dni = self.leer_texto("DNI (7 u 8 dígitos): ")
        cliente = self.__banco.registrar_cliente(nombre, dni)
        self.mostrar(f"Cliente registrado: {cliente}")

    def opcion_listar_clientes(self):
        clientes = self.__banco.get_clientes()
        if not clientes:
            self.mostrar("No hay clientes registrados.")
            return
        for cliente in clientes:
            self.mostrar(
                f"- {cliente} | cuentas: {len(cliente.get_cuentas())} | "
                f"saldo total: {formatear_monto(cliente.get_saldo_total())}"
            )

    def opcion_abrir_cuenta(self):
        dni = self.leer_texto("DNI del titular: ")
        tipo = self.leer_texto("Tipo de cuenta (ahorro/corriente): ")
        saldo = self.leer_monto("Depósito inicial (0 para ninguno): ")
        cuenta = self.__banco.abrir_cuenta(dni, tipo, saldo)
        self.mostrar(f"Cuenta abierta: {cuenta}")

    def opcion_listar_cuentas(self):
        cuentas = self.__banco.get_cuentas()
        if not cuentas:
            self.mostrar("No hay cuentas abiertas.")
            return
        for cuenta in cuentas:
            self.mostrar(
                f"- {cuenta.get_numero()} | {cuenta.get_tipo()} | "
                f"{cuenta.get_titular().get_nombre()} | {formatear_monto(cuenta.get_saldo())}"
            )
            self.mostrar(f"    {cuenta.get_condiciones()}")

    def opcion_depositar(self):
        numero = self.leer_texto("Número de cuenta: ")
        monto = self.leer_monto("Monto a depositar: ")
        self.__banco.depositar(numero, monto)
        self.mostrar(f"Depósito realizado. Saldo: {formatear_monto(self.__banco.buscar_cuenta(numero).get_saldo())}")

    def opcion_extraer(self):
        numero = self.leer_texto("Número de cuenta: ")
        monto = self.leer_monto("Monto a extraer: ")
        self.__banco.extraer(numero, monto)
        self.mostrar(f"Extracción realizada. Saldo: {formatear_monto(self.__banco.buscar_cuenta(numero).get_saldo())}")

    def opcion_transferir(self):
        origen = self.leer_texto("Cuenta de origen: ")
        destino = self.leer_texto("Cuenta de destino: ")
        monto = self.leer_monto("Monto a transferir: ")
        self.__banco.transferir(origen, destino, monto)
        self.mostrar("Transferencia realizada.")

    def opcion_ver_movimientos(self):
        numero = self.leer_texto("Número de cuenta: ")
        cuenta = self.__banco.buscar_cuenta(numero)
        movimientos = cuenta.get_movimientos()
        if not movimientos:
            self.mostrar("La cuenta todavía no tiene movimientos.")
            return
        for mov in movimientos:
            efecto = mov.efecto_sobre(cuenta)
            self.mostrar(
                f"- #{mov.get_id():<3} {mov.a_fila()[1]} | {mov.get_tipo():<13} | {formatear_monto(efecto):>16}"
            )
        self.mostrar(f"Saldo actual: {formatear_monto(cuenta.get_saldo())}")

    def opcion_cierre_mensual(self):
        generadas = self.__banco.cierre_mensual()
        if not generadas:
            self.mostrar("No se generaron intereses ni comisiones.")
            return
        for transaccion in generadas:
            self.mostrar(f"- {transaccion.descripcion()}: {formatear_monto(transaccion.get_monto())}")

    def opcion_generar_pdf(self):
        nombre = self.leer_texto("Nombre del archivo (Enter para uno automático): ")
        if not nombre:
            nombre = f"reporte_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        if not nombre.lower().endswith(".pdf"):
            nombre += ".pdf"
        ruta = generar_pdf(self.__banco, os.path.join(self.__carpeta_reportes, nombre))
        self.mostrar(f"PDF guardado en: {ruta}")

    def opcion_cargar_demo(self):
        resumen = cargar_datos_demo(self.__banco)
        self.mostrar(f"Datos de ejemplo cargados: {resumen['clientes']} clientes, {resumen['cuentas']} cuentas.")

    def opcion_salir(self):
        self.mostrar("¡Hasta luego!")

    def _opciones(self):
        return {
            "1": ("Registrar cliente", self.opcion_registrar_cliente),
            "2": ("Listar clientes", self.opcion_listar_clientes),
            "3": ("Abrir cuenta", self.opcion_abrir_cuenta),
            "4": ("Listar cuentas", self.opcion_listar_cuentas),
            "5": ("Depositar", self.opcion_depositar),
            "6": ("Extraer", self.opcion_extraer),
            "7": ("Transferir", self.opcion_transferir),
            "8": ("Ver movimientos de una cuenta", self.opcion_ver_movimientos),
            "9": ("Cierre mensual (intereses y comisiones)", self.opcion_cierre_mensual),
            "10": ("Guardar reporte en PDF", self.opcion_generar_pdf),
            "11": ("Cargar datos de ejemplo", self.opcion_cargar_demo),
            "0": ("Salir", self.opcion_salir),
        }

    def ejecutar_opcion(self, opcion):
        """Ejecuta la opción elegida. Devuelve ``False`` si hay que salir del menú."""
        opciones = self._opciones()
        if opcion not in opciones:
            self.mostrar("Opción inválida. Elegí un número del menú.")
            return True
        try:
            opciones[opcion][1]()
        except BancoError as error:
            self.mostrar(f"[ERROR] {error}")
        return opcion != "0"

    def iniciar(self):
        """Bucle principal del menú."""
        continuar = True
        while continuar:
            try:
                self.mostrar_opciones()
                continuar = self.ejecutar_opcion(self.leer_texto("Elegí una opción: "))
            except (KeyboardInterrupt, EOFError):
                self.mostrar("\nSe interrumpió el programa. ¡Hasta luego!")
                continuar = False
