"""Pruebas de los formatos y de la generación del PDF (fpdf2)."""

from datetime import datetime

import pytest
from fpdf import FPDF

from mini_banco.banco import Banco
from mini_banco.datos_demo import cargar_datos_demo
from mini_banco.excepciones import ReporteError
from mini_banco.reportes import (
    ReportePDF,
    agregar_parrafo,
    agregar_subtitulo,
    agregar_tabla,
    agregar_titulo,
    armar_contenido,
    formatear_fecha,
    formatear_monto,
    generar_pdf,
    limpiar_texto,
)
from mini_banco.transaccion import Transaccion


@pytest.fixture(autouse=True)
def reiniciar_ids():
    Transaccion.reiniciar_contador()


@pytest.fixture
def banco_demo():
    banco = Banco("Banco Demo")
    cargar_datos_demo(banco)
    return banco


class TestFormatearMonto:
    @pytest.mark.parametrize(
        "monto, esperado",
        [
            (0, "$ 0,00"),
            (5, "$ 5,00"),
            (1234.5, "$ 1.234,50"),
            (1000000, "$ 1.000.000,00"),
            (-1234.5, "-$ 1.234,50"),
            (0.99, "$ 0,99"),
        ],
    )
    def test_formatos(self, monto, esperado):
        assert formatear_monto(monto) == esperado


def test_formatear_fecha():
    assert formatear_fecha(datetime(2026, 3, 9, 14, 5)) == "09/03/2026 14:05"


class TestLimpiarTexto:
    def test_respeta_acentos_y_enie(self):
        assert limpiar_texto("Peña Gómez") == "Peña Gómez"

    def test_convierte_numeros_a_texto(self):
        assert limpiar_texto(42) == "42"

    def test_reemplaza_caracteres_no_soportados(self):
        resultado = limpiar_texto("Hola 😀")
        assert resultado.startswith("Hola ")
        assert "😀" not in resultado


class TestComponentes:
    @pytest.fixture
    def pdf(self):
        documento = ReportePDF()
        documento.add_page()
        return documento

    def test_reporte_pdf_es_un_fpdf(self, pdf):
        assert isinstance(pdf, FPDF)

    def test_pie_de_pagina_personalizado(self):
        assert ReportePDF("Otro pie").titulo_pie == "Otro pie"

    def test_titulo_subtitulo_y_parrafo_avanzan_el_cursor(self, pdf):
        y0 = pdf.get_y()
        agregar_titulo(pdf, "Título")
        y1 = pdf.get_y()
        agregar_subtitulo(pdf, "Subtítulo")
        y2 = pdf.get_y()
        agregar_parrafo(pdf, "Texto " * 50)
        y3 = pdf.get_y()
        assert y0 < y1 < y2 < y3

    def test_tabla_avanza_el_cursor(self, pdf):
        y0 = pdf.get_y()
        agregar_tabla(pdf, ["A", "B"], [["1", "2"], ["3", "4"]], (50, 50))
        assert pdf.get_y() > y0


class TestGenerarPdf:
    def test_crea_un_pdf_valido(self, banco_demo, tmp_path):
        ruta = tmp_path / "reporte.pdf"
        resultado = generar_pdf(banco_demo, str(ruta))
        assert resultado == str(ruta)
        assert ruta.exists()
        assert ruta.read_bytes().startswith(b"%PDF")

    def test_crea_la_carpeta_si_no_existe(self, banco_demo, tmp_path):
        ruta = tmp_path / "reportes" / "nuevo" / "r.pdf"
        generar_pdf(banco_demo, str(ruta))
        assert ruta.exists()

    def test_funciona_con_el_banco_vacio(self, tmp_path):
        ruta = tmp_path / "vacio.pdf"
        generar_pdf(Banco(), str(ruta))
        assert ruta.read_bytes().startswith(b"%PDF")

    def test_funciona_con_ruta_sin_carpeta(self, banco_demo, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert generar_pdf(banco_demo, "solo_nombre.pdf") == "solo_nombre.pdf"
        assert (tmp_path / "solo_nombre.pdf").exists()

    def test_ruta_por_defecto(self, banco_demo, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ruta = generar_pdf(banco_demo)
        assert ruta == "reportes/reporte_banco.pdf"
        assert (tmp_path / "reportes" / "reporte_banco.pdf").exists()

    def test_acepta_caracteres_raros_en_los_nombres(self, tmp_path):
        banco = Banco("Banco Ñandú")
        banco.registrar_cliente("Zoë 😀 Núñez", "12345678")
        ruta = tmp_path / "raro.pdf"
        generar_pdf(banco, str(ruta))
        assert ruta.exists()

    def test_varias_paginas_con_muchas_transacciones(self, tmp_path):
        banco = Banco()
        banco.registrar_cliente("Ana", "30123456")
        banco.abrir_cuenta("30123456", "corriente", 1000)
        for _ in range(80):
            banco.depositar("CC-0001", 10)
        ruta = tmp_path / "largo.pdf"
        generar_pdf(banco, str(ruta))
        assert ruta.read_bytes().count(b"/Type /Page\n") >= 2

    def test_error_si_no_se_puede_guardar(self, banco_demo, tmp_path):
        archivo = tmp_path / "archivo.txt"
        archivo.write_text("hola")
        with pytest.raises(ReporteError):
            generar_pdf(banco_demo, str(archivo / "reporte.pdf"))

    def test_error_si_la_ruta_es_una_carpeta(self, banco_demo, tmp_path):
        with pytest.raises(ReporteError):
            generar_pdf(banco_demo, str(tmp_path))


def test_armar_contenido_escribe_en_el_pdf(banco_demo):
    pdf = ReportePDF()
    pdf.add_page()
    armar_contenido(pdf, banco_demo)
    assert pdf.page_no() >= 1