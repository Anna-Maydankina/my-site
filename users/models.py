from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.core.validators import RegexValidator
from .countries import COUNTRIES

class CustomUser(AbstractUser):
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name='Никнейм')
    country = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name='Страна',
        choices=COUNTRIES
    )
    
    # === ДОБАВЛЕННОЕ ПОЛЕ ТЕЛЕФОНА ===
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. Максимум 15 цифр."
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        verbose_name='Номер телефона',
        help_text='Формат: +79991234567'
    )
    
    def __str__(self):
        return self.username
    
    def get_bookmarks_count(self):
        """Возвращает количество закладок пользователя"""
        return self.bookmarks.count()
    
    def get_comments_count(self):
        """Возвращает количество комментариев пользователя"""
        return self.comment_set.count()

class Fanfic(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
        ('archived', 'В архиве'),
        ('deleted', 'В корзине'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    content = models.TextField(verbose_name='Текст фанфика')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Автор')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    tags = models.CharField(max_length=500, blank=True, verbose_name='Теги (через запятую)')
    
    # === СИСТЕМА ПРОСМОТРОВ ===
    views_count = models.PositiveIntegerField(default=0, verbose_name='Количество просмотров')
    last_viewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Последний просмотр')
    
    # Поля для корзины
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата удаления в корзину")
    purge_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата окончательного удаления")
    
    # Поле для архива
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата архивации")
    
    class Meta:
        verbose_name = 'Фанфик'
        verbose_name_plural = 'Фанфики'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-views_count']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('fanfic_detail', kwargs={'pk': self.pk})
    
    def get_tags_list(self):
        """Возвращает теги в виде очищенного списка"""
        if self.tags:
            tags = [tag.strip().lower() for tag in self.tags.split(',')]
            return [tag for tag in tags if tag]
        return []
    
    def add_tag(self, tag):
        """Добавляет тег к фанфику"""
        current_tags = self.get_tags_list()
        tag_lower = tag.strip().lower()
        
        if tag_lower and tag_lower not in current_tags:
            if self.tags:
                self.tags += f", {tag}"
            else:
                self.tags = tag
            self.save()
    
    def remove_tag(self, tag):
        """Удаляет тег из фанфика"""
        current_tags = self.get_tags_list()
        tag_lower = tag.strip().lower()
        
        if tag_lower in current_tags:
            current_tags.remove(tag_lower)
            self.tags = ', '.join(current_tags)
            self.save()
    
    # === СИСТЕМА ПРОСМОТРОВ ===
    def increment_views(self, user=None):
        """Увеличивает счетчик просмотров"""
        from django.db.models import F
        
        # Атомарное увеличение счетчика
        Fanfic.objects.filter(pk=self.pk).update(
            views_count=F('views_count') + 1,
            last_viewed_at=timezone.now()
        )
        
        # Обновляем объект в памяти
        self.refresh_from_db()
        
        # Если пользователь авторизован, обновляем историю просмотров
        if user and user.is_authenticated:
            ViewHistory.objects.update_or_create(
                user=user,
                fanfic=self,
                defaults={'viewed_at': timezone.now()}
            )
    
    def get_popularity_level(self):
        """Возвращает уровень популярности фанфика"""
        if self.views_count >= 1000:
            return 'viral'
        elif self.views_count >= 500:
            return 'hot'
        elif self.views_count >= 100:
            return 'trending'
        elif self.views_count >= 10:
            return 'new'
        else:
            return 'fresh'
    
    def get_popularity_badge_class(self):
        """Возвращает CSS класс для бейджа популярности"""
        levels = {
            'viral': 'badge-popularity-viral',
            'hot': 'badge-popularity-hot',
            'trending': 'badge-popularity-trending',
            'new': 'badge-popularity-new',
            'fresh': 'badge-popularity-fresh'
        }
        return levels.get(self.get_popularity_level(), '')
    
    def get_popularity_text(self):
        """Возвращает текстовое описание популярности"""
        texts = {
            'viral': '🔥 Вирусный',
            'hot': '🔥 Горячий',
            'trending': '📈 Набирает популярность',
            'new': '✨ Новый',
            'fresh': '🌱 Свежий'
        }
        return texts.get(self.get_popularity_level(), '')
    
    # === Методы для корзины ===
    def move_to_trash(self):
        """Перемещает фанфик в корзину (удаление через 30 дней)"""
        self.status = 'deleted'
        self.deleted_at = timezone.now()
        self.purge_at = timezone.now() + timedelta(days=30)
        self.archived_at = None
        self.save()
        return self
    
    def restore_from_trash(self):
        """Восстанавливает фанфик из корзины"""
        self.status = 'draft'
        self.deleted_at = None
        self.purge_at = None
        self.save()
        return self
    
    # === Методы для архива ===
    def move_to_archive(self):
        """Перемещает фанфик в архив (просто хранение)"""
        self.status = 'archived'
        self.archived_at = timezone.now()
        self.deleted_at = None
        self.purge_at = None
        self.save()
        return self
    
    def restore_from_archive(self):
        """Восстанавливает фанфик из архива (в черновики)"""
        self.status = 'draft'
        self.archived_at = None
        self.save()
        return self
    
    def publish_from_archive(self):
        """Публикует фанфик из архива"""
        self.status = 'published'
        self.archived_at = None
        self.save()
        return self
    
    # === Методы для закладок ===
    def is_bookmarked_by(self, user):
        """Проверяет, добавлен ли фанфик в закладки пользователем"""
        if not user.is_authenticated:
            return False
        return self.bookmarked_by.filter(user=user).exists()
    
    def get_bookmarks_count(self):
        """Возвращает количество пользователей, добавивших фанфик в закладки"""
        return self.bookmarked_by.count()
    
    # === Методы для комментариев ===
    def get_comments_count(self):
        """Возвращает количество комментариев к фанфику"""
        return self.comments.filter(is_deleted=False).count()
    
    def get_active_comments(self):
        """Возвращает активные (не удаленные) комментарии"""
        return self.comments.filter(is_deleted=False)
    
    # === Вспомогательные методы ===
    @property
    def is_popular(self):
        """Проверяет, является ли фанфик популярным"""
        return self.views_count >= 100
    
    @property
    def is_trending(self):
        """Проверяет, набирает ли фанфик популярность"""
        if self.views_count < 50:
            return False
        
        time_since_creation = timezone.now() - self.created_at
        return time_since_creation.days <= 7
    
    @property
    def days_until_purge(self):
        """Сколько дней осталось до удаления из корзины"""
        if self.purge_at and self.status == 'deleted':
            delta = self.purge_at - timezone.now()
            days = delta.days + 1 if delta.seconds > 0 else delta.days
            return max(0, days)
        return None
    
    @property
    def should_be_purged(self):
        """Проверяет, нужно ли удалять фанфик из корзины"""
        if self.purge_at and self.status == 'deleted':
            return timezone.now() >= self.purge_at
        return False
    
    @property
    def time_in_archive(self):
        """Сколько дней фанфик находится в архиве"""
        if self.archived_at and self.status == 'archived':
            delta = timezone.now() - self.archived_at
            return delta.days
        return None
    
    def save(self, *args, **kwargs):
        # Автоматически устанавливаем даты при перемещении в корзину
        if self.status == 'deleted' and not self.deleted_at:
            self.deleted_at = timezone.now()
        
        if self.deleted_at and not self.purge_at:
            self.purge_at = self.deleted_at + timedelta(days=30)
        
        # Автоматически устанавливаем дату при перемещении в архив
        if self.status == 'archived' and not self.archived_at:
            self.archived_at = timezone.now()
        
        # Очищаем теги от лишних запятых
        if self.tags:
            tags_list = self.get_tags_list()
            self.tags = ', '.join(tags_list)
        
        super().save(*args, **kwargs)


# === МОДЕЛЬ: История просмотров ===
class ViewHistory(models.Model):
    """Модель для отслеживания истории просмотров пользователей"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    fanfic = models.ForeignKey(Fanfic, on_delete=models.CASCADE, verbose_name='Фанфик')
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата просмотра')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP адрес')
    
    class Meta:
        verbose_name = 'История просмотра'
        verbose_name_plural = 'История просмотров'
        ordering = ['-viewed_at']
        unique_together = ['user', 'fanfic']  # Один пользователь - одна запись на фанфик
        indexes = [
            models.Index(fields=['user', '-viewed_at']),
        ]
    
    def __str__(self):
        return f"{self.user} просмотрел {self.fanfic}"


# === МОДЕЛЬ: Закладки ===
class Bookmark(models.Model):
    """Модель для закладок пользователей"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Пользователь', 
                            related_name='bookmarks')
    fanfic = models.ForeignKey(Fanfic, on_delete=models.CASCADE, verbose_name='Фанфик',
                              related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    notes = models.TextField(blank=True, null=True, verbose_name='Заметки', 
                            help_text='Необязательные заметки к закладке')
    
    class Meta:
        verbose_name = 'Закладка'
        verbose_name_plural = 'Закладки'
        ordering = ['-created_at']
        unique_together = ['user', 'fanfic']  # Один пользователь не может дважды добавить один фанфик
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['fanfic']),
        ]
    
    def __str__(self):
        return f"{self.user.username} -> {self.fanfic.title}"
    
    def get_read_time_estimate(self):
        """Примерное время чтения фанфика (в минутах)"""
        word_count = len(self.fanfic.content.split())
        reading_speed = 200  # слов в минуту
        return max(1, word_count // reading_speed)


# === МОДЕЛЬ: Комментарии ===
class Comment(models.Model):
    """Модель для комментариев с древовидной структурой"""
    fanfic = models.ForeignKey(Fanfic, on_delete=models.CASCADE, verbose_name='Фанфик', 
                              related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              verbose_name='Родительский комментарий', related_name='replies')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Автор')
    content = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_deleted = models.BooleanField(default=False, verbose_name='Удален')
    edited_count = models.PositiveIntegerField(default=0, verbose_name='Количество редактирований')
    
    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['fanfic', 'parent']),
            models.Index(fields=['author']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        author_name = self.author.nickname or self.author.username
        fanfic_title = self.fanfic.title[:30] + "..." if len(self.fanfic.title) > 30 else self.fanfic.title
        return f'Комментарий от {author_name} к "{fanfic_title}"'
    
    def get_absolute_url(self):
        return reverse('fanfic_detail', kwargs={'pk': self.fanfic.pk}) + f'#comment-{self.pk}'
    
    @property
    def is_root(self):
        """Проверяет, является ли комментарий корневым (без родителя)"""
        return self.parent is None
    
    @property
    def has_replies(self):
        """Проверяет, есть ли ответы на комментарий"""
        return self.replies.filter(is_deleted=False).exists()
    
    @property
    def replies_count(self):
        """Возвращает количество ответов (без учета удаленных)"""
        return self.replies.filter(is_deleted=False).count()
    
    @property
    def is_edited(self):
        """Проверяет, редактировался ли комментарий"""
        return self.edited_count > 0 or self.created_at < self.updated_at
    
    @property
    def display_content(self):
        """Возвращает контент для отображения (с обработкой удаленных)"""
        if self.is_deleted:
            return "[Комментарий удален]"
        return self.content
    
    def get_all_replies(self, include_deleted=False):
        """Возвращает все ответы на комментарий (включая вложенные)"""
        replies = []
        
        def collect_replies(comment):
            queryset = comment.replies.all()
            if not include_deleted:
                queryset = queryset.filter(is_deleted=False)
                
            for reply in queryset:
                replies.append(reply)
                collect_replies(reply)
        
        collect_replies(self)
        return replies
    
    def get_reply_depth(self):
        """Возвращает глубину вложенности комментария"""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth
    
    def soft_delete(self):
        """Мягкое удаление комментария (скрытие)"""
        self.is_deleted = True
        self.content = "[Комментарий удален]"
        self.save(update_fields=['is_deleted', 'content'])
    
    def restore(self):
        """Восстановление удаленного комментария"""
        if self.is_deleted:
            self.is_deleted = False
            # Восстанавливаем исходный контент или оставляем стандартный
            if self.content == "[Комментарий удален]":
                self.content = "[Комментарий восстановлен]"
            self.save(update_fields=['is_deleted', 'content'])
    
    def can_edit(self, user):
        """Проверяет, может ли пользователь редактировать комментарий"""
        if not user.is_authenticated:
            return False
        return user == self.author or user.is_staff
    
    def can_delete(self, user):
        """Проверяет, может ли пользователь удалить комментарий"""
        if not user.is_authenticated:
            return False
        return user == self.author or user.is_staff or user == self.fanfic.author
    
    def can_reply(self, user):
        """Проверяет, можно ли ответить на комментарий"""
        if not user.is_authenticated:
            return False
        # Нельзя отвечать на удаленные комментарии
        if self.is_deleted:
            return False
        # Ограничение глубины вложенности (максимум 5 уровней)
        if self.get_reply_depth() >= 5:
            return False
        return True
    
    def edit_content(self, new_content, user):
        """Редактирование комментария с увеличением счетчика"""
        if not self.can_edit(user):
            return False
        
        self.content = new_content
        self.edited_count += 1
        self.save()
        return True
    
    @classmethod
    def get_comments_for_fanfic(cls, fanfic_id, include_deleted=False):
        """Возвращает все комментарии для фанфика в древовидной структуре"""
        queryset = cls.objects.filter(fanfic_id=fanfic_id)
        
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        comments = queryset.select_related('author').order_by('created_at')
        
        # Строим дерево комментариев
        def build_tree(parent_id=None, level=0):
            tree = []
            for comment in comments:
                if comment.parent_id == parent_id:
                    comment.temp_level = level
                    comment.temp_children = build_tree(comment.id, level + 1)
                    tree.append(comment)
            return tree
        
        return build_tree()
    
    @classmethod
    def get_user_comments(cls, user_id, include_deleted=False):
        """Возвращает все комментарии пользователя"""
        queryset = cls.objects.filter(author_id=user_id)
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        return queryset.order_by('-created_at')
    
    def save(self, *args, **kwargs):
        # Автоматически увеличиваем edited_count при редактировании
        if self.pk:
            original = Comment.objects.get(pk=self.pk)
            if original.content != self.content:
                self.edited_count += 1
        
        # Очищаем контент от лишних пробелов
        if self.content:
            self.content = self.content.strip()
        
        super().save(*args, **kwargs)


# === МОДЕЛЬ: Теги ===
class Tag(models.Model):
    """Модель для хранения всех уникальных тегов"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Название тега')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    usage_count = models.PositiveIntegerField(default=0, verbose_name='Количество использований')
    
    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)
    
    def get_fanfics_count(self):
        """Возвращает количество опубликованных фанфиков с этим тегом"""
        return Fanfic.objects.filter(
            status='published',
            tags__icontains=self.name
        ).count()
    
    def get_popular_fanfics(self, limit=10):
        """Возвращает популярные фанфики с этим тегом"""
        return Fanfic.objects.filter(
            status='published',
            tags__icontains=self.name
        ).order_by('-views_count', '-created_at')[:limit]
    
    @classmethod
    def update_all_tags(cls):
        """Обновляет базу тегов из всех фанфиков"""
        from collections import Counter
        
        # Собираем все уникальные теги из опубликованных фанфиков
        published_fanfics = Fanfic.objects.filter(status='published')
        all_tags = Counter()
        
        for fanfic in published_fanfics:
            tags = fanfic.get_tags_list()
            all_tags.update(tags)
        
        # Обновляем или создаем теги
        for tag_name, count in all_tags.items():
            if tag_name:
                tag, created = cls.objects.get_or_create(name=tag_name)
                if created:
                    tag.usage_count = count
                else:
                    tag.usage_count = count
                tag.save()
        
        return cls.objects.count()


# === МОДЕЛЬ: Предлагаемые теги (опционально) ===
class SuggestedTag(models.Model):
    """Модель для предлагаемых/популярных тегов"""
    CATEGORY_CHOICES = [
        ('genre', 'Жанр'),
        ('fandom', 'Фэндом'),
        ('theme', 'Тема'),
        ('relationship', 'Отношения'),
        ('character', 'Персонаж'),
        ('other', 'Другое'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name='Название тега')
    is_featured = models.BooleanField(default=False, verbose_name='Рекомендуемый тег')
    usage_count = models.PositiveIntegerField(default=0, verbose_name='Количество использований')
    category = models.CharField(
        max_length=50,
        blank=True,
        choices=CATEGORY_CHOICES,
        verbose_name='Категория'
    )
    
    class Meta:
        verbose_name = 'Предлагаемый тег'
        verbose_name_plural = 'Предлагаемые теги'
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)


# === МОДЕЛЬ: Лайки комментариев (опционально, если нужно) ===
class CommentLike(models.Model):
    """Модель для лайков комментариев"""
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='Комментарий',
                               related_name='likes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Лайк комментария'
        verbose_name_plural = 'Лайки комментариев'
        unique_together = ['comment', 'user']  # Один пользователь может лайкнуть комментарий только один раз
        indexes = [
            models.Index(fields=['comment', 'user']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user} лайкнул комментарий #{self.comment.id}" 