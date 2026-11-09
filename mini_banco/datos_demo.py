"""Carga de datos de ejemplo para probar el sistema rápidamente."""


def cargar_datos_demo(banco):
    """Agrega clientes, cuentas y movimientos de ejemplo. Devuelve el resumen del banco."""
    banco.registrar_cliente("Ana Gómez", "30123456")
    banco.registrar_cliente("Luis Fernández", "28456789")
    banco.registrar_cliente("María López", "35111222")

    ahorro_ana = banco.abrir_cuenta("30123456", "ahorro", 50000)
    corriente_ana = banco.abrir_cuenta("30123456", "corriente", 20000)
    ahorro_luis = banco.abrir_cuenta("28456789", "ahorro", 15000)
    corriente_maria = banco.abrir_cuenta("35111222", "corriente", 8000)

    banco.depositar(ahorro_luis.get_numero(), 5000)
    banco.extraer(ahorro_ana.get_numero(), 3500)
    banco.transferir(corriente_ana.get_numero(), corriente_maria.get_numero(), 4000)
    return banco.resumen()
