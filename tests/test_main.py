"""Pruebas del punto de entrada."""

import main


def test_main_crea_el_banco_y_abre_el_menu(monkeypatch):
    llamadas = {}

    class MenuFalso:
        def __init__(self, banco):
            llamadas["banco"] = banco

        def iniciar(self):
            llamadas["iniciado"] = True

    monkeypatch.setattr(main, "Menu", MenuFalso)
    main.main()
    assert llamadas["banco"].get_nombre() == "Mini Banco"
    assert llamadas["iniciado"] is True