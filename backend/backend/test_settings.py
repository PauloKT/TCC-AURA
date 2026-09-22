"""Configuração de testes: SQLite em disco permite testar espera entre conexões."""
from .settings import *  # noqa: F403

if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':  # noqa: F405
    # Nunca usar db.sqlite3: Django cria e remove somente este banco de testes.
    DATABASES['default']['TEST'] = {'NAME': BASE_DIR / 'test-aura.sqlite3'}  # noqa: F405
