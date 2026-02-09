import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

class TestFanficModel(TestCase):
    """Тесты для модели Fanfic"""
    
    def setUp(self):
        self.User = get_user_model()
        self.author = self.User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpass'
        )
    
    def test_create_fanfic(self):
        """Тест создания фанфика"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Мой первый фанфик',
            description='Описание фанфика',
            content='Текст фанфика...',
            author=self.author,
            tags='фэнтези, романтика'
        )
        
        self.assertEqual(fanfic.title, 'Мой первый фанфик')
        self.assertEqual(fanfic.author, self.author)
        self.assertEqual(fanfic.description, 'Описание фанфика')
        self.assertEqual(fanfic.content, 'Текст фанфика...')
        self.assertEqual(fanfic.status, 'draft')
        self.assertEqual(fanfic.views_count, 0)
        self.assertIsNone(fanfic.last_viewed_at)
        self.assertIsNone(fanfic.deleted_at)
        self.assertIsNone(fanfic.purge_at)
        self.assertIsNone(fanfic.archived_at)
    
    def test_fanfic_str(self):
        """Тест строкового представления фанфика"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Тестовый фанфик',
            content='Текст',
            author=self.author
        )
        
        self.assertEqual(str(fanfic), 'Тестовый фанфик')
    
    def test_fanfic_get_tags_list(self):
        """Тест получения списка тегов"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Теггированный фанфик',
            content='Текст',
            author=self.author,
            tags='фэнтези, романтика, приключения'
        )
        
        tags = fanfic.get_tags_list()
        self.assertEqual(len(tags), 3)
        self.assertIn('фэнтези', tags)
        self.assertIn('романтика', tags)
        self.assertIn('приключения', tags)
    
    def test_fanfic_get_tags_list_empty(self):
        """Тест получения списка тегов, когда их нет"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Без тегов',
            content='Текст',
            author=self.author,
            tags=''
        )
        
        tags = fanfic.get_tags_list()
        self.assertEqual(tags, [])
    
    def test_fanfic_add_tag(self):
        """Тест добавления тега"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Тестовый фанфик',
            content='Текст',
            author=self.author,
            tags='фэнтези'
        )
        
        fanfic.add_tag('романтика')
        fanfic.refresh_from_db()
        tags = fanfic.get_tags_list()
        self.assertEqual(len(tags), 2)
        self.assertIn('фэнтези', tags)
        self.assertIn('романтика', tags)
    
    def test_fanfic_remove_tag(self):
        """Тест удаления тега"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Тестовый фанфик',
            content='Текст',
            author=self.author,
            tags='фэнтези, романтика, приключения'
        )
        
        fanfic.remove_tag('романтика')
        fanfic.refresh_from_db()
        tags = fanfic.get_tags_list()
        self.assertEqual(len(tags), 2)
        self.assertIn('фэнтези', tags)
        self.assertIn('приключения', tags)
        self.assertNotIn('романтика', tags)
    
    def test_fanfic_increment_views(self):
        """Тест увеличения счетчика просмотров"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Популярный фанфик',
            content='Текст',
            author=self.author
        )
        
        # Увеличиваем просмотры
        fanfic.increment_views()
        fanfic.refresh_from_db()
        
        self.assertEqual(fanfic.views_count, 1)
        self.assertIsNotNone(fanfic.last_viewed_at)
    
    def test_fanfic_get_popularity_level(self):
        """Тест определения уровня популярности"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Тест популярности',
            content='Текст',
            author=self.author,
            views_count=0
        )
        
        self.assertEqual(fanfic.get_popularity_level(), 'fresh')
        
        fanfic.views_count = 5
        self.assertEqual(fanfic.get_popularity_level(), 'fresh')
        
        fanfic.views_count = 15
        self.assertEqual(fanfic.get_popularity_level(), 'new')
        
        fanfic.views_count = 150
        self.assertEqual(fanfic.get_popularity_level(), 'trending')
        
        fanfic.views_count = 600
        self.assertEqual(fanfic.get_popularity_level(), 'hot')
        
        fanfic.views_count = 1500
        self.assertEqual(fanfic.get_popularity_level(), 'viral')
    
    def test_fanfic_move_to_trash(self):
        """Тест перемещения фанфика в корзину"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Удаляемый фанфик',
            content='Текст',
            author=self.author,
            status='published'
        )
        
        fanfic.move_to_trash()
        fanfic.refresh_from_db()
        
        self.assertEqual(fanfic.status, 'deleted')
        self.assertIsNotNone(fanfic.deleted_at)
        self.assertIsNotNone(fanfic.purge_at)
        self.assertIsNone(fanfic.archived_at)
        
        # Проверяем, что purge_at через 30 дней
        self.assertAlmostEqual(
            (fanfic.purge_at - fanfic.deleted_at).days,
            30,
            delta=1
        )
    
    def test_fanfic_restore_from_trash(self):
        """Тест восстановления фанфика из корзины"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Восстанавливаемый фанфик',
            content='Текст',
            author=self.author,
            status='deleted',
            deleted_at=timezone.now(),
            purge_at=timezone.now() + timedelta(days=30)
        )
        
        fanfic.restore_from_trash()
        fanfic.refresh_from_db()
        
        self.assertEqual(fanfic.status, 'draft')
        self.assertIsNone(fanfic.deleted_at)
        self.assertIsNone(fanfic.purge_at)
    
    def test_fanfic_move_to_archive(self):
        """Тест перемещения фанфика в архив"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Архивный фанфик',
            content='Текст',
            author=self.author,
            status='published'
        )
        
        fanfic.move_to_archive()
        fanfic.refresh_from_db()
        
        self.assertEqual(fanfic.status, 'archived')
        self.assertIsNotNone(fanfic.archived_at)
        self.assertIsNone(fanfic.deleted_at)
        self.assertIsNone(fanfic.purge_at)
    
    def test_fanfic_is_popular_property(self):
        """Тест свойства is_popular"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Тест популярности',
            content='Текст',
            author=self.author,
            views_count=50
        )
        
        self.assertFalse(fanfic.is_popular)  # Меньше 100
        
        fanfic.views_count = 150
        self.assertTrue(fanfic.is_popular)   # Больше или равно 100
    
    def test_fanfic_days_until_purge(self):
        """Тест подсчета дней до удаления из корзины"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Фанфик в корзине',
            content='Текст',
            author=self.author,
            status='deleted',
            deleted_at=timezone.now() - timedelta(days=25),
            purge_at=timezone.now() + timedelta(days=5)
        )
        
        days = fanfic.days_until_purge
        self.assertIsNotNone(days)
        self.assertGreaterEqual(days, 4)
        self.assertLessEqual(days, 5)
    
    def test_fanfic_meta_options(self):
        """Тест мета-опций модели"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Тест мета-опций',
            content='Текст',
            author=self.author
        )
        
        self.assertEqual(fanfic._meta.verbose_name, 'Фанфик')
        self.assertEqual(fanfic._meta.verbose_name_plural, 'Фанфики')
        self.assertEqual(fanfic._meta.ordering, ['-created_at'])
    
    def test_fanfic_get_absolute_url(self):
        """Тест получения абсолютного URL"""
        from users.models import Fanfic
        
        fanfic = Fanfic.objects.create(
            title='Тест URL',
            content='Текст',
            author=self.author
        )
        
        url = fanfic.get_absolute_url()
        self.assertEqual(url, f'/fanfic/{fanfic.pk}/')  # Зависит от ваших URL паттернов

class TestViewHistoryModel(TestCase):
    """Тесты для модели истории просмотров"""
    
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='historyuser',
            email='history@example.com',
            password='test123'
        )
        self.author = self.User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpass'
        )
        
        from users.models import Fanfic
        self.fanfic = Fanfic.objects.create(
            title='Исторический фанфик',
            content='Текст',
            author=self.author
        )
    
    def test_create_view_history(self):
        """Тест создания записи истории просмотров"""
        from users.models import ViewHistory
        
        view_history = ViewHistory.objects.create(
            user=self.user,
            fanfic=self.fanfic
        )
        
        self.assertEqual(view_history.user, self.user)
        self.assertEqual(view_history.fanfic, self.fanfic)
        self.assertIsNotNone(view_history.viewed_at)
        self.assertIsNone(view_history.ip_address)
    
    def test_view_history_str(self):
        """Тест строкового представления истории просмотров"""
        from users.models import ViewHistory
        
        view_history = ViewHistory.objects.create(
            user=self.user,
            fanfic=self.fanfic
        )
        
        expected_str = f"{self.user} просмотрел {self.fanfic}"
        self.assertEqual(str(view_history), expected_str)
    
    def test_view_history_unique_together(self):
        """Тест уникальности записи пользователь-фанфик"""
        from users.models import ViewHistory
        
        # Первая запись
        ViewHistory.objects.create(user=self.user, fanfic=self.fanfic)
        
        # Вторая запись с теми же пользователем и фанфиком
        # Должна обновить существующую (update_or_create в методе increment_views)
        # Но при явном create будет ошибка
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ViewHistory.objects.create(user=self.user, fanfic=self.fanfic)

class TestBookmarkModel(TestCase):
    """Тесты для модели закладок"""
    
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='bookmarkuser',
            email='bookmark@example.com',
            password='test123'
        )
        self.author = self.User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpass'
        )
        
        from users.models import Fanfic
        self.fanfic = Fanfic.objects.create(
            title='Фанфик для закладок',
            content='Текст фанфика...',
            author=self.author
        )
    
    def test_create_bookmark(self):
        """Тест создания закладки"""
        from users.models import Bookmark
        
        bookmark = Bookmark.objects.create(
            user=self.user,
            fanfic=self.fanfic,
            notes='Интересный фанфик'
        )
        
        self.assertEqual(bookmark.user, self.user)
        self.assertEqual(bookmark.fanfic, self.fanfic)
        self.assertEqual(bookmark.notes, 'Интересный фанфик')
        self.assertIsNotNone(bookmark.created_at)
    
    def test_bookmark_str(self):
        """Тест строкового представления закладки"""
        from users.models import Bookmark
        
        bookmark = Bookmark.objects.create(
            user=self.user,
            fanfic=self.fanfic
        )
        
        expected_str = f"{self.user.username} -> {self.fanfic.title}"
        self.assertEqual(str(bookmark), expected_str)
    
    def test_bookmark_get_read_time_estimate(self):
        """Тест оценки времени чтения"""
        from users.models import Bookmark
        
        bookmark = Bookmark.objects.create(
            user=self.user,
            fanfic=self.fanfic
        )
        
        time_estimate = bookmark.get_read_time_estimate()
        self.assertIsInstance(time_estimate, int)
        self.assertGreaterEqual(time_estimate, 1)

class TestTagModels(TestCase):
    """Тесты для моделей тегов"""
    
    def test_create_tag(self):
        """Тест создания тега"""
        from users.models import Tag
        
        tag = Tag.objects.create(
            name='фэнтези',
            usage_count=10
        )
        
        self.assertEqual(tag.name, 'фэнтези')
        self.assertEqual(tag.usage_count, 10)
        self.assertIsNotNone(tag.created_at)
    
    def test_tag_str(self):
        """Тест строкового представления тега"""
        from users.models import Tag
        
        tag = Tag.objects.create(name='романтика')
        self.assertEqual(str(tag), 'романтика')
    
    def test_tag_save_lowercase(self):
        """Тест сохранения тега в нижнем регистре"""
        from users.models import Tag
        
        tag = Tag.objects.create(name='ФЭНТЕЗИ')
        self.assertEqual(tag.name, 'фэнтези')
    
    def test_create_suggested_tag(self):
        """Тест создания предлагаемого тега"""
        from users.models import SuggestedTag
        
        tag = SuggestedTag.objects.create(
            name='хёрт-комфорт',
            is_featured=True,
            usage_count=50,
            category='theme'
        )
        
        self.assertEqual(tag.name, 'хёрт-комфорт')
        self.assertTrue(tag.is_featured)
        self.assertEqual(tag.usage_count, 50)
        self.assertEqual(tag.category, 'theme')

@pytest.mark.django_db
def test_fanfic_interaction_flow():
    """Интеграционный тест взаимодействия с фанфиком"""
    from django.contrib.auth import get_user_model
    from users.models import Fanfic, Bookmark, ViewHistory
    
    User = get_user_model()
    
    author = User.objects.create_user(
        username='test_author',
        email='author@test.com',
        password='test123'
    )
    
    reader = User.objects.create_user(
        username='test_reader',
        email='reader@test.com',
        password='test123'
    )
    
    # Создаем фанфик
    fanfic = Fanfic.objects.create(
        title='Интеграционный тест',
        content='Содержание фанфика',
        author=author,
        tags='тест, интеграция'
    )
    
    # Читатель просматривает
    fanfic.increment_views(user=reader)
    fanfic.refresh_from_db()
    
    assert fanfic.views_count == 1
    
    # Читатель добавляет в закладки
    Bookmark.objects.create(user=reader, fanfic=fanfic)
    
    assert fanfic.get_bookmarks_count() == 1
    assert reader.get_bookmarks_count() == 1