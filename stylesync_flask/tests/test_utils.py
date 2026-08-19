from app.utils import format_currecy

def test_format_currency_with_decimal():
    input_value = 59.9
    result = format_currecy(input_value)

    # verifica se resultado é True
    assert result == '59,90'

def test_format_currency_with_integer():
    assert format_currecy(123) == '123,00'

def test_format_current_with_zero():
    assert format_currecy(0) == '0,00'
