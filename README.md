# Pawnshop Scoring — Django REST API

Сервіс для ломбарду: приймає заявку клієнта на позику під заставу, за фото застави автоматично визначає її категорію та орієнтовну вартість (Google Gemini Vision), і на основі доходу клієнта, його боргів та вартості застави приймає рішення — схвалити позику чи відмовити, і на яку суму.

## Стек

- Python 3.13, Django 6.1.1, Django REST Framework
- SQLite (dev)
- Google Gemini Vision API (`google-genai`) — розпізнавання застави по фото
- pytest + pytest-django — тести

## Архітектура

```
Client (клієнт)
   │  1───N
   ▼
Application (заявка) ──1───1── Collateral (застава)
```

- **Client** — ПІБ, телефон, дохід, поточні борги.
- **Collateral** — фото застави + поля, які заповнює AI: категорія (`watch` / `jewelry` / `electronics` / `other`), оцінна вартість, стан (`new` / `good` / `fair` / `poor`), сире пояснення від моделі.
- **Application** — заявка: посилається на клієнта і (опційно) на заставу, зберігає статус (`pending` / `approved` / `rejected`) і запропоновану суму позики.

### Потік запиту

1. `POST /api/collaterals/` з фото → сервер зберігає файл, відправляє його в Gemini Vision (`applications/ai_vision.py`), отримує структуровану відповідь (Pydantic `CollateralEstimate`: категорія, вартість, стан, пояснення) і записує її в `Collateral`.
2. `POST /api/applications/` з даними клієнта (і, опційно, `collateral_id`) → створює/знаходить клієнта (`get_or_create` по телефону), створює заявку і одразу викликає `calculate_scoring()`.
3. `GET /api/applications/<id>/` → повертає деталі заявки разом із клієнтом.

### Логіка скорингу (`Application.calculate_scoring`)

```python
income_to_debt_ok = self.client_income > (self.existing_debts * 2)
collateral_value_ok = self.collateral.estimated_value > 500

if income_to_debt_ok and collateral_value_ok:
    status = "approved"
    proposed_loan_amount = collateral.estimated_value * 0.7   # 70% від вартості застави
else:
    status = "rejected"
```

Якщо застави ще немає (`collateral` не прив'язана або AI ще не оцінив вартість) — заявка лишається `pending`, без відмови.

Правило спрощене навмисно (rule-based, без ML) — головна мета була показати чисту, тестовану бізнес-логіку, а не складну модель.

## Запуск локально

```bash
git clone https://github.com/MAJIbTA26/pawnshop-scoring-django.git
cd pawnshop-scoring-django

python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# .env у корені проєкту:
# GEMINI_API_KEY=your_key_here

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API буде доступне на `http://127.0.0.1:8000/api/`, адмінка — на `/admin/`.

## Тести

```bash
pytest
```

5 тестів на `calculate_scoring()`:
- схвалення при хорошому доході і достатній вартості застави
- відмова при заниженій вартості застави
- відмова при завеликих боргах
- `pending`, коли застави ще немає
- `pending`, коли застава є, але AI ще не оцінив вартість

## Відомі обмеження і що зробив би далі

- **Celery + Redis** — виклик Gemini Vision зараз синхронний і блокує запит на кілька секунд; в проді варто винести це в фонову чергу.
- **Один ендпоінт на заставу** — зараз застава створюється окремим запитом, а не вкладено всередині заявки; можна об'єднати в один POST.
- **SQLite** — тільки для розробки, для продакшену — міграція на PostgreSQL (Neon).
- **Rate limit / retry для Gemini** — базовий retry з backoff вже є на 503, але немає загального rate-лімітера на клієнтські запити.
- **Аутентифікація** — API зараз відкрите, немає токенів/JWT для клієнтів.

## Приклад

Фото фігурки штурмовика → AI визначив: категорія `other`, оцінна вартість `250 грн`, стан `good`, з детальним поясненням чому саме така оцінка.
