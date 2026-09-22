from decimal import Decimal
from django.db import models


class Client(models.Model):
    """Клієнт ломбарду."""
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Collateral(models.Model):
    """Застава - річ, яку клієнт приносить у заставу."""

    CATEGORY_CHOICES = [
        ("watch", "Годинник"),
        ("jewelry", "Ювелірка"),
        ("electronics", "Електроніка"),
        ("other", "Інше"),
    ]

    CONDITION_CHOICES = [
        ("new", "Новий"),
        ("good", "Добрий"),
        ("fair", "Задовільний"),
        ("poor", "Поганий"),
    ]

    photo = models.ImageField(upload_to="collateral_photos/")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True)
    estimated_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, blank=True)
    ai_analysis_raw = models.TextField(blank=True)  # повна відповідь AI, для діагностики

    def __str__(self):
        return f"{self.get_category_display() or 'Не визначено'} (~{self.estimated_value or '?'} грн)"


class Application(models.Model):
    """Заявка на позику під заставу."""

    STATUS_CHOICES = [
        ("pending", "На розгляді"),
        ("approved", "Схвалено"),
        ("rejected", "Відхилено"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="applications")
    collateral = models.OneToOneField(Collateral, on_delete=models.CASCADE, null=True, blank=True)
    client_income = models.DecimalField(max_digits=10, decimal_places=2)
    existing_debts = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    proposed_loan_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_scoring(self):
        """Розраховує рішення по заявці на основі доходу, боргів та вартості застави.

        Логіка (проста, правило-базована, без ML):
        - Якщо застави немає, або її вартість не визначена AI - заявка
          не може бути оцінена, залишається "pending".
        - Якщо дохід клієнта більше ніж удвічі перевищує його борги,
          І вартість застави більша за 500 грн - схвалюємо, пропонуємо
          70% від вартості застави.
        - Інакше - відхиляємо.
        """
        if not self.collateral or self.collateral.estimated_value is None:
            self.status = "pending"
            self.proposed_loan_amount = None
            return

        income_to_debt_ok = self.client_income > (self.existing_debts * 2)
        collateral_value_ok = self.collateral.estimated_value > 500

        if income_to_debt_ok and collateral_value_ok:
            self.status = "approved"
            self.proposed_loan_amount = round(self.collateral.estimated_value * Decimal("0.7"), 2)
        else:
            self.status = "rejected"
            self.proposed_loan_amount = None

        self.save()

    def __str__(self):
        return f"Заявка #{self.id} - {self.client.full_name} - {self.status}"