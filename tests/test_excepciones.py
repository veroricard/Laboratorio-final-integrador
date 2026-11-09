import pytest

from mini_banco import excepciones as ex


@pytest.mark.parametrize("clase", [
    ex.DatoInvalidoError, ex.MontoInvalidoError, ex.SaldoInsuficienteError,
    ex.LimiteExtraccionesError, ex.ClienteNoEncontradoError, ex.CuentaNoEncontradaError,
    ex.DuplicadoError, ex.OperacionInvalidaError, ex.ReporteError,
])
def test_todas_heredan_de_banco_error(clase):
    assert issubclass(clase, ex.BancoError)
    with pytest.raises(ex.BancoError):
        raise clase("mensaje")


def test_banco_error_es_una_excepcion_comun():
    assert issubclass(ex.BancoError, Exception)
