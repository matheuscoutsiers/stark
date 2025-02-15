import pytest
from main import generate_valid_cpf, create_invoice


def test_generate_valid_cpf_length():
    cpf = generate_valid_cpf()
    assert len(cpf) == 11


def test_create_invoice():
    # Teste a criação de uma invoice com dados simulados.
    invoice = create_invoice(
        amount=5000,
        name="Teste",
        tax_id="12345678901",
        due="2025-12-31T23:59:59Z"
    )
    assert invoice.amount == 5000
    assert invoice.name == "Teste"
