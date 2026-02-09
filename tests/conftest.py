"""
Фикстуры для тестов.
Этот файл должен быть в папке tests/
"""

import pytest

# Может быть пустым или содержать только фикстуры
# НЕ ИСПОЛЬЗУЙТЕ settings.configure() здесь!

@pytest.fixture
def sample_fixture():
    return "test data"