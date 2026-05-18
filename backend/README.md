# IELTS Vocabulary Backend

FastAPI backend for IELTS vocabulary learning app.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── chapter.py
│   │   ├── word.py
│   │   └── settings.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── chapter.py
│   │   ├── word.py
│   │   └── settings.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── chapters.py
│   │   ├── words.py
│   │   └── settings.py
│   └── core/
│       ├── __init__.py
│       ├── security.py
│       └── deps.py
├── alembic/
│   └── versions/
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

3. Initialize database:
```bash
alembic upgrade head
```

4. Run server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
