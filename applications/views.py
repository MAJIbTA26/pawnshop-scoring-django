from rest_framework import generics
from .models import Application, Collateral
from .serializers import ApplicationSerializer, CollateralSerializer
from .ai_vision import analyze_collateral_photo


class CollateralListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/collaterals/  - список усіх застав
    POST /api/collaterals/  - завантажити нову заставу (фото)
    """
    queryset = Collateral.objects.all()
    serializer_class = CollateralSerializer

    def perform_create(self, serializer):
        collateral = serializer.save()

        try:
            estimate = analyze_collateral_photo(collateral.photo.path)
            collateral.category = estimate.category
            collateral.estimated_value = estimate.estimated_value
            collateral.condition = estimate.condition
            collateral.ai_analysis_raw = estimate.reasoning
            collateral.save()

        except Exception as e:
            collateral.ai_analysis_raw = f"Помилка AI-аналізу: {e}"
            collateral.save()


class ApplicationListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/applications/  - список усіх заявок
    POST /api/applications/  - створити нову заявку
    """
    queryset = Application.objects.all().order_by("-created_at")
    serializer_class = ApplicationSerializer

    def perform_create(self, serializer):
        application = serializer.save()
        application.calculate_scoring()


class ApplicationDetailView(generics.RetrieveAPIView):
    """
    GET /api/applications/<id>/  - деталі однієї заявки
    """
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer