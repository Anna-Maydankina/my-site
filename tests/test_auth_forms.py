import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django import forms

class TestRegistrationForm(TestCase):
    """Тесты для формы регистрации"""
    
    def setUp(self):
        from users.forms import RegistrationForm
        self.form_class = RegistrationForm
        self.User = get_user_model()
    
    def get_valid_form_data(self):
        """Возвращает валидные данные для формы"""
        return {
            'username': 'testuser',
            'nickname': 'Тестовый',
            'email': 'test@example.com',
            'country': 'RU',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        }
    
    def test_form_valid_data(self):
        """Тест формы с валидными данными"""
        form = self.form_class(data=self.get_valid_form_data())
        self.assertTrue(form.is_valid())
    
    def test_form_required_fields(self):
        """Тест обязательных полей"""
        form = self.form_class(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('nickname', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('country', form.errors)
        self.assertIn('password1', form.errors)
        self.assertIn('password2', form.errors)
    
    def test_username_validation(self):
        """Тест валидации имени пользователя"""
        data = self.get_valid_form_data()
        
        # Слишком короткое имя
        data['username'] = 'ab'
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Имя пользователя должно содержать минимум 3 символа', form.errors['username'][0])
        
        # Пустое имя
        data['username'] = ''
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Имя пользователя не может быть пустым', form.errors['username'][0])
    
    def test_username_uniqueness(self):
        """Тест уникальности имени пользователя"""
        self.User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='test123'
        )
        
        data = self.get_valid_form_data()
        data['username'] = 'existinguser'
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Пользователь с таким именем уже существует', form.errors['username'][0])
    
    def test_nickname_validation(self):
        """Тест валидации никнейма"""
        data = self.get_valid_form_data()
        
        # Слишком короткий никнейм
        data['nickname'] = 'а'
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Никнейм должен содержать минимум 2 символа', form.errors['nickname'][0])
        
        # Пустой никнейм
        data['nickname'] = ''
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Никнейм не может быть пустым', form.errors['nickname'][0])
    
    def test_email_validation(self):
        """Тест валидации email"""
        data = self.get_valid_form_data()
        
        # Невалидный email
        data['email'] = 'not-an-email'
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        
        # Пустой email
        data['email'] = ''
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Email не может быть пустым', form.errors['email'][0])
        
        # Email с пробелами (должен обрезаться)
        data['email'] = '  test@example.com  '
        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'test@example.com')
    
    def test_email_uniqueness(self):
        """Тест уникальности email"""
        self.User.objects.create_user(
            username='user1',
            email='existing@example.com',
            password='test123'
        )
        
        data = self.get_valid_form_data()
        data['email'] = 'existing@example.com'
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Пользователь с таким email уже существует', form.errors['email'][0])
    
    def test_password_validation(self):
        """Тест валидации пароля"""
        data = self.get_valid_form_data()
        
        # Пароли не совпадают
        data['password1'] = 'Password123!'
        data['password2'] = 'DifferentPassword123!'
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Пароли не совпадают', form.errors['password2'][0])
        
        # Слишком короткий пароль
        data['password1'] = 'short'
        data['password2'] = 'short'
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Пароль должен содержать минимум 8 символов', form.errors['password2'][0])
    
    def test_phone_validation(self):
        """Тест валидации телефона"""
        data = self.get_valid_form_data()
        
        # Валидный телефон
        data['phone'] = '+79991234567'
        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())
        
        # Невалидный телефон
        data['phone'] = 'not-a-phone'
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        
        # Пустой телефон (допустимо)
        data['phone'] = ''
        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data['phone'])
    
    def test_phone_uniqueness(self):
        """Тест уникальности телефона"""
        self.User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='test123',
            phone='+79991234567'
        )
        
        data = self.get_valid_form_data()
        data['phone'] = '+79991234567'
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Этот номер телефона уже используется', form.errors['phone'][0])
    
    def test_form_save(self):
        """Тест сохранения формы"""
        data = self.get_valid_form_data()
        data['phone'] = '+79991234567'
        
        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.nickname, 'Тестовый')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.country, 'RU')
        self.assertEqual(user.phone, '+79991234567')
        self.assertTrue(user.check_password('StrongPassword123!'))

class TestLoginForm(TestCase):
    """Тесты для формы входа"""
    
    def test_login_form_valid(self):
        """Тест валидной формы входа"""
        from users.forms import LoginForm
        
        data = {'username': 'testuser', 'password': 'password123'}
        form = LoginForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_login_form_empty(self):
        """Тест пустой формы входа"""
        from users.forms import LoginForm
        
        form = LoginForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('password', form.errors)
        self.assertEqual(form.errors['username'][0], 'Обязательное поле.')
        self.assertEqual(form.errors['password'][0], 'Обязательное поле.')
    
    def test_login_form_widgets(self):
        """Тест виджетов формы входа"""
        from users.forms import LoginForm
        
        form = LoginForm()
        self.assertEqual(form.fields['username'].widget.attrs.get('class'), 'form-control')
        self.assertEqual(form.fields['password'].widget.attrs.get('class'), 'form-control')
        self.assertIsInstance(form.fields['password'].widget, forms.PasswordInput)

class TestProfileEditForm(TestCase):
    """Тесты для формы редактирования профиля"""
    
    def setUp(self):
        from users.forms import ProfileEditForm
        self.form_class = ProfileEditForm
        self.User = get_user_model()
        
        self.user = self.User.objects.create_user(
            username='originaluser',
            nickname='Оригинал',
            email='original@example.com',
            country='US',
            password='test123',
            phone='+79998887766'
        )
    
    def get_valid_form_data(self):
        """Возвращает валидные данные для формы"""
        return {
            'username': 'updateduser',
            'nickname': 'Обновленный',
            'email': 'updated@example.com',
            'country': 'RU',
            'phone': '+79991234567',
        }
    
    def test_form_valid_data(self):
        """Тест формы с валидными данными"""
        form = self.form_class(data=self.get_valid_form_data(), user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_form_with_instance(self):
        """Тест формы с существующим экземпляром"""
        form = self.form_class(instance=self.user, user=self.user)
        self.assertEqual(form.initial.get('username'), 'originaluser')
        self.assertEqual(form.initial.get('email'), 'original@example.com')
    
    def test_username_uniqueness_with_exclusion(self):
        """Тест уникальности username с исключением текущего пользователя"""
        self.User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='test123'
        )
        
        data = self.get_valid_form_data()
        data['username'] = 'otheruser'
        form = self.form_class(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Пользователь с таким именем уже существует', form.errors['username'][0])
    
    def test_email_uniqueness_with_exclusion(self):
        """Тест уникальности email с исключением текущего пользователя"""
        self.User.objects.create_user(
            username='user2',
            email='other@example.com',
            password='test123'
        )
        
        data = self.get_valid_form_data()
        data['email'] = 'other@example.com'
        form = self.form_class(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Пользователь с таким email уже существует', form.errors['email'][0])
    
    def test_phone_uniqueness_with_exclusion(self):
        """Тест уникальности телефона с исключением текущего пользователя"""
        self.User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='test123',
            phone='+79991112233'
        )
        
        data = self.get_valid_form_data()
        data['phone'] = '+79991112233'
        form = self.form_class(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Этот номер телефона уже используется', form.errors['phone'][0])
    
    def test_form_save(self):
        """Тест сохранения формы"""
        data = self.get_valid_form_data()
        form = self.form_class(data=data, instance=self.user, user=self.user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        self.assertEqual(updated_user.username, 'updateduser')
        self.assertEqual(updated_user.email, 'updated@example.com')
        self.assertEqual(updated_user.country, 'RU')
        self.assertEqual(updated_user.phone, '+79991234567')

@pytest.mark.django_db
def test_pytest_registration_form():
    """Pytest тест для формы регистрации"""
    from users.forms import RegistrationForm
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Валидные данные
    data = {
        'username': 'pytestuser',
        'nickname': 'Pytest',
        'email': 'pytest@example.com',
        'country': 'RU',
        'password1': 'PytestPass123!',
        'password2': 'PytestPass123!',
        'phone': '+79991234567'
    }
    
    form = RegistrationForm(data=data)
    assert form.is_valid() == True
    
    if form.is_valid():
        user = form.save()
        assert user.username == 'pytestuser'
        assert user.email == 'pytest@example.com'
        assert user.phone == '+79991234567'