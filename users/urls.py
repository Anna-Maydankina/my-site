from django.urls import path
from . import views

urlpatterns = [
    
    

    # Главная страница
    path('', views.index_view, name='index'),
    
    # Расширенный поиск
    path('search/', views.advanced_search_view, name='advanced_search'),
    
    # Аутентификация
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Профиль
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    
    # Фанфики
    path('fanfic/new/', views.fanfic_create_view, name='fanfic_create'),
    path('fanfic/<int:pk>/edit/', views.fanfic_edit_view, name='fanfic_edit'),
    path('fanfic/<int:pk>/', views.fanfic_detail_view, name='fanfic_detail'),
    
    # ===== КОММЕНТАРИИ =====
    path('fanfic/<int:fanfic_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/restore/', views.restore_comment, name='restore_comment'),
    path('fanfic/<int:fanfic_id>/comments/json/', views.get_comments_json, name='get_comments_json'),
    path('my-comments/', views.my_comments_view, name='my_comments'),
    
    # Система тегов (простая)
    path('tags/', views.all_tags_view, name='all_tags'),
    path('tags/search/', views.search_by_tags_view, name='tag_search'),
    path('tags/<str:tag_slug>/', views.tag_detail_view, name='tag_detail'),
    
    # Архив
    path('fanfic/<int:fanfic_id>/archive/', views.archive_fanfic_view, name='archive_fanfic'),
    path('fanfic/<int:fanfic_id>/restore-archive/', views.restore_from_archive_view, name='restore_from_archive'),
    path('fanfic/<int:fanfic_id>/publish-archive/', views.publish_from_archive_view, name='publish_from_archive'),
    
    # Корзина
    path('fanfic/<int:fanfic_id>/trash/', views.move_to_trash_view, name='move_to_trash'),
    path('fanfic/<int:fanfic_id>/restore/', views.restore_from_trash_view, name='restore_from_trash'),
    path('fanfic/<int:fanfic_id>/delete/', views.delete_permanently_view, name='delete_permanently'),
    path('trash/empty/', views.empty_trash_view, name='empty_trash'),
    
    # Смена статуса
    path('fanfic/<int:fanfic_id>/publish/', views.publish_fanfic_view, name='publish_fanfic'),
    
    # Публичные страницы
    path('new/', views.new_fanfics_view, name='new_fanfics'),
    path('popular/', views.popular_fanfics_view, name='popular_fanfics'),
    
    # История просмотров
    path('history/', views.view_history_view, name='view_history'),
    path('history/clear/', views.clear_view_history_view, name='clear_view_history'),
    
    # Универсальная смена статуса
    path('fanfic/<int:fanfic_id>/status/<str:new_status>/', views.change_status_view, name='change_status'),
    
    # Просмотр фанфиков пользователя
    path('user/<str:username>/', views.user_fanfics_view, name='user_fanfics'),
    
    # Закладки
    path('bookmarks/', views.my_bookmarks, name='my_bookmarks'),
    path('bookmarks/toggle/<int:fanfic_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('bookmarks/clear/', views.clear_bookmarks, name='clear_bookmarks'),
    path('bookmarks/remove/<int:bookmark_id>/', views.remove_bookmark, name='remove_bookmark'),
    
    # Обработчики ошибок
    path('404/', views.custom_404_view, name='custom_404'),
    path('500/', views.custom_500_view, name='custom_500'),
]

# Обработчики ошибок для всего проекта
handler404 = 'users.views.custom_404_view'
handler500 = 'users.views.custom_500_view'