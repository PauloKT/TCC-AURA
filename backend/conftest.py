"""
Configuração pytest-django.

Aponta o DJANGO_SETTINGS_MODULE e desabilita migrações para testes
mais rápidos (cada TestCase cria seu próprio schema em SQLite in-memory).
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
