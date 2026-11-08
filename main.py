"""Punto de entrada del Mini Banco."""

from mini_banco.banco import Banco
from mini_banco.menu import Menu


def main():
    """Crea el banco y abre el menú interactivo."""
    Menu(Banco("Mini Banco")).iniciar()


if __name__ == "__main__":  # pragma: no cover
    main()
