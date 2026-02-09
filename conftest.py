# conftest.py в корне проекта
import pytest
import os
import django
from django.conf import settings

def pytest_configure():
    """Настройка pytest"""
    
    # Проверяем, не настроены ли уже настройки
    if not settings.configured:
        # Используем существующие настройки из fanfiction.settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fanfiction.settings')
        django.setup()