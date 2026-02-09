import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

class TestCommentForm(TestCase):
    """Тесты для формы комментариев"""
    
    def setUp(self):
        from users.forms import CommentForm
        self.form_class = CommentForm
        self.User = get_user_model()
        
        self.author = self.User.objects.create_user(
            username='author',
            email='author@example.com',
            password='test123'
        )
        self.user = self.User.objects.create_user(
            username='commenter',
            email='commenter@example.com',
            password='test123'
        )
        
        from users.models import Fanfic, Comment
        self.fanfic = Fanfic.objects.create(
            title='Тестовый фанфик',
            content='Текст фанфика',
            author=self.author
        )
        
        self.parent_comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Родительский комментарий'
        )
    
    def get_valid_form_data(self):
        """Возвращает валидные данные для формы"""
        return {
            'content': 'Это тестовый комментарий.',
            'parent_id': '',
        }
    
    def test_form_valid_data(self):
        """Тест формы с валидными данными"""
        form = self.form_class(data=self.get_valid_form_data())
        self.assertTrue(form.is_valid())
    
    def test_content_validation(self):
        """Тест валидации содержания комментария"""
        data = self.get_valid_form_data()
        
        # Слишком короткий комментарий
        data['content'] = 'а'
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Комментарий слишком короткий (минимум 3 символа)', form.errors['content'][0])
        
        # Слишком длинный комментарий
        data['content'] = 'а' * 5001
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Комментарий слишком длинный (максимум 5000 символов)', form.errors['content'][0])
        
        # Запрещенные слова
        data['content'] = 'Это спам комментарий'
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Комментарий содержит запрещенные слова', form.errors['content'][0])
    
    def test_parent_id_validation(self):
        """Тест валидации parent_id"""
        data = self.get_valid_form_data()
        
        # Ответ на существующий комментарий
        data['parent_id'] = self.parent_comment.id
        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())
        
        # Ответ на несуществующий комментарий
        data['parent_id'] = 99999
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Родительский комментарий не найден или был удален', form.errors['parent_id'][0])
    
    def test_max_reply_depth(self):
        """Тест максимальной глубины вложенности"""
        from users.models import Comment
        
        # Создаем цепочку комментариев глубиной 5
        current = self.parent_comment
        for i in range(4):
            current = Comment.objects.create(
                fanfic=self.fanfic,
                author=self.user,
                content=f'Комментарий уровня {i+2}',
                parent=current
            )
        
        # Глубина = 5, нельзя отвечать
        data = self.get_valid_form_data()
        data['parent_id'] = current.id
        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Превышена максимальная глубина вложенности комментариев (5 уровней)', form.errors['parent_id'][0])
    
    def test_form_save(self):
        """Тест сохранения формы"""
        from users.models import Comment
        
        data = self.get_valid_form_data()
        data['content'] = 'Тестовый комментарий для сохранения'
        
        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())
        
        comment = form.save(commit=False)
        comment.author = self.user
        comment.fanfic = self.fanfic
        comment.save()
        
        self.assertEqual(comment.content, 'Тестовый комментарий для сохранения')
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.fanfic, self.fanfic)

class TestCommentEditForm(TestCase):
    """Тесты для формы редактирования комментария"""
    
    def setUp(self):
        from users.forms import CommentEditForm
        self.form_class = CommentEditForm
        self.User = get_user_model()
        
        self.user = self.User.objects.create_user(
            username='commenter',
            email='commenter@example.com',
            password='test123'
        )
        
        from users.models import Fanfic, Comment
        self.fanfic = Fanfic.objects.create(
            title='Тестовый фанфик',
            content='Текст',
            author=self.user
        )
        
        self.comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Оригинальный комментарий'
        )
    
    def test_form_with_instance(self):
        """Тест формы с существующим комментарием"""
        form = self.form_class(comment=self.comment)
        self.assertEqual(form.initial.get('content'), 'Оригинальный комментарий')
    
    def test_content_validation(self):
        """Тест валидации содержания"""
        # Слишком короткий
        form = self.form_class(data={'content': 'а'}, comment=self.comment)
        self.assertFalse(form.is_valid())
        self.assertIn('Комментарий слишком короткий (минимум 3 символа)', form.errors['content'][0])
        
        # Слишком длинный
        form = self.form_class(data={'content': 'а' * 5001}, comment=self.comment)
        self.assertFalse(form.is_valid())
        self.assertIn('Комментарий слишком длинный (максимум 5000 символов)', form.errors['content'][0])
        
        # Валидный
        form = self.form_class(data={'content': 'Отредактированный комментарий'}, comment=self.comment)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """Тест сохранения формы"""
        from users.models import Comment
        
        form = self.form_class(
            data={'content': 'Отредактированный текст'},
            instance=self.comment,
            comment=self.comment
        )
        self.assertTrue(form.is_valid())
        
        updated_comment = form.save()
        self.assertEqual(updated_comment.content, 'Отредактированный текст')

class TestCommentManagementForms(TestCase):
    """Тесты для форм управления комментариями"""
    
    def setUp(self):
        from users.forms import (
            CommentDeleteForm,
            CommentSearchForm,
            CommentReportForm,
            CommentModerationForm
        )
        
        self.CommentDeleteForm = CommentDeleteForm
        self.CommentSearchForm = CommentSearchForm
        self.CommentReportForm = CommentReportForm
        self.CommentModerationForm = CommentModerationForm
        
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        
        from users.models import Fanfic, Comment
        self.fanfic = Fanfic.objects.create(
            title='Тест',
            content='Текст',
            author=self.user
        )
        
        self.comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Тестовый комментарий'
        )
    
    def test_comment_delete_form(self):
        """Тест формы удаления комментария"""
        # Обязательное подтверждение
        form = self.CommentDeleteForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)
        self.assertIn('Необходимо подтвердить удаление', form.errors['confirm'][0])
        
        # Валидная форма
        form = self.CommentDeleteForm(data={'confirm': True}, comment=self.comment)
        self.assertTrue(form.is_valid())
        
        # Форма с ответами
        form = self.CommentDeleteForm(
            data={'confirm': True, 'delete_replies': True}, 
            comment=self.comment
        )
        self.assertTrue(form.is_valid())
    
    def test_comment_search_form(self):
        """Тест формы поиска комментариев"""
        # Все поля необязательные
        form = self.CommentSearchForm(data={})
        self.assertTrue(form.is_valid())
        
        # Валидная форма
        form = self.CommentSearchForm(data={
            'search': 'текст',
            'author': 'автор',
            'sort_by': '-created_at'
        })
        self.assertTrue(form.is_valid())
        
        # Невалидные даты
        import datetime
        form = self.CommentSearchForm(data={
            'date_from': datetime.date(2024, 1, 10),
            'date_to': datetime.date(2024, 1, 1)
        })
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('Дата "с" не может быть позже даты "по"', form.errors['__all__'][0])
        
        # Валидные даты
        form = self.CommentSearchForm(data={
            'date_from': datetime.date(2024, 1, 1),
            'date_to': datetime.date(2024, 1, 10)
        })
        self.assertTrue(form.is_valid())
    
    def test_comment_report_form(self):
        """Тест формы жалобы на комментарий"""
        # Обязательная причина
        form = self.CommentReportForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('reason', form.errors)
        
        # Валидная форма
        form = self.CommentReportForm(data={'reason': 'spam'})
        self.assertTrue(form.is_valid())
        
        # Форма с деталями
        form = self.CommentReportForm(data={
            'reason': 'offensive',
            'details': 'Комментарий содержит оскорбления'
        })
        self.assertTrue(form.is_valid())
        
        # Слишком длинные детали
        form = self.CommentReportForm(data={
            'reason': 'other',
            'details': 'а' * 1001
        })
        self.assertFalse(form.is_valid())
        self.assertIn('details', form.errors)
        
        # Проверяем все причины
        for reason in ['spam', 'offensive', 'hate_speech', 'harassment', 'inappropriate', 'other']:
            form = self.CommentReportForm(data={'reason': reason})
            self.assertTrue(form.is_valid())
    
    def test_comment_moderation_form(self):
        """Тест формы модерации комментариев"""
        # Обязательные поля
        form = self.CommentModerationForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('action', form.errors)
        self.assertIn('reason', form.errors)
        
        # Слишком короткая причина
        form = self.CommentModerationForm(data={'action': 'delete', 'reason': 'а'})
        self.assertFalse(form.is_valid())
        self.assertIn('reason', form.errors)
        
        # Слишком длинная причина
        form = self.CommentModerationForm(data={
            'action': 'approve', 
            'reason': 'а' * 501
        })
        self.assertFalse(form.is_valid())
        self.assertIn('reason', form.errors)
        
        # Валидная форма
        form = self.CommentModerationForm(data={
            'action': 'delete',
            'reason': 'Комментарий нарушает правила сообщества',
            'notify_user': True
        })
        self.assertTrue(form.is_valid())
        
        # Проверяем все действия
        for action in ['approve', 'delete', 'warn', 'ban_user']:
            form = self.CommentModerationForm(data={
                'action': action,
                'reason': 'Причина действия'
            })
            self.assertTrue(form.is_valid())

@pytest.mark.django_db
def test_pytest_comment_form():
    """Pytest тест для формы комментариев"""
    from users.forms import CommentForm
    from users.models import Fanfic, Comment
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    user = User.objects.create_user(username='test', email='test@example.com', password='test123')
    author = User.objects.create_user(username='author', email='author@example.com', password='test123')
    
    fanfic = Fanfic.objects.create(
        title='Pytest фанфик',
        content='Текст',
        author=author
    )
    
    parent = Comment.objects.create(
        fanfic=fanfic,
        author=user,
        content='Родительский комментарий'
    )
    
    # Тест ответа на комментарий
    data = {
        'content': 'Ответ на комментарий',
        'parent_id': parent.id
    }
    
    form = CommentForm(data=data)
    assert form.is_valid() == True
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = user
        comment.fanfic = fanfic
        comment.save()
        assert comment.content == 'Ответ на комментарий'
        assert comment.parent == parent