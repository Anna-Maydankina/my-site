import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

class TestCommentModel(TestCase):
    """Тесты для модели комментариев"""
    
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='commentuser',
            email='comment@example.com',
            password='test123'
        )
        self.author = self.User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpass'
        )
        
        from users.models import Fanfic
        self.fanfic = Fanfic.objects.create(
            title='Фанфик для комментариев',
            content='Текст фанфика...',
            author=self.author
        )
    
    def test_create_comment(self):
        """Тест создания комментария"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Отличный фанфик!'
        )
        
        self.assertEqual(comment.fanfic, self.fanfic)
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.content, 'Отличный фанфик!')
        self.assertIsNone(comment.parent)
        self.assertFalse(comment.is_deleted)
        self.assertEqual(comment.edited_count, 0)
        self.assertIsNotNone(comment.created_at)
        self.assertIsNotNone(comment.updated_at)
    
    def test_create_reply_comment(self):
        """Тест создания ответа на комментарий"""
        from users.models import Comment
        
        # Родительский комментарий
        parent_comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Первый комментарий'
        )
        
        # Ответ
        reply_comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.author,
            content='Спасибо за комментарий!',
            parent=parent_comment
        )
        
        self.assertEqual(reply_comment.parent, parent_comment)
        self.assertTrue(parent_comment.has_replies)
        self.assertEqual(parent_comment.replies_count, 1)
    
    def test_comment_str(self):
        """Тест строкового представления комментария"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Тестовый комментарий'
        )
        
        # Проверяем, что строка содержит нужные элементы
        str_repr = str(comment)
        self.assertIn(str(self.user), str_repr)
        self.assertIn(self.fanfic.title[:30], str_repr)
    
    def test_comment_soft_delete(self):
        """Тест мягкого удаления комментария"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Удаляемый комментарий'
        )
        
        comment.soft_delete()
        comment.refresh_from_db()
        
        self.assertTrue(comment.is_deleted)
        self.assertEqual(comment.content, '[Комментарий удален]')
    
    def test_comment_restore(self):
        """Тест восстановления комментария"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Удаленный комментарий',
            is_deleted=True
        )
        
        comment.restore()
        comment.refresh_from_db()
        
        self.assertFalse(comment.is_deleted)
    
    def test_comment_edit_content(self):
        """Тест редактирования комментария"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Исходный комментарий'
        )
        
        # Редактирование автором
        success = comment.edit_content('Отредактированный комментарий', self.user)
        comment.refresh_from_db()
        
        self.assertTrue(success)
        self.assertEqual(comment.content, 'Отредактированный комментарий')
        self.assertEqual(comment.edited_count, 1)
    
    def test_comment_cannot_edit_by_other_user(self):
        """Тест что нельзя редактировать чужой комментарий"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Мой комментарий'
        )
        
        # Другой пользователь пытается редактировать
        other_user = self.User.objects.create_user(
            username='other',
            email='other@example.com',
            password='test123'
        )
        
        success = comment.edit_content('Попытка редактирования', other_user)
        
        self.assertFalse(success)
        self.assertEqual(comment.content, 'Мой комментарий')
        self.assertEqual(comment.edited_count, 0)
    
    def test_comment_can_edit_permissions(self):
        """Тест проверки прав на редактирование"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Комментарий'
        )
        
        # Автор может редактировать
        self.assertTrue(comment.can_edit(self.user))
        
        # Другой пользователь не может
        other_user = self.User.objects.create_user(
            username='other',
            email='other@example.com',
            password='test123'
        )
        self.assertFalse(comment.can_edit(other_user))
        
        # Staff может редактировать
        staff_user = self.User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='test123',
            is_staff=True
        )
        self.assertTrue(comment.can_edit(staff_user))
    
    def test_comment_can_delete_permissions(self):
        """Тест проверки прав на удаление"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Комментарий'
        )
        
        # Автор может удалять
        self.assertTrue(comment.can_delete(self.user))
        
        # Автор фанфика может удалять
        self.assertTrue(comment.can_delete(self.author))
        
        # Другой пользователь не может
        other_user = self.User.objects.create_user(
            username='other',
            email='other@example.com',
            password='test123'
        )
        self.assertFalse(comment.can_delete(other_user))
        
        # Staff может удалять
        staff_user = self.User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='test123',
            is_staff=True
        )
        self.assertTrue(comment.can_delete(staff_user))
    
    def test_comment_is_edited_property(self):
        """Тест свойства is_edited"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Комментарий'
        )
        
        # Сразу после создания
        self.assertFalse(comment.is_edited)
        
        # После редактирования
        comment.edit_content('Отредактировано', self.user)
        comment.refresh_from_db()
        self.assertTrue(comment.is_edited)
    
    def test_comment_get_reply_depth(self):
        """Тест определения глубины вложенности"""
        from users.models import Comment
        
        # Уровень 0
        level0 = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Корневой комментарий'
        )
        
        # Уровень 1
        level1 = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.author,
            content='Ответ уровня 1',
            parent=level0
        )
        
        # Уровень 2
        level2 = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Ответ уровня 2',
            parent=level1
        )
        
        self.assertEqual(level0.get_reply_depth(), 0)
        self.assertEqual(level1.get_reply_depth(), 1)
        self.assertEqual(level2.get_reply_depth(), 2)
    
    def test_comment_can_reply(self):
        """Тест проверки возможности ответа"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Комментарий'
        )
        
        # Неавторизованный пользователь не может ответить
        self.assertFalse(comment.can_reply(None))
        
        # Авторизованный пользователь может
        self.assertTrue(comment.can_reply(self.author))
    
    def test_comment_cannot_reply_to_deleted(self):
        """Тест что нельзя ответить на удаленный комментарий"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Комментарий',
            is_deleted=True
        )
        
        self.assertFalse(comment.can_reply(self.author))
    
    def test_comment_get_all_replies(self):
        """Тест получения всех ответов"""
        from users.models import Comment
        
        root = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Корневой'
        )
        
        reply1 = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.author,
            content='Ответ 1',
            parent=root
        )
        
        reply2 = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Ответ 2',
            parent=reply1
        )
        
        all_replies = root.get_all_replies()
        
        self.assertEqual(len(all_replies), 2)
        self.assertIn(reply1, all_replies)
        self.assertIn(reply2, all_replies)
    
    def test_comment_display_content(self):
        """Тест отображаемого содержимого"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Нормальный комментарий'
        )
        
        self.assertEqual(comment.display_content, 'Нормальный комментарий')
        
        comment.is_deleted = True
        comment.save()
        
        self.assertEqual(comment.display_content, '[Комментарий удален]')
    
    def test_comment_save_cleanup(self):
        """Тест очистки контента при сохранении"""
        from users.models import Comment
        
        comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='   Комментарий с пробелами   '
        )
        
        self.assertEqual(comment.content, 'Комментарий с пробелами')

class TestCommentLikeModel(TestCase):
    """Тесты для модели лайков комментариев"""
    
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='likeuser',
            email='like@example.com',
            password='test123'
        )
        self.author = self.User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpass'
        )
        
        from users.models import Fanfic, Comment
        self.fanfic = Fanfic.objects.create(
            title='Фанфик для лайков',
            content='Текст',
            author=self.author
        )
        self.comment = Comment.objects.create(
            fanfic=self.fanfic,
            author=self.user,
            content='Комментарий для лайка'
        )
    
    def test_create_comment_like(self):
        """Тест создания лайка комментария"""
        from users.models import CommentLike
        
        like = CommentLike.objects.create(
            comment=self.comment,
            user=self.user
        )
        
        self.assertEqual(like.comment, self.comment)
        self.assertEqual(like.user, self.user)
        self.assertIsNotNone(like.created_at)
    
    def test_comment_like_str(self):
        """Тест строкового представления лайка"""
        from users.models import CommentLike
        
        like = CommentLike.objects.create(
            comment=self.comment,
            user=self.user
        )
        
        expected_str = f"{self.user} лайкнул комментарий #{self.comment.id}"
        self.assertEqual(str(like), expected_str)
    
    def test_comment_like_unique_together(self):
        """Тест уникальности лайка комментарий-пользователь"""
        from users.models import CommentLike
        
        # Первый лайк
        CommentLike.objects.create(comment=self.comment, user=self.user)
        
        # Второй лайк от того же пользователя
        # Должен вызвать ошибку
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            CommentLike.objects.create(comment=self.comment, user=self.user)

@pytest.mark.django_db
def test_comments_tree_structure():
    """Тест древовидной структуры комментариев"""
    from django.contrib.auth import get_user_model
    from users.models import Fanfic, Comment
    
    User = get_user_model()
    
    user1 = User.objects.create_user(
        username='user1',
        email='user1@test.com',
        password='test123'
    )
    
    user2 = User.objects.create_user(
        username='user2',
        email='user2@test.com',
        password='test123'
    )
    
    author = User.objects.create_user(
        username='author',
        email='author@test.com',
        password='test123'
    )
    
    fanfic = Fanfic.objects.create(
        title='Тест комментариев',
        content='Содержание',
        author=author
    )
    
    # Создаем дерево комментариев
    comment1 = Comment.objects.create(
        fanfic=fanfic,
        author=user1,
        content='Первый комментарий'
    )
    
    comment2 = Comment.objects.create(
        fanfic=fanfic,
        author=user2,
        content='Ответ на первый',
        parent=comment1
    )
    
    comment3 = Comment.objects.create(
        fanfic=fanfic,
        author=user1,
        content='Ответ на ответ',
        parent=comment2
    )
    
    # Проверяем структуру
    assert comment1.is_root == True
    assert comment2.is_root == False
    assert comment1.has_replies == True
    assert comment1.replies_count == 1
    assert comment2.replies_count == 1
    
    # Проверяем глубину
    assert comment1.get_reply_depth() == 0
    assert comment2.get_reply_depth() == 1
    assert comment3.get_reply_depth() == 2

@pytest.mark.django_db
def test_comment_class_methods():
    """Тест классовых методов комментариев"""
    from django.contrib.auth import get_user_model
    from users.models import Fanfic, Comment
    
    User = get_user_model()
    
    user = User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='test123'
    )
    
    author = User.objects.create_user(
        username='author',
        email='author@test.com',
        password='test123'
    )
    
    fanfic = Fanfic.objects.create(
        title='Тест методов',
        content='Содержание',
        author=author
    )
    
    # Создаем несколько комментариев
    Comment.objects.create(
        fanfic=fanfic,
        author=user,
        content='Комментарий 1'
    )
    
    Comment.objects.create(
        fanfic=fanfic,
        author=author,
        content='Комментарий 2'
    )
    
    Comment.objects.create(
        fanfic=fanfic,
        author=user,
        content='Комментарий 3',
        is_deleted=True
    )
    
    # Тестируем get_comments_for_fanfic
    comments = Comment.get_comments_for_fanfic(fanfic.id)
    assert len(comments) == 2  # Два не удаленных комментария
    
    # Тестируем get_user_comments
    user_comments = Comment.get_user_comments(user.id)
    assert len(user_comments) == 1  # Один не удаленный комментарий
    
    user_comments_all = Comment.get_user_comments(user.id, include_deleted=True)
    assert len(user_comments_all) == 2  # Два комментария включая удаленный