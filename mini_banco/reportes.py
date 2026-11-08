"""Generación del reporte PDF con la información del sistema (usa fpdf2)."""

import os
from datetime import datetime

from fpdf import FPDF
from fpdf.fonts import FontFace

from mini_banco.excepciones import ReporteError

COLOR_PRINCIPAL = (11, 93, 75)
COLOR_FILA = (238, 245, 242)
COLOR_BLANCO = (255, 255, 255)
COLOR_GRIS = (128, 128, 128)


def formatear_monto(monto):
    """Formatea un número como moneda: 1234.5 -> '$ 1.234,50'."""
    texto = f"{abs(monto):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    signo = "-" if monto < 0 else ""
    return f"{signo}$ {texto}"


def formatear_fecha(fecha):
    """Formatea un datetime como 'dd/mm/aaaa hh:mm'."""
    return fecha.strftime("%d/%m/%Y %H:%M")


def limpiar_texto(valor):
    """Convierte ``valor`` a texto compatible con la fuente Helvetica (latin-1)."""
    return str(valor).encode("latin-1", "replace").decode("latin-1")


class ReportePDF(FPDF):
    """PDF con pie de página que muestra el nombre del sistema y el número de hoja."""

    def __init__(self, titulo_pie="Mini Banco - Reporte del sistema"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.titulo_pie = limpiar_texto(titulo_pie)
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*COLOR_GRIS)
        self.cell(0, 8, self.titulo_pie, align="L")
        self.set_x(self.l_margin)
        self.cell(0, 8, f"Página {self.page_no()}", align="R")
        self.set_text_color(0, 0, 0)


def agregar_titulo(pdf, texto):
    """Escribe el título principal del reporte."""
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*COLOR_PRINCIPAL)
    pdf.multi_cell(0, 10, limpiar_texto(texto), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_text_color(0, 0, 0)


def agregar_subtitulo(pdf, texto):
    """Escribe un título de sección."""
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*COLOR_PRINCIPAL)
    pdf.cell(0, 8, limpiar_texto(texto), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)


def agregar_parrafo(pdf, texto):
    """Escribe un párrafo de texto normal."""
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5.5, limpiar_texto(texto), new_x="LMARGIN", new_y="NEXT")


def agregar_tabla(pdf, encabezados, filas, anchos):
    """Dibuja una tabla con encabezado de color y filas alternadas."""
    pdf.set_font("Helvetica", "", 8.5)
    estilo_encabezado = FontFace(emphasis="BOLD", color=COLOR_BLANCO, fill_color=COLOR_PRINCIPAL)
    with pdf.table(
        col_widths=anchos,
        headings_style=estilo_encabezado,
        cell_fill_color=COLOR_FILA,
        cell_fill_mode="ROWS",
        line_height=5.5,
        text_align="LEFT",
        padding=1.5,
        borders_layout="ALL",
    ) as tabla:
        encabezado = tabla.row()
        for texto in encabezados:
            encabezado.cell(limpiar_texto(texto))
        for fila in filas:
            registro = tabla.row()
            for valor in fila:
                registro.cell(limpiar_texto(valor))


def armar_contenido(pdf, banco):
    """Escribe en ``pdf`` todas las secciones del reporte."""
    resumen = banco.resumen()
    agregar_titulo(pdf, f"{banco.get_nombre()} - Reporte del sistema")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generado el {formatear_fecha(datetime.now())}",
             new_x="LMARGIN", new_y="NEXT", align="C")

    agregar_subtitulo(pdf, "Acerca del sistema")
    agregar_parrafo(
        pdf,
        "Sistema de gestión bancaria desarrollado con Programación Orientada a Objetos. "
        "Modela clientes, cuentas (caja de ahorro y cuenta corriente) y transacciones "
        "(depósitos, extracciones, transferencias, intereses y comisiones). "
        "Los datos se almacenan en listas en memoria mientras el programa está en ejecución.",
    )

    agregar_subtitulo(pdf, "Resumen general")
    agregar_tabla(
        pdf,
        ["Concepto", "Valor"],
        [
            ["Clientes registrados", resumen["clientes"]],
            ["Cuentas abiertas", resumen["cuentas"]],
            ["Transacciones realizadas", resumen["transacciones"]],
            ["Saldo total del banco", formatear_monto(resumen["saldo_total"])],
        ],
        (100, 70),
    )

    agregar_subtitulo(pdf, "Clientes")
    filas_clientes = [
        [c.get_dni(), c.get_nombre(), len(c.get_cuentas()), formatear_monto(c.get_saldo_total())]
        for c in banco.get_clientes()
    ]
    agregar_tabla(
        pdf,
        ["DNI", "Nombre", "Cuentas", "Saldo total"],
        filas_clientes or [["-", "Sin clientes registrados", "-", "-"]],
        (30, 70, 25, 45),
    )

    agregar_subtitulo(pdf, "Cuentas")
    filas_cuentas = [
        [c.get_numero(), c.get_tipo(), c.get_titular().get_nombre(),
         formatear_monto(c.get_saldo()), c.get_condiciones()]
        for c in banco.get_cuentas()
    ]
    agregar_tabla(
        pdf,
        ["Número", "Tipo", "Titular", "Saldo", "Condiciones"],
        filas_cuentas or [["-", "-", "Sin cuentas abiertas", "-", "-"]],
        (20, 28, 30, 30, 62),
    )

    agregar_subtitulo(pdf, "Transacciones")
    filas_trans = [
        [f[0], f[1], f[2], f[3], formatear_monto(f[4])]
        for f in (t.a_fila() for t in banco.get_transacciones())
    ]
    agregar_tabla(
        pdf,
        ["N.º", "Fecha", "Tipo", "Descripción", "Monto"],
        filas_trans or [["-", "-", "-", "Sin transacciones", "-"]],
        (10, 30, 24, 70, 36),
    )


def generar_pdf(banco, ruta="reportes/reporte_banco.pdf"):
    """Genera el reporte PDF en ``ruta`` y devuelve la ruta final.

    Lanza ``ReporteError`` si no se puede escribir el archivo.
    """
    try:
        carpeta = os.path.dirname(ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        pdf = ReportePDF()
        pdf.set_title(limpiar_texto(f"{banco.get_nombre()} - Reporte"))
        pdf.set_author("Mini Banco")
        pdf.add_page()
        armar_contenido(pdf, banco)
        pdf.output(ruta)
    except OSError as error:
        raise ReporteError(f"No se pudo guardar el PDF en '{ruta}': {error}") from error
    return ruta