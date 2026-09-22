from rest_framework import serializers
from .models import Client, Collateral, Application


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "full_name", "phone", "email", "created_at"]


class CollateralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collateral
        fields = ["id", "photo", "category", "estimated_value", "condition", "ai_analysis_raw"]
        read_only_fields = ["category", "estimated_value", "condition", "ai_analysis_raw"]


class ApplicationSerializer(serializers.ModelSerializer):
    client = ClientSerializer()
    collateral = CollateralSerializer(read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "client", "collateral", "client_income",
            "existing_debts", "status", "proposed_loan_amount", "created_at"
        ]
        read_only_fields = ["status", "proposed_loan_amount"]

    def create(self, validated_data):
        # Витягуємо дані клієнта окремо від решти полів заявки
        client_data = validated_data.pop("client")

        # Спочатку створюємо (або знаходимо існуючого) клієнта
        client, _ = Client.objects.get_or_create(
            phone=client_data["phone"],
            defaults=client_data,
        )

        # Тепер створюємо саму заявку, прив'язану до цього клієнта
        application = Application.objects.create(client=client, **validated_data)
        return application