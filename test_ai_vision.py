"""Тести для applications/ai_vision.py — аналізу фото застави через Gemini Vision."""
import os

import pytest

from applications.ai_vision import CollateralEstimate, analyze_collateral_photo


def test_analyze_collateral_photo_raises_on_missing_file() -> None:
    """Якщо шлях до фото не існує — має піднятися FileNotFoundError, а не впасти мовчки."""
    with pytest.raises(FileNotFoundError):
        analyze_collateral_photo("nonexistent_photo.jpg")


@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="Потрібен GEMINI_API_KEY у .env для реального виклику Gemini API",
)
def test_analyze_collateral_photo_returns_structured_estimate() -> None:
    """Реальний виклик Gemini Vision має повернути коректно заповнений CollateralEstimate."""
    photo_path = os.path.join("collateral_photos", os.listdir("collateral_photos")[0])

    result = analyze_collateral_photo(photo_path)

    assert isinstance(result, CollateralEstimate)
    assert result.category in ("watch", "jewelry", "electronics", "other")
    assert result.estimated_value > 0
    assert result.condition in ("new", "good", "fair", "poor")
    assert result.reasoning