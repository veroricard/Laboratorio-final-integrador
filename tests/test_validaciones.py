import pytest

from mini_banco import validaciones as v
from mini_banco.excepciones import DatoInvalidoError, MontoInvalidoError


class TestValidarNumero:
    @pytest.mark.parametrize("valor, esperado", [(5, 5.0), (3.14159, 3.14), (0, 0.0), (-2.5, -2.5)])
    def test_acepta_numeros(self, valor, esperado):
        assert v.validar_numero(valor) == esperado

    @pytest.mark.parametrize("valor", ["10", None, True, [1], float("nan"), float("inf")])
    def test_rechaza_no_numeros(self, valor):
        with pytest.raises(MontoInvalidoError):
            v.validar_numero(valor)


class TestValidarMonto:
    def test_acepta_positivo(self):
        assert v.validar_monto(10.556) == 10.56

    @pytest.mark.parametrize("valor", [0, -1, -0.01])
    def test_rechaza_cero_y_negativos(self, valor):
        with pytest.raises(MontoInvalidoError):
            v.validar_monto(valor)

    def test_rechaza_texto(self):
        with pytest.raises(MontoInvalidoError):
            v.validar_monto("abc")


class TestValidarNoNegativo:
    @pytest.mark.parametrize("valor", [0, 1, 99.99])
    def test_acepta_cero_y_positivos(self, valor):
        assert v.validar_no_negativo(valor) == valor

    def test_rechaza_negativo(self):
        with pytest.raises(MontoInvalidoError):
            v.validar_no_negativo(-0.5)


class TestValidarTexto:
    def test_recorta_espacios(self):
        assert v.validar_texto("  hola  ") == "hola"

    @pytest.mark.parametrize("valor", ["", "   ", None, 5])
    def test_rechaza_vacios_o_no_texto(self, valor):
        with pytest.raises(DatoInvalidoError):
            v.validar_texto(valor)

    def test_el_mensaje_nombra_el_campo(self):
        with pytest.raises(DatoInvalidoError, match="El apodo"):
            v.validar_texto("", "El apodo")


class TestValidarDni:
    @pytest.mark.parametrize("entrada, esperado", [
        ("30123456", "30123456"), ("1234567", "1234567"), ("30.123.456", "30123456"),
        (" 30123456 ", "30123456"), (30123456, "30123456"),
    ])
    def test_acepta_dni_validos(self, entrada, esperado):
        assert v.validar_dni(entrada) == esperado

    @pytest.mark.parametrize("entrada", ["123", "123456789", "abcdefgh", "", None, 3.5, True, 12])
    def test_rechaza_dni_invalidos(self, entrada):
        with pytest.raises(DatoInvalidoError):
            v.validar_dni(entrada)
