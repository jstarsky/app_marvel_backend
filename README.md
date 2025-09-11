app_marvel_backend/
│
├── requirements.txt
├── requirements-dev.txt
├── manage.py
├── .env.example
├── .gitignore
├── pytest.ini
├── db.sqlite3  # SQLite database file
│
├── app_marvel_backend/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   └── authentication/
│       ├── __init__.py
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       ├── permissions.py
│       └── tests.py
│
└── utils/
    ├── __init__.py
    └── responses.py