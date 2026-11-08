"""Generación del reporte PDF con la información del sistema (usa reportlab)."""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from mini_banco.excepciones import ReporteError

COLOR_PRINCIPAL = colors.HexColor("#0B5D4B")
COLOR_FILA = colors.HexColor("#EEF5F2")


def formatear_monto(monto):
    """Formatea un número como moneda: 1234.5 -> '$ 1.234,50'."""
    texto = f"{abs(monto):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    signo = "-" if monto < 0 else ""
    return f"{signo}$ {texto}"


def formatear_fecha(fecha):
    """Formatea un datetime como 'dd/mm/aaaa hh:mm'."""
    return fecha.strftime("%d/%m/%Y %H:%M")


def construir_estilos():
    """Devuelve los estilos de párrafo usados en el reporte."""
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("Titulo", parent=base["Title"], textColor=COLOR_PRINCIPAL, fontSize=22),
        "subtitulo": ParagraphStyle("Subtitulo", parent=base["Heading2"], textColor=COLOR_PRINCIPAL, spaceBefore=14),
        "texto": ParagraphStyle("Texto", parent=base["BodyText"], fontSize=10, leading=14),
        "celda": ParagraphStyle("Celda", parent=base["BodyText"], fontSize=8.5, leading=10.5),
    }


def crear_tabla(filas, encabezados, anchos=None):
    """Arma una tabla con encabezado de color y filas alternadas."""
    estilos = construir_estilos()
    datos = [encabezados] + [
        [Paragraph(str(valor), estilos["celda"]) for valor in fila] for fila in filas
    ]
    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRINCIPAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_FILA]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C9C3")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tabla


def armar_contenido(banco):
    """Construye la lista de elementos (flowables) que forman el PDF."""
    estilos = construir_estilos()
    resumen = banco.resumen()
    contenido = [
        Paragraph(f"{banco.get_nombre()} - Reporte del sistema", estilos["titulo"]),
        Paragraph(f"Generado el {formatear_fecha(datetime.now())}", estilos["texto"]),
        Spacer(1, 0.4 * cm),
        Paragraph("Acerca del sistema", estilos["subtitulo"]),
        Paragraph(
            "Sistema de gestión bancaria desarrollado con Programación Orientada a Objetos. "
            "Modela clientes, cuentas (caja de ahorro y cuenta corriente) y transacciones "
            "(depósitos, extracciones, transferencias, intereses y comisiones). "
            "Los datos se almacenan en listas en memoria mientras el programa está en ejecución.",
            estilos["texto"],
        ),
        Paragraph("Resumen general", estilos["subtitulo"]),
        crear_tabla(
            [
                ["Clientes registrados", resumen["clientes"]],
                ["Cuentas abiertas", resumen["cuentas"]],
                ["Transacciones realizadas", resumen["transacciones"]],
                ["Saldo total del banco", formatear_monto(resumen["saldo_total"])],
            ],
            ["Concepto", "Valor"],
            [9 * cm, 6 * cm],
        ),
        Paragraph("Clientes", estilos["subtitulo"]),
    ]
    filas_clientes = [
        [c.get_dni(), c.get_nombre(), len(c.get_cuentas()), formatear_monto(c.get_saldo_total())]
        for c in banco.get_clientes()
    ]
    contenido.append(crear_tabla(
        filas_clientes or [["-", "Sin clientes registrados", "-", "-"]],
        ["DNI", "Nombre", "Cuentas", "Saldo total"],
        [3 * cm, 7 * cm, 2.5 * cm, 4 * cm],
    ))
    contenido.append(Paragraph("Cuentas", estilos["subtitulo"]))
    filas_cuentas = [
        [c.get_numero(), c.get_tipo(), c.get_titular().get_nombre(),
         formatear_monto(c.get_saldo()), c.get_condiciones()]
        for c in banco.get_cuentas()
    ]
    contenido.append(crear_tabla(
        filas_cuentas or [["-", "-", "Sin cuentas abiertas", "-", "-"]],
        ["Número", "Tipo", "Titular", "Saldo", "Condiciones"],
        [2.2 * cm, 3 * cm, 3.4 * cm, 2.8 * cm, 6 * cm],
    ))
    contenido.append(Paragraph("Transacciones", estilos["subtitulo"]))
    filas_trans = [
        [f[0], f[1], f[2], f[3], formatear_monto(f[4])]
        for f in (t.a_fila() for t in banco.get_transacciones())
    ]
    contenido.append(crear_tabla(
        filas_trans or [["-", "-", "-", "Sin transacciones", "-"]],
        ["N.º", "Fecha", "Tipo", "Descripción", "Monto"],
        [1.2 * cm, 3 * cm, 2.6 * cm, 7.4 * cm, 3.2 * cm],
    ))
    return contenido


def dibujar_pie(lienzo, documento):
    """Escribe el número de página al pie de cada hoja."""
    lienzo.saveState()
    lienzo.setFont("Helvetica", 8)
    lienzo.setFillColor(colors.grey)
    lienzo.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {documento.page}")
    lienzo.drawString(2 * cm, 1.2 * cm, "Mini Banco - Reporte del sistema")
    lienzo.restoreState()


def generar_pdf(banco, ruta="reportes/reporte_banco.pdf"):
    """Genera el reporte PDF en ``ruta`` y devuelve la ruta final.

    Lanza ``ReporteError`` si no se puede escribir el archivo.
    """
    try:
        carpeta = os.path.dirname(ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        documento = SimpleDocTemplate(
            ruta, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
            title=f"{banco.get_nombre()} - Reporte", author="Mini Banco",
        )
        documento.build(armar_contenido(banco), onFirstPage=dibujar_pie, onLaterPages=dibujar_pie)
    except OSError as error:
        raise ReporteError(f"No se pudo guardar el PDF en '{ruta}': {error}") from error
    return ruta
