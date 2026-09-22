import os
from dotenv import load_dotenv

load_dotenv()

from applications.ai_vision import analyze_collateral_photo

# Встав СЮДИ шлях до будь-якого реального фото на твоєму комп'ютері
# (можеш використати те саме фото, яке завантажував через форму раніше)
TEST_IMAGE_PATH = r"C:\Users\VivoBook\Desktop\Нова папка\collateral_photos\photo_2026-09-22_19-41-15_ok8UE39.jpg"

if __name__ == "__main__":
    result = analyze_collateral_photo(TEST_IMAGE_PATH)
    print("Категорія:", result.category)
    print("Оцінна вартість:", result.estimated_value, "грн")
    print("Стан:", result.condition)
    print("Пояснення AI:", result.reasoning)