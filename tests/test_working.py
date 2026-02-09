import pytest

def test_simple():
    """Простейший тест"""
    assert 1 + 1 == 2

@pytest.mark.django_db
def test_django_works():
    """Проверяем, что Django работает"""
    from django.conf import settings
    
    assert settings.SECRET_KEY is not None
    assert 'django.contrib.auth' in settings.INSTALLED_APPS
    assert 'main' in settings.INSTALLED_APPS
    
    print("✓ Django настроен корректно")

@pytest.mark.django_db
def test_create_user():
    """Тест создания пользователя"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    assert user.pk is not None
    assert user.username == 'testuser'
    assert user.check_password('testpass123')
    print(f"✓ Пользователь создан: {user.username}")