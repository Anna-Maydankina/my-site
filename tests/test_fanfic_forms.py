import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

class TestFanficForm(TestCase):
    """Тесты для формы фанфика"""
    
    def setUp(self):
        from users.forms import FanficForm
        self.form_class = FanficForm
        self.User = get_user_model()
        
        self.user = self.User.objects.create_user(
            username='author',
            email='author@example.com',
            password='test123'
        )
    
    def get_valid_form_data(self):
        """Возвращает валидные данные для формы"""
        return {
            'title': 'Мой тестовый фанфик',
            'description': 'Описание тестового фанфика',
            'content': 'Текст моего фанфика.',
            'tags': 'фэнтези, романтика',
        }
    
    def test_form_valid_data(self):
        """Тест формы с валидными данными"""
        form = self.form_class(data=self.get_valid_form_data())
        self.assertTrue(form.is_valid())
    
    def test_required_fields(self):
        """Тест обязательных полей"""
        form = self.form_class(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('content', form.errors)
        self.assertIn('Обязательное поле.', form.errors['title'][0])
        self.assertIn('Обязательное поле.', form.errors['content'][0])
    
    def test_title_validation(self):
        """Тест валидации названия"""
        data = self.get_valid_form_data()
        
        # Пустой заголовок
        data['title'] = ''
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Название не может быть пустым', form.errors['title'][0])
        
        # Обрезка пробелов
        data['title'] = '  Тестовый фанфик  '
        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['title'], 'Тестовый фанфик')
    
    def test_content_validation(self):
        """Тест валидации содержания"""
        data = self.get_valid_form_data()
        
        # Пустое содержание
        data['content'] = ''
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Содержание не может быть пустым', form.errors['content'][0])
    
    def test_tags_validation(self):
        """Тест валидации тегов"""
        data = self.get_valid_form_data()
        
        # Слишком много тегов
        data['tags'] = ', '.join([f'тег{i}' for i in range(15)])
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Максимальное количество тегов - 10', form.errors['tags'][0])
        
        # Пустые теги
        data['tags'] = ', , ,'
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Введите хотя бы один тег', form.errors['tags'][0])
        
        # Нормализация тегов
        data['tags'] = '  фэнтези , романтика  , приключения  '
        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['tags'], 'фэнтези, романтика, приключения')
    
    def test_form_save(self):
        """Тест сохранения формы"""
        from users.models import Fanfic
        
        data = self.get_valid_form_data()
        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())
        
        fanfic = form.save(commit=False)
        fanfic.author = self.user
        fanfic.save()
        
        self.assertEqual(fanfic.title, 'Мой тестовый фанфик')
        self.assertEqual(fanfic.author, self.user)
        self.assertEqual(fanfic.status, 'draft')
        self.assertEqual(fanfic.tags, 'фэнтези, романтика')

class TestFanficManagementForms(TestCase):
    """Тесты для форм управления фанфиками (удаление, восстановление)"""
    
    def setUp(self):
        from users.forms import (
            FanficDeleteForm, 
            FanficRestoreForm,
            EmptyTrashForm,
            BulkActionForm,
            FanficSearchForm
        )
        
        self.FanficDeleteForm = FanficDeleteForm
        self.FanficRestoreForm = FanficRestoreForm
        self.EmptyTrashForm = EmptyTrashForm
        self.BulkActionForm = BulkActionForm
        self.FanficSearchForm = FanficSearchForm
        
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
    
    def test_fanfic_delete_form(self):
        """Тест формы удаления фанфика"""
        # Обязательное подтверждение
        form = self.FanficDeleteForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)
        self.assertIn('Необходимо подтвердить удаление', form.errors['confirm'][0])
        
        # Валидная форма
        form = self.FanficDeleteForm(data={'confirm': True})
        self.assertTrue(form.is_valid())
        
        # С опцией удаления навсегда
        form = self.FanficDeleteForm(data={'confirm': True, 'permanent': True})
        self.assertTrue(form.is_valid())
    
    def test_fanfic_restore_form(self):
        """Тест формы восстановления фанфика"""
        # Обязательный выбор статуса
        form = self.FanficRestoreForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('restore_status', form.errors)
        
        # Валидная форма
        form = self.FanficRestoreForm(data={'restore_status': 'draft'})
        self.assertTrue(form.is_valid())
        
        # Проверяем варианты статусов
        for status in ['draft', 'archived', 'published']:
            form = self.FanficRestoreForm(data={'restore_status': status})
            self.assertTrue(form.is_valid())
    
    def test_empty_trash_form(self):
        """Тест формы очистки корзины"""
        # Обязательное подтверждение
        form = self.EmptyTrashForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)
        
        # Валидная форма
        form = self.EmptyTrashForm(data={'confirm': True})
        self.assertTrue(form.is_valid())
    
    def test_bulk_action_form(self):
        """Тест формы массовых действий"""
        # Обязательное действие
        form = self.BulkActionForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('action', form.errors)
        self.assertIn('fanfic_ids', form.errors)
        
        # Невалидные ID
        form = self.BulkActionForm(data={'action': 'publish', 'fanfic_ids': 'not-numbers'})
        self.assertFalse(form.is_valid())
        self.assertIn('fanfic_ids', form.errors)
        
        # Пустые ID
        form = self.BulkActionForm(data={'action': 'publish', 'fanfic_ids': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('fanfic_ids', form.errors)
        
        # Валидная форма
        form = self.BulkActionForm(data={'action': 'publish', 'fanfic_ids': '1,2,3'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['fanfic_ids'], [1, 2, 3])
        
        # Проверяем все действия
        for action in ['publish', 'archive', 'trash', 'delete', 'restore']:
            form = self.BulkActionForm(data={'action': action, 'fanfic_ids': '1,2'})
            self.assertTrue(form.is_valid())
    
    def test_fanfic_search_form(self):
        """Тест формы поиска фанфиков"""
        # Все поля необязательные
        form = self.FanficSearchForm(data={})
        self.assertTrue(form.is_valid())
        
        # Валидная форма с поиском
        form = self.FanficSearchForm(data={'search': 'фэнтези', 'sort_by': 'title'})
        self.assertTrue(form.is_valid())
        
        # Проверяем варианты сортировки
        for sort in ['deleted_at', '-deleted_at', 'purge_at', 'title']:
            form = self.FanficSearchForm(data={'sort_by': sort})
            self.assertTrue(form.is_valid())
        
        # Проверяем фильтр по дням
        for days in ['7', '3', '1']:
            form = self.FanficSearchForm(data={'days_left': days})
            self.assertTrue(form.is_valid())

class TestTagSearchForm(TestCase):
    """Тесты для формы поиска по тегам"""
    
    def test_tag_search_form(self):
        """Тест формы поиска по тегам"""
        from users.forms import TagSearchForm
        
        # Обязательное поле tags
        form = TagSearchForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('tags', form.errors)
        
        # Пустые теги
        form = TagSearchForm(data={'tags': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('tags', form.errors)
        
        # Слишком много тегов
        form = TagSearchForm(data={'tags': 'тег1, тег2, тег3, тег4, тег5, тег6'})
        self.assertFalse(form.is_valid())
        self.assertIn('tags', form.errors)
        self.assertIn('Максимальное количество тегов для поиска - 5', form.errors['tags'][0])
        
        # Валидная форма
        form = TagSearchForm(data={'tags': 'фэнтези, романтика'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['tags'], 'фэнтези, романтика')
        
        # Нормализация тегов
        form = TagSearchForm(data={'tags': '  фэнтези , романтика  '})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['tags'], 'фэнтези, романтика')

@pytest.mark.django_db
def test_pytest_fanfic_form():
    """Pytest тест для формы фанфика"""
    from users.forms import FanficForm
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    user = User.objects.create_user(username='test', email='test@example.com', password='test123')
    
    data = {
        'title': 'Pytest фанфик',
        'description': 'Описание pytest фанфика',
        'content': 'Содержание pytest фанфика.',
        'tags': 'тест, pytest'
    }
    
    form = FanficForm(data=data)
    assert form.is_valid() == True
    
    if form.is_valid():
        fanfic = form.save(commit=False)
        fanfic.author = user
        fanfic.save()
        assert fanfic.title == 'Pytest фанфик'
        assert fanfic.author == user
        assert fanfic.tags == 'тест, pytest'