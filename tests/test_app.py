import pytest
from main import generate_valid_cpf, create_invoice
from datetime import datetime, timedelta, timezone


def test_generate_valid_cpf_length():
    cpf = generate_valid_cpf()
    assert len(cpf) == 11


def test_create_invoice():
    # Teste a criação de uma invoice com dados simulados.
    invoice = create_invoice(
        amount=5000,
        name="Teste",
        tax_id="12345678901",
        due=datetime(2021, 5, 12, 15, 23, 26, 689377)
    )
    assert invoice.amount == 5000
    assert invoice.name == "Teste"
