import json
import os
import time
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Literal

MAX_RETRIES = 3
BASE_RETRY_DELAY_SECONDS = 3  # exponential backoff: 3s, 6s, 12s


class CollateralEstimate(BaseModel):
    category: Literal["watch", "jewelry", "electronics", "other"]
    estimated_value: float
    condition: Literal["new", "good", "fair", "poor"]
    reasoning: str


def analyze_collateral_photo(image_path: str) -> CollateralEstimate:
    """Аналізує фото застави через Gemini Vision і повертає структуровану оцінку.

    Робить до MAX_RETRIES спроб з exponential backoff при тимчасовій
    недоступності моделі (503) - той самий підхід, що вже показав себе
    надійним у GitHub Critic Agent.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY не знайдено в .env")

    client = genai.Client(api_key=api_key)

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=[
                    image_part,
                    "Проаналізуй цей предмет для оцінки застави в ломбарді. "
                    "Визнач категорію, орієнтовну ринкову вартість у гривнях, "
                    "та стан предмета.",
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": CollateralEstimate,
                },
            )
            data = json.loads(response.text)
            return CollateralEstimate.model_validate(data)

        except Exception as e:
            last_error = e
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                delay = BASE_RETRY_DELAY_SECONDS * (2 ** attempt)
                print(f"Спроба {attempt + 1} невдала (503), чекаю {delay} сек...")
                time.sleep(delay)
                continue
            else:
                # Інші помилки (не 503) - немає сенсу повторювати
                raise

    raise RuntimeError(f"Не вдалось отримати оцінку після {MAX_RETRIES + 1} спроб: {last_error}")