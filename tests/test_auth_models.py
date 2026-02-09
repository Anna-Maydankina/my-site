import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

class TestCustomUserModel(TestCase):
    """Тесты для кастомной модели пользователя"""
    
    def setUp(self):
        self.User = get_user_model()
    
    def test_create_user(self):
        """Тест создания обычного пользователя"""
        user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            nickname='Тестовый',
            country='RU',
            phone='+79991234567'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.nickname, 'Тестовый')
        self.assertEqual(user.country, 'RU')
        self.assertEqual(user.phone, '+79991234567')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('testpass123'))
    
    def test_create_user_without_optional_fields(self):
        """Тест создания пользователя без дополнительных полей"""
        user = self.User.objects.create_user(
            username='simpleuser',
            email='simple@example.com',
            password='simplepass'
        )
        
        self.assertEqual(user.username, 'simpleuser')
        self.assertIsNone(user.nickname)
        self.assertIsNone(user.country)
        self.assertIsNone(user.phone)
    
    def test_create_superuser(self):
        """Тест создания суперпользователя"""
        admin = self.User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_active)
    
    def test_user_str(self):
        """Тест строкового представления пользователя"""
        user = self.User.objects.create_user(
            username='john_doe',
            email='john@example.com',
            password='password123'
        )
        
        self.assertEqual(str(user), 'john_doe')
    
    def test_user_get_bookmarks_count(self):
        """Тест подсчета закладок пользователя"""
        user = self.User.objects.create_user(
            username='bookmarkuser',
            email='bookmark@example.com',
            password='test123'
        )
        
        # Пока нет закладок
        self.assertEqual(user.get_bookmarks_count(), 0)
    
    def test_user_get_comments_count(self):
        """Тест подсчета комментариев пользователя"""
        user = self.User.objects.create_user(
            username='commentuser',
            email='comment@example.com',
            password='test123'
        )
        
        # Пока нет комментариев
        self.assertEqual(user.get_comments_count(), 0)
    
    def test_user_with_invalid_phone(self):
        """Тест пользователя с невалидным номером телефона"""
        from django.core.exceptions import ValidationError
        
        user = self.User.objects.create_user(
            username='invalidphone',
            email='phone@example.com',
            password='test123'
        )
        
        # Проверяем, что можно сохранить без телефона
        self.assertIsNone(user.phone)
        
        # Пробуем присвоить невалидный номер
        # (Валидация происходит при сохранении формы, а не в модели)
        user.phone = 'не номер'
        # Сохраняем - должно пройти, т.к. валидатор на уровне формы
        user.save()
    
    def test_unique_username(self):
        """Тест уникальности имени пользователя"""
        self.User.objects.create_user(
            username='uniqueuser',
            email='unique1@example.com',
            password='test123'
        )
        
        # Пробуем создать пользователя с тем же username
        with self.assertRaises(Exception):
            self.User.objects.create_user(
                username='uniqueuser',
                email='unique2@example.com',
                password='test123'
            )
    
    def test_user_email_optional(self):
        """Тест что email не обязателен (по умолчанию в Django)"""
        user = self.User.objects.create_user(
            username='noemail',
            password='test123'
        )
        
        self.assertEqual(user.username, 'noemail')
        self.assertEqual(user.email, '')  # Пустая строка по умолчанию

@pytest.mark.django_db
def test_pytest_user_creation():
    """Тест создания пользователя через pytest"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = User.objects.create_user(
        username='pytest_user',
        email='pytest@example.com',
        password='pytest123'
    )
    
    assert user.username == 'pytest_user'
    assert user.email == 'pytest@example.com'
    assert user.is_active == True
    assert user.is_staff == False
    assert user.is_superuser == False