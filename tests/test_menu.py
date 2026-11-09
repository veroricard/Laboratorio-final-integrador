"""Pruebas del menú interactivo (se simula el teclado y la pantalla)."""

import pytest

from mini_banco.banco import Banco
from mini_banco.excepciones import MontoInvalidoError
from mini_banco.menu import Menu
from mini_banco.transaccion import Transaccion


@pytest.fixture(autouse=True)
def reiniciar_ids():
    Transaccion.reiniciar_contador()


class Teclado:
    """Entrada falsa: va entregando las respuestas en orden."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.preguntas = []

    def __call__(self, mensaje):
        self.preguntas.append(mensaje)
        if not self.respuestas:
            raise EOFError
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, BaseException):
            raise respuesta
        return respuesta


def crear_menu(*respuestas, banco=None, carpeta="reportes"):
    pantalla = []
    teclado = Teclado(*respuestas)
    menu = Menu(banco or Banco("Banco Test"), entrada=teclado, salida=pantalla.append,
                carpeta_reportes=carpeta)
    return menu, pantalla


def texto(pantalla):
    return "\n".join(pantalla)


@pytest.fixture
def banco():
    b = Banco("Banco Test")
    b.registrar_cliente("Ana Gómez", "30123456")
    b.abrir_cuenta("30123456", "ahorro", 1000)
    b.abrir_cuenta("30123456", "corriente", 500)
    return b


class TestAccesores:
    def test_banco(self, banco):
        menu, _ = crear_menu(banco=banco)
        assert menu.get_banco() is banco
        otro = Banco("Otro")
        menu.set_banco(otro)
        assert menu.get_banco() is otro

    def test_carpeta_reportes(self):
        menu, _ = crear_menu()
        assert menu.get_carpeta_reportes() == "reportes"
        menu.set_carpeta_reportes("salida")
        assert menu.get_carpeta_reportes() == "salida"

    def test_entrada_y_salida_por_defecto(self, monkeypatch, capsys):
        monkeypatch.setattr("builtins.input", lambda mensaje: "  hola  ")
        menu = Menu(Banco())
        assert menu.leer_texto("? ") == "hola"
        menu.mostrar("mensaje en pantalla")
        assert "mensaje en pantalla" in capsys.readouterr().out


class TestLectura:
    def test_leer_texto_quita_espacios(self):
        menu, _ = crear_menu("  hola  ")
        assert menu.leer_texto("? ") == "hola"

    @pytest.mark.parametrize("escrito, esperado", [("100", 100.0), ("12,5", 12.5), ("7.25", 7.25)])
    def test_leer_monto(self, escrito, esperado):
        menu, _ = crear_menu(escrito)
        assert menu.leer_monto("? ") == esperado

    @pytest.mark.parametrize("escrito", ["abc", "", "1,2,3"])
    def test_leer_monto_invalido(self, escrito):
        menu, _ = crear_menu(escrito)
        with pytest.raises(MontoInvalidoError):
            menu.leer_monto("? ")


class TestPantalla:
    def test_mostrar_opciones(self):
        menu, pantalla = crear_menu()
        menu.mostrar_opciones()
        salida = texto(pantalla)
        assert "BANCO TEST" in salida
        assert "Registrar cliente" in salida
        assert "Guardar reporte en PDF" in salida
        assert "Salir" in salida


class TestOpciones:
    def test_registrar_cliente(self):
        menu, pantalla = crear_menu("Ana Gómez", "30123456")
        menu.opcion_registrar_cliente()
        assert "Cliente registrado: Ana Gómez (DNI 30123456)" in texto(pantalla)
        assert len(menu.get_banco().get_clientes()) == 1

    def test_listar_clientes_vacio(self):
        menu, pantalla = crear_menu()
        menu.opcion_listar_clientes()
        assert "No hay clientes registrados." in texto(pantalla)

    def test_listar_clientes(self, banco):
        menu, pantalla = crear_menu(banco=banco)
        menu.opcion_listar_clientes()
        salida = texto(pantalla)
        assert "Ana Gómez" in salida
        assert "cuentas: 2" in salida
        assert "$ 1.500,00" in salida

    def test_abrir_cuenta(self):
        banco = Banco()
        banco.registrar_cliente("Ana", "30123456")
        menu, pantalla = crear_menu("30123456", "ahorro", "2500", banco=banco)
        menu.opcion_abrir_cuenta()
        assert "Cuenta abierta: Caja de Ahorro AH-0001 - saldo 2500.00" in texto(pantalla)

    def test_listar_cuentas_vacio(self):
        menu, pantalla = crear_menu()
        menu.opcion_listar_cuentas()
        assert "No hay cuentas abiertas." in texto(pantalla)

    def test_listar_cuentas(self, banco):
        menu, pantalla = crear_menu(banco=banco)
        menu.opcion_listar_cuentas()
        salida = texto(pantalla)
        assert "AH-0001" in salida and "CC-0002" in salida
        assert "Interés mensual" in salida
        assert "Descubierto" in salida

    def test_depositar(self, banco):
        menu, pantalla = crear_menu("AH-0001", "200", banco=banco)
        menu.opcion_depositar()
        assert "Depósito realizado. Saldo: $ 1.200,00" in texto(pantalla)

    def test_extraer(self, banco):
        menu, pantalla = crear_menu("AH-0001", "200", banco=banco)
        menu.opcion_extraer()
        assert "Extracción realizada. Saldo: $ 800,00" in texto(pantalla)

    def test_transferir(self, banco):
        menu, pantalla = crear_menu("AH-0001", "CC-0002", "300", banco=banco)
        menu.opcion_transferir()
        assert "Transferencia realizada." in texto(pantalla)
        assert banco.buscar_cuenta("CC-0002").get_saldo() == 800.0

    def test_ver_movimientos(self, banco):
        menu, pantalla = crear_menu("AH-0001", banco=banco)
        menu.opcion_ver_movimientos()
        salida = texto(pantalla)
        assert "Depósito" in salida
        assert "Saldo actual: $ 1.000,00" in salida

    def test_ver_movimientos_sin_movimientos(self):
        banco = Banco()
        banco.registrar_cliente("Ana", "30123456")
        banco.abrir_cuenta("30123456", "ahorro")
        menu, pantalla = crear_menu("AH-0001", banco=banco)
        menu.opcion_ver_movimientos()
        assert "todavía no tiene movimientos" in texto(pantalla)

    def test_cierre_mensual(self, banco):
        menu, pantalla = crear_menu(banco=banco)
        menu.opcion_cierre_mensual()
        salida = texto(pantalla)
        assert "Interés mensual en AH-0001" in salida
        assert "Comisión de mantenimiento de CC-0002" in salida

    def test_cierre_mensual_sin_nada_que_aplicar(self):
        menu, pantalla = crear_menu()
        menu.opcion_cierre_mensual()
        assert "No se generaron intereses ni comisiones." in texto(pantalla)

    def test_cargar_demo(self):
        menu, pantalla = crear_menu()
        menu.opcion_cargar_demo()
        assert "3 clientes, 4 cuentas" in texto(pantalla)

    def test_salir(self):
        menu, pantalla = crear_menu()
        menu.opcion_salir()
        assert "¡Hasta luego!" in texto(pantalla)


class TestPdf:
    def test_con_nombre(self, banco, tmp_path):
        menu, pantalla = crear_menu("mi_reporte", banco=banco, carpeta=str(tmp_path))
        menu.opcion_generar_pdf()
        assert (tmp_path / "mi_reporte.pdf").exists()
        assert "PDF guardado en:" in texto(pantalla)

    def test_con_extension_pdf_no_se_duplica(self, banco, tmp_path):
        menu, _ = crear_menu("REPORTE.PDF", banco=banco, carpeta=str(tmp_path))
        menu.opcion_generar_pdf()
        assert (tmp_path / "REPORTE.PDF").exists()

    def test_nombre_automatico(self, banco, tmp_path):
        menu, _ = crear_menu("", banco=banco, carpeta=str(tmp_path))
        menu.opcion_generar_pdf()
        archivos = list(tmp_path.glob("reporte_*.pdf"))
        assert len(archivos) == 1


class TestEjecutarOpcion:
    def test_opcion_invalida(self):
        menu, pantalla = crear_menu()
        assert menu.ejecutar_opcion("99") is True
        assert "Opción inválida" in texto(pantalla)

    def test_salir_devuelve_false(self):
        menu, _ = crear_menu()
        assert menu.ejecutar_opcion("0") is False

    def test_otras_opciones_devuelven_true(self):
        menu, _ = crear_menu()
        assert menu.ejecutar_opcion("2") is True

    def test_captura_errores_del_banco(self, banco):
        menu, pantalla = crear_menu("AH-0001", "999999", banco=banco)
        assert menu.ejecutar_opcion("6") is True
        assert "[ERROR] Saldo insuficiente en AH-0001" in texto(pantalla)

    def test_captura_monto_no_numerico(self, banco):
        menu, pantalla = crear_menu("AH-0001", "abc", banco=banco)
        menu.ejecutar_opcion("5")
        assert "[ERROR] 'abc' no es un monto válido." in texto(pantalla)

    def test_captura_cuenta_inexistente(self, banco):
        menu, pantalla = crear_menu("ZZ-9", "10", banco=banco)
        menu.ejecutar_opcion("5")
        assert "[ERROR] No existe la cuenta ZZ-9." in texto(pantalla)


class TestIniciar:
    def test_sale_con_cero(self):
        menu, pantalla = crear_menu("0")
        menu.iniciar()
        assert "¡Hasta luego!" in texto(pantalla)

    def test_sesion_completa(self):
        menu, pantalla = crear_menu("11", "4", "abc", "0")
        menu.iniciar()
        salida = texto(pantalla)
        assert "Datos de ejemplo cargados" in salida
        assert "AH-0001" in salida
        assert "Opción inválida" in salida

    def test_sigue_funcionando_despues_de_un_error(self):
        menu, pantalla = crear_menu("6", "XX-1", "10", "0")
        menu.iniciar()
        salida = texto(pantalla)
        assert "[ERROR]" in salida
        assert "¡Hasta luego!" in salida

    def test_ctrl_c(self):
        menu, pantalla = crear_menu(KeyboardInterrupt())
        menu.iniciar()
        assert "Se interrumpió el programa" in texto(pantalla)

    def test_fin_de_entrada(self):
        menu, pantalla = crear_menu()
        menu.iniciar()
        assert "Se interrumpió el programa" in texto(pantalla)