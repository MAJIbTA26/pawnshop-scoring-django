import pytest
from decimal import Decimal
from applications.models import Client, Collateral, Application


@pytest.fixture
def client():
    return Client.objects.create(
        full_name="Тестовий Клієнт",
        phone="+380001112233",
    )


@pytest.mark.django_db
def test_approved_when_income_and_collateral_are_good(client):
    """Заявка схвалюється, якщо дохід удвічі більший за борги,
    і вартість застави перевищує 500 грн."""
    collateral = Collateral.objects.create(estimated_value=Decimal("3000"))
    application = Application.objects.create(
        client=client,
        collateral=collateral,
        client_income=Decimal("5000"),
        existing_debts=Decimal("500"),
    )

    application.calculate_scoring()

    assert application.status == "approved"
    assert application.proposed_loan_amount == Decimal("2100.00")  # 70% від 3000


@pytest.mark.django_db
def test_rejected_when_collateral_value_too_low(client):
    """Заявка відхиляється, якщо вартість застави менша за 500 грн,
    навіть при хорошому доході."""
    collateral = Collateral.objects.create(estimated_value=Decimal("250"))
    application = Application.objects.create(
        client=client,
        collateral=collateral,
        client_income=Decimal("5000"),
        existing_debts=Decimal("500"),
    )

    application.calculate_scoring()

    assert application.status == "rejected"
    assert application.proposed_loan_amount is None


@pytest.mark.django_db
def test_rejected_when_debts_too_high(client):
    """Заявка відхиляється, якщо дохід НЕ перевищує борги вдвічі,
    навіть при дорогій заставі."""
    collateral = Collateral.objects.create(estimated_value=Decimal("3000"))
    application = Application.objects.create(
        client=client,
        collateral=collateral,
        client_income=Decimal("1000"),
        existing_debts=Decimal("600"),  # дохід НЕ вдвічі більший за борги
    )

    application.calculate_scoring()

    assert application.status == "rejected"


@pytest.mark.django_db
def test_pending_when_no_collateral(client):
    """Заявка залишається 'pending', якщо застава ще не прив'язана."""
    application = Application.objects.create(
        client=client,
        client_income=Decimal("5000"),
        existing_debts=Decimal("500"),
    )

    application.calculate_scoring()

    assert application.status == "pending"


@pytest.mark.django_db
def test_pending_when_collateral_has_no_estimated_value(client):
    """Заявка залишається 'pending', якщо AI ще не оцінив заставу
    (estimated_value порожній)."""
    collateral = Collateral.objects.create()  # без estimated_value
    application = Application.objects.create(
        client=client,
        collateral=collateral,
        client_income=Decimal("5000"),
        existing_debts=Decimal("500"),
    )

    application.calculate_scoring()

    assert application.status == "pending"
