from traversalkit.ids import ANY_ID, DEC_ID, HEX_ID, TEXT_ID


def test_any_id():
    assert ANY_ID.match('')
    assert ANY_ID.match('Jane Doe.1984')


def test_text_id():
    assert TEXT_ID.match('Jane_Doe-1984')
    assert not TEXT_ID.match('Jane Doe.1984')


def test_dec_id():
    assert DEC_ID.match('42')
    assert not DEC_ID.match('2A')


def test_hex_id():
    assert HEX_ID.match('2Af')
    assert not HEX_ID.match('2h')
