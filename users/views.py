from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, F
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.db import transaction

from .forms import RegistrationForm, LoginForm, ProfileEditForm, FanficForm, CommentForm
from .models import Fanfic, CustomUser, ViewHistory, Tag, Bookmark, Comment

# ===== АУТЕНТИФИКАЦИЯ =====
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать!')
            return redirect('profile')
    else:
        form = RegistrationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                return redirect('profile')
            else:
                form.add_error(None, 'Неверное имя пользователя или пароль')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('login')
# ===== ГЛАВНАЯ =====
def index_view(request):
    """Главная страница - рекомендации по тегам из последнего фанфика"""
    
    print("=" * 80)
    print("🚀 index_view ВЫЗВАНА")
    print("=" * 80)
    
    # 1. ПОПУЛЯРНЫЕ
    popular_fanfics = Fanfic.objects.filter(
        status='published'
    ).order_by('-views_count', '-created_at')[:10]
    
    print(f"🔥 ПОПУЛЯРНЫЕ: {popular_fanfics.count()} фанфиков")
    
    # 2. НОВИНКИ
    new_fanfics = Fanfic.objects.filter(
        status='published'
    ).order_by('-created_at')[:10]
    
    print(f"✨ НОВИНКИ: {new_fanfics.count()} фанфиков")
    
    # 3. РЕКОМЕНДАЦИИ ПО ТЕГАМ ИЗ ПОСЛЕДНЕГО ФАНФИКА
    print(f"\n🎯 ФОРМИРУЕМ РЕКОМЕНДАЦИИ ИЗ ПОСЛЕДНЕГО ФАНФИКА:")
    
    if request.user.is_authenticated:
        # Получаем ТОЛЬКО последний просмотренный фанфик
        last_view = ViewHistory.objects.filter(
            user=request.user
        ).select_related('fanfic').order_by('-viewed_at').first()
        
        if last_view:
            print(f"   Последний фанфик: '{last_view.fanfic.title}'")
            
            # Берем теги только из этого фанфика
            if last_view.fanfic.tags:
                tags = last_view.fanfic.get_tags_list()
                clean_tags = [tag.strip() for tag in tags if tag.strip()]
                
                print(f"   Теги последнего фанфика: {clean_tags}")
                
                if clean_tags:
                    # Ищем фанфики по тегам последнего фанфика
                    recommended_fanfics = get_recommendations_from_last_fanfic(
                        tags=clean_tags,
                        exclude_fanfic_id=last_view.fanfic.id,
                        limit=10
                    )
                    print(f"   Найдено рекомендаций: {recommended_fanfics.count()}")
                else:
                    recommended_fanfics = Fanfic.objects.none()
                    print("   Нет тегов в последнем фанфике - пустые рекомендации")
            else:
                recommended_fanfics = Fanfic.objects.none()
                print("   Нет тегов в последнем фанфике - пустые рекомендации")
        else:
            recommended_fanfics = Fanfic.objects.none()
            print("   Нет истории просмотров - пустые рекомендации")
    else:
        recommended_fanfics = Fanfic.objects.none()
        print("   Пользователь не авторизован - пустые рекомендации")
    
    print("=" * 80)
    
    context = {
        'popular_fanfics': popular_fanfics,
        'new_fanfics': new_fanfics,
        'recommended_fanfics': recommended_fanfics,
    }
    
    return render(request, 'index.html', context)


def get_recommendations_from_last_fanfic(tags, exclude_fanfic_id, limit=10):
    """Получить рекомендации по тегам из последнего фанфика"""
    
    if not tags:
        return Fanfic.objects.none()
    
    print(f"\n   Поиск рекомендаций по тегам последнего фанфика:")
    print(f"   Теги: {tags}")
    print(f"   Исключаем фанфик ID: {exclude_fanfic_id}")
    
    recommended_ids = set()
    result_fanfics = []
    
    # Если несколько тегов, сначала ищем фанфики со ВСЕМИ тегами
    if len(tags) > 1:
        print(f"   Пробуем найти фанфики со всеми тегами...")
        
        combined_query = Fanfic.objects.filter(status='published')
        
        for tag in tags:
            combined_query = combined_query.filter(tags__icontains=tag)
        
        combined_fanfics = combined_query.exclude(
            id=exclude_fanfic_id
        ).order_by(
            '-views_count', '-created_at'
        )[:limit]
        
        found_combined = combined_fanfics.count()
        print(f"   Найдено со всеми тегами: {found_combined}")
        
        if found_combined > 0:
            for fanfic in combined_fanfics:
                result_fanfics.append(fanfic)
                recommended_ids.add(fanfic.id)
    
    # Добираем по отдельным тегам
    if len(result_fanfics) < limit:
        print(f"   Добираем по отдельным тегам...")
        
        for tag in tags:
            if len(result_fanfics) >= limit:
                break
                
            print(f"   Ищем по тегу: '{tag}'")
            
            tag_fanfics = Fanfic.objects.filter(
                status='published',
                tags__icontains=tag
            ).exclude(
                id=exclude_fanfic_id
            ).exclude(
                id__in=recommended_ids
            ).order_by(
                '-views_count', '-created_at'
            )[:limit - len(result_fanfics)]
            
            found_count = tag_fanfics.count()
            print(f"   Найдено по тегу '{tag}': {found_count} фанфиков")
            
            if found_count > 0:
                for fanfic in tag_fanfics:
                    if fanfic.id not in recommended_ids:
                        result_fanfics.append(fanfic)
                        recommended_ids.add(fanfic.id)
                        
                        if len(result_fanfics) >= limit:
                            break
    
    print(f"   Всего собрано: {len(result_fanfics)} фанфиков")
    
    # Возвращаем QuerySet
    if result_fanfics:
        fanfic_ids = [f.id for f in result_fanfics]
        return Fanfic.objects.filter(id__in=fanfic_ids).order_by('-views_count', '-created_at')
    else:
        return Fanfic.objects.none()
# ===== ПОИСК =====
def advanced_search_view(request):
    """Расширенный поиск"""
    title_query = request.GET.get('title', '').strip()
    tag_query = request.GET.get('tag', '').strip()
    author_query = request.GET.get('author', '').strip()
    page = request.GET.get('page', 1)
    
    # Базовый запрос
    fanfics = Fanfic.objects.filter(status='published').select_related('author').order_by('-created_at')
    
    has_search = False
    
    # Поиск по названию
    if title_query:
        has_search = True
        fanfics = fanfics.filter(title__icontains=title_query)
    
    # Поиск по тегам
    if tag_query:
        has_search = True
        tag_terms = [tag.strip().lower() for tag in tag_query.split(',') if tag.strip()]
        tag_q = Q()
        
        for term in tag_terms:
            tag_q &= Q(tags__icontains=term)
        
        fanfics = fanfics.filter(tag_q)
    
    # Поиск по автору
    if author_query:
        has_search = True
        fanfics = fanfics.filter(
            Q(author__username__icontains=author_query) |
            Q(author__nickname__icontains=author_query)
        )
    
    # Пагинация
    paginator = Paginator(fanfics, 12)
    try:
        fanfics_page = paginator.page(page)
    except PageNotAnInteger:
        fanfics_page = paginator.page(1)
    except EmptyPage:
        fanfics_page = paginator.page(paginator.num_pages)
    
    context = {
        'fanfics': fanfics_page,
        'title_query': title_query,
        'tag_query': tag_query,
        'author_query': author_query,
        'has_search': has_search,
        'total_results': fanfics.count(),
    }
    
    return render(request, 'users/search_results.html', context)

# ===== ПРОФИЛЬ =====
@login_required
def profile_view(request):
    published_fanfics = Fanfic.objects.filter(
        author=request.user, 
        status='published'
    ).order_by('-created_at')
    
    draft_fanfics = Fanfic.objects.filter(
        author=request.user, 
        status='draft'
    ).order_by('-created_at')
    
    archived_fanfics = Fanfic.objects.filter(
        author=request.user, 
        status='archived'
    ).order_by('-archived_at')
    
    deleted_fanfics = Fanfic.objects.filter(
        author=request.user,
        status='deleted'
    ).order_by('-deleted_at')
    
    # Количество закладок пользователя
    bookmarks_count = Bookmark.objects.filter(user=request.user).count()
    
    # Количество комментариев пользователя
    comments_count = Comment.objects.filter(author=request.user, is_deleted=False).count()
    
    context = {
        'user': request.user,
        'published_fanfics': published_fanfics,
        'draft_fanfics': draft_fanfics,
        'archived_fanfics': archived_fanfics,
        'deleted_fanfics': deleted_fanfics,
        'bookmarks_count': bookmarks_count,
        'comments_count': comments_count,
    }
    return render(request, 'users/profile.html', context)

@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'users/profile_edit.html', {'form': form})

# ===== ФАНФИКИ =====
@login_required
def fanfic_create_view(request):
    if request.method == 'POST':
        form = FanficForm(request.POST)
        if form.is_valid():
            fanfic = form.save(commit=False)
            fanfic.author = request.user
            fanfic.save()
            messages.success(request, 'Фанфик успешно создан!')
            return redirect('fanfic_detail', pk=fanfic.pk)
    else:
        form = FanficForm()
    return render(request, 'users/fanfic_editor.html', {'form': form})

@login_required
def fanfic_edit_view(request, pk):
    fanfic = get_object_or_404(Fanfic, pk=pk, author=request.user)
    
    if request.method == 'POST':
        form = FanficForm(request.POST, instance=fanfic)
        if form.is_valid():
            form.save()
            messages.success(request, 'Фанфик успешно обновлен!')
            return redirect('fanfic_detail', pk=fanfic.pk)
    else:
        form = FanficForm(instance=fanfic)
    return render(request, 'users/fanfic_editor.html', {'form': form})

def fanfic_detail_view(request, pk):
    """Детальная страница фанфика"""
    fanfic = get_object_or_404(Fanfic, pk=pk)
    
    # Проверяем, что фанфик опубликован или пользователь - автор
    if fanfic.status != 'published' and request.user != fanfic.author:
        messages.error(request, 'Этот фанфик не доступен для просмотра.')
        return redirect('index')
    
    # Проверяем, в закладках ли фанфик
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(user=request.user, fanfic=fanfic).exists()
    
    # Увеличиваем счетчик просмотров
    fanfic.increment_views(request.user if request.user.is_authenticated else None)
    
    # Получаем комментарии в древовидной структуре
    comments = Comment.get_comments_for_fanfic(fanfic.id)
    
    # Форма для нового комментария
    comment_form = CommentForm()
    
    # Похожие фанфики
    similar_fanfics = Fanfic.objects.filter(
        status='published'
    ).exclude(
        pk=fanfic.pk
    ).order_by('-views_count')[:5]
    
    context = {
        'fanfic': fanfic,
        'similar_fanfics': similar_fanfics,
        'is_bookmarked': is_bookmarked,
        'comments': comments,
        'comment_form': comment_form,
        'comments_count': fanfic.get_comments_count(),
    }
    
    # Для AJAX запросов возвращаем только комментарии
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        comments_html = render(request, 'fanfic/comments_list.html', {'comments': comments}).content
        return JsonResponse({'comments_html': comments_html.decode('utf-8')})
    
    return render(request, 'users/fanfic_detail.html', context)

# ===== КОММЕНТАРИИ =====
@login_required
@require_POST
def add_comment(request, fanfic_id):
    """Добавление нового комментария"""
    fanfic = get_object_or_404(Fanfic, id=fanfic_id)
    
    # Проверяем, что фанфик опубликован
    if fanfic.status != 'published':
        return JsonResponse({
            'success': False,
            'error': 'Нельзя комментировать неопубликованные фанфики'
        })
    
    form = CommentForm(request.POST)
    
    if form.is_valid():
        with transaction.atomic():
            comment = form.save(commit=False)
            comment.fanfic = fanfic
            comment.author = request.user
            
            # Проверяем parent_id
            parent_id = form.cleaned_data.get('parent_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id, fanfic=fanfic)
                    # Проверяем глубину вложенности
                    if parent_comment.get_reply_depth() >= 5:
                        return JsonResponse({
                            'success': False,
                            'error': 'Превышена максимальная глубина вложенности комментариев'
                        })
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Родительский комментарий не найден'
                    })
            
            comment.save()
        
        # Возвращаем данные для AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'comment_id': comment.id,
                'author': comment.author.username,
                'author_nickname': comment.author.nickname or comment.author.username,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
                'parent_id': comment.parent_id,
                'replies_count': 0,
                'is_root': comment.is_root,
            })
        
        messages.success(request, 'Комментарий добавлен!')
        return redirect('fanfic_detail', pk=fanfic_id)
    
    return JsonResponse({
        'success': False,
        'errors': form.errors.as_json()
    })

@login_required
@require_POST
def delete_comment(request, comment_id):
    """Удаление комментария"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if not comment.can_delete(request.user):
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав на удаление этого комментария'
        })
    
    comment.soft_delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Комментарий удален')
    return redirect('fanfic_detail', pk=comment.fanfic.id)

@login_required
@require_POST
def edit_comment(request, comment_id):
    """Редактирование комментария"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if not comment.can_edit(request.user):
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав на редактирование этого комментария'
        })
    
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({
            'success': False,
            'error': 'Комментарий не может быть пустым'
        })
    
    if len(content) > 5000:
        return JsonResponse({
            'success': False,
            'error': 'Комментарий слишком длинный (максимум 5000 символов)'
        })
    
    comment.edit_content(content, request.user)
    
    return JsonResponse({
        'success': True,
        'content': comment.content,
        'updated_at': comment.updated_at.strftime('%d.%m.%Y %H:%M'),
        'edited_count': comment.edited_count,
    })

@login_required
def get_comments_json(request, fanfic_id):
    """Получение комментариев в формате JSON"""
    fanfic = get_object_or_404(Fanfic, id=fanfic_id)
    comments = Comment.get_comments_for_fanfic(fanfic.id)
    
    def serialize_comment(comment):
        return {
            'id': comment.id,
            'author': {
                'username': comment.author.username,
                'nickname': comment.author.nickname,
            },
            'content': comment.display_content,
            'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
            'updated_at': comment.updated_at.strftime('%d.%m.%Y %H:%M'),
            'is_edited': comment.is_edited,
            'edited_count': comment.edited_count,
            'parent_id': comment.parent_id,
            'replies': [serialize_comment(reply) for reply in comment.replies.filter(is_deleted=False)],
            'replies_count': comment.replies_count,
            'can_edit': comment.can_edit(request.user) if request.user.is_authenticated else False,
            'can_delete': comment.can_delete(request.user) if request.user.is_authenticated else False,
        }
    
    serialized_comments = [serialize_comment(comment) for comment in comments]
    
    return JsonResponse({
        'comments': serialized_comments,
        'total': len(serialized_comments),
    })

@login_required
def restore_comment(request, comment_id):
    """Восстановление удаленного комментария"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if not comment.can_delete(request.user):
        messages.error(request, 'У вас нет прав на восстановление этого комментария')
        return redirect('fanfic_detail', pk=comment.fanfic.id)
    
    if not comment.is_deleted:
        messages.warning(request, 'Комментарий не был удален')
    else:
        comment.restore()
        messages.success(request, 'Комментарий восстановлен')
    
    return redirect('fanfic_detail', pk=comment.fanfic.id)

# ===== ТЕГИ =====
def all_tags_view(request):
    """Все теги"""
    published_fanfics = Fanfic.objects.filter(status='published')
    
    # Собираем теги
    all_tags = {}
    for fanfic in published_fanfics:
        tags = fanfic.get_tags_list()
        for tag in tags:
            tag = tag.strip()
            if tag:
                if tag in all_tags:
                    all_tags[tag] += 1
                else:
                    all_tags[tag] = 1
    
    # Сортируем
    tags_list = []
    for tag_name, count in sorted(all_tags.items()):
        slug = tag_name.lower().replace(' ', '-')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        tags_list.append({
            'name': tag_name,
            'count': count,
            'slug': slug
        })
    
    context = {
        'tags_list': tags_list,
        'total_tags': len(all_tags),
        'total_fanfics': published_fanfics.count(),
    }
    
    return render(request, 'users/all_tags.html', context)

def tag_detail_view(request, tag_slug):
    """Фанфики по тегу"""
    if not tag_slug:
        return redirect('all_tags')
    
    tag_name = tag_slug.replace('-', ' ')
    
    fanfics = Fanfic.objects.filter(
        status='published',
        tags__icontains=tag_name
    ).select_related('author').order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(fanfics, 12)
    page = request.GET.get('page')
    
    try:
        fanfics_page = paginator.page(page)
    except PageNotAnInteger:
        fanfics_page = paginator.page(1)
    except EmptyPage:
        fanfics_page = paginator.page(paginator.num_pages)
    
    context = {
        'tag_name': tag_name,
        'tag_slug': tag_slug,
        'fanfics': fanfics_page,
        'fanfics_count': fanfics.count(),
        'page_obj': fanfics_page,
    }
    
    return render(request, 'users/tag_detail.html', context)

def search_by_tags_view(request):
    """Поиск по тегам"""
    query = request.GET.get('q', '').strip()
    
    if query:
        search_tags = [tag.strip().lower() for tag in query.split(',') if tag.strip()]
        
        if search_tags:
            # Ищем фанфики, содержащие все указанные теги
            fanfics = Fanfic.objects.filter(status='published')
            
            for tag in search_tags:
                fanfics = fanfics.filter(tags__icontains=tag)
            
            fanfics = fanfics.select_related('author').order_by('-created_at')
            
            context = {
                'query': query,
                'tags_list': search_tags,
                'fanfics': fanfics,
                'fanfics_count': fanfics.count(),
            }
            
            return render(request, 'users/tag_search.html', context)
    
    return render(request, 'users/tag_search.html', {})

# ===== ЗАКЛАДКИ =====
@login_required
def toggle_bookmark(request, fanfic_id):
    """Добавить/удалить фанфик из закладок"""
    fanfic = get_object_or_404(Fanfic, pk=fanfic_id, status='published')
    
    # Проверяем, есть ли уже закладка
    bookmark = Bookmark.objects.filter(user=request.user, fanfic=fanfic).first()
    
    if bookmark:
        # Удаляем закладку
        bookmark.delete()
        messages.success(request, f'Фанфик "{fanfic.title}" удален из закладок')
        is_bookmarked = False
    else:
        # Добавляем закладку
        Bookmark.objects.create(user=request.user, fanfic=fanfic)
        messages.success(request, f'Фанфик "{fanfic.title}" добавлен в закладки')
        is_bookmarked = True
    
    # Если это AJAX запрос (без перезагрузки)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'is_bookmarked': is_bookmarked,
            'fanfic_id': fanfic_id,
            'bookmarks_count': request.user.bookmarks.count()
        })
    
    # Обычный запрос - возвращаем на страницу фанфика
    return redirect('fanfic_detail', pk=fanfic_id)

@login_required
def my_bookmarks(request):
    """Страница с закладками пользователя"""
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('fanfic').order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(bookmarks, 10)
    page = request.GET.get('page')
    
    try:
        bookmarks_page = paginator.page(page)
    except PageNotAnInteger:
        bookmarks_page = paginator.page(1)
    except EmptyPage:
        bookmarks_page = paginator.page(paginator.num_pages)
    
    context = {
        'bookmarks': bookmarks_page,
        'total_bookmarks': bookmarks.count(),
        'page_obj': bookmarks_page,
    }
    
    return render(request, 'users/bookmarks.html', context)

@login_required
def clear_bookmarks(request):
    """Очистить все закладки"""
    if request.method == 'POST':
        count = request.user.bookmarks.count()
        request.user.bookmarks.all().delete()
        messages.success(request, f'Очищено {count} закладок')
        return redirect('my_bookmarks')
    
    # GET запрос - показываем подтверждение
    return render(request, 'users/confirm_clear_bookmarks.html', {
        'bookmarks_count': request.user.bookmarks.count()
    })

@login_required
def remove_bookmark(request, bookmark_id):
    """Удалить конкретную закладку"""
    bookmark = get_object_or_404(Bookmark, pk=bookmark_id, user=request.user)
    fanfic_title = bookmark.fanfic.title
    bookmark.delete()
    messages.success(request, f'Фанфик "{fanfic_title}" удален из закладок')
    
    return redirect('my_bookmarks')

# ===== АРХИВ =====
@login_required
def archive_fanfic_view(request, fanfic_id):
    fanfic = get_object_or_404(Fanfic, pk=fanfic_id, author=request.user)
    
    if fanfic.status == 'archived':
        messages.warning(request, f'Фанфик "{fanfic.title}" уже в архиве')
    else:
        fanfic.move_to_archive()
        messages.success(request, f'Фанфик "{fanfic.title}" перемещен в архив')
    
    return redirect('profile')

@login_required
def restore_from_archive_view(request, fanfic_id):
    fanfic = get_object_or_404(Fanfic, pk=fanfic_id, author=request.user, status='archived')
    
    fanfic.restore_from_archive()
    messages.success(request, f'Фанфик "{fanfic.title}" восстановлен из архива')
    
    return redirect('profile')

@login_required
def publish_from_archive_view(request, fanfic_id):
    fanfic = get_object_or_404(Fanfic, pk=fanfic_id, author=request.user, status='archived')
    
    fanfic.publish_from_archive()
    messages.success(request, f'Фанфик "{fanfic.title}" опубликован из архива')
    
    return redirect('fanfic_detail', pk=fanfic_id)

# ===== КОРЗИНА =====
@login_required
def move_to_trash_view(request, fanfic_id):
    fanfic = get_object_or_404(Fanfic, pk=fanfic_id, author=request.user)
    
    if fanfic.status == 'deleted':
        messages.warning(request, f'Фанфик "{fanfic.title}" уже в корзине')
    else:
        fanfic.move_to_trash()
        messages.success(request, f'Фанфик "{fanfic.title}" перемещен в корзину')
    
    return redirect('profile')

@login_required
def restore_from_trash_view(request, fanfic_id):
    fanfic = get_object_or_404(Fanfic, pk=fanfic_id, author=request.user, status='deleted')
    
    fanfic.restore_from_trash()
    messages.success(request, f'Фанфик "{fanfic.title}" восстановлен из корзины')
    
    return redirect('profile')

@login_required
def delete_permanently_view(request, fanfic_id):
    fanfic = get_object_or_404(Fanfic, pk=fanfic_id, author=request.user, status='deleted')
    
    title = fanfic.title
    fanfic.delete()
    messages.success(request, f'Фанфик "{title}" удален навсегда')
    
    return redirect('profile')

@login_required
def empty_trash_view(request):
    deleted_fanfics = Fanfic.objects.filter(author=request.user, status='deleted')
    count = deleted_fanfics.count()
    
    if count == 0:
        messages.info(request, 'Корзина уже пуста')
    else:
        deleted_fanfics.delete()
        messages.success(request, f'Корзина очищена. Удалено {count} фанфиков')
    
    return redirect('profile')

# ===== ПУБЛИКАЦИЯ =====
@login_required
def publish_fanfic_view(request, fanfic_id):
    fanfic = get_object_or_404(Fanfic, pk=fanfic_id, author=request.user)
    
    if fanfic.status == 'published':
        messages.warning(request, f'Фанфик "{fanfic.title}" уже опубликован')
    else:
        fanfic.status = 'published'
        fanfic.save()
        messages.success(request, f'Фанфик "{fanfic.title}" опубликован')
    
    return redirect('fanfic_detail', pk=fanfic_id)

# ===== ПУБЛИЧНЫЕ СТРАНИЦЫ =====
def new_fanfics_view(request):
    """Новые фанфики"""
    last_month = timezone.now() - timedelta(days=30)
    
    new_fanfics = Fanfic.objects.filter(
        status='published',  
        created_at__gte=last_month
    ).select_related('author').order_by('-created_at')
    
    # Если нет фанфиков за последний месяц, показываем просто последние опубликованные
    if not new_fanfics.exists():
        new_fanfics = Fanfic.objects.filter(
            status='published'
        ).select_related('author').order_by('-created_at')
        subtitle = "Последние опубликованные фанфики"
    else:
        subtitle = "Фанфики, добавленные за последние 30 дней"
    
    # Пагинация
    paginator = Paginator(new_fanfics, 12)
    page = request.GET.get('page')
    
    try:
        new_fanfics_page = paginator.page(page)  # ★★★ ИСПРАВЛЕНО: было fanfics_page, теперь new_fanfics_page ★★★
    except PageNotAnInteger:
        new_fanfics_page = paginator.page(1)
    except EmptyPage:
        new_fanfics_page = paginator.page(paginator.num_pages)
    
    context = {
        'new_fanfics': new_fanfics_page,  # ★★★ ИСПРАВЛЕНО: ключ должен быть 'new_fanfics', а не 'fanfics' ★★★
        'title': 'Новые истории',
        'subtitle': subtitle,
        'page_obj': new_fanfics_page,
    }
    
    return render(request, 'users/new_fanfics.html', context)

def popular_fanfics_view(request):
    """Популярные фанфики (топ-50 по просмотрам)"""
    # Получаем 50 самых популярных фанфиков
    popular_fanfics = Fanfic.objects.filter(
        status='published'
    ).order_by('-views_count', '-created_at')[:50]
    
    # Пагинация: 12 фанфиков на странице
    paginator = Paginator(popular_fanfics, 12)
    page = request.GET.get('page')
    
    try:
        fanfics_page = paginator.page(page)
    except PageNotAnInteger:
        fanfics_page = paginator.page(1)
    except EmptyPage:
        fanfics_page = paginator.page(paginator.num_pages)
    
    # Статистика
    total_views = sum(fanfic.views_count for fanfic in popular_fanfics)
    avg_views = total_views // len(popular_fanfics) if popular_fanfics else 0
    
    context = {
        'fanfics': fanfics_page,
        'title': '🔥 Самые популярные истории',
        'subtitle': 'Топ-50 фанфиков по количеству просмотров',
        'total_fanfics': len(popular_fanfics),
        'total_views': total_views,
        'avg_views': avg_views,
        'page_obj': fanfics_page,
    }
    
    return render(request, 'users/popular_fanfics.html', context)

# ===== ИСТОРИЯ ПРОСМОТРОВ =====
@login_required
def view_history_view(request):
    """История просмотров пользователя"""
    history = ViewHistory.objects.filter(
        user=request.user
    ).select_related('fanfic', 'fanfic__author').order_by('-viewed_at')[:50]
    
    context = {
        'history': history,
    }
    
    return render(request, 'users/view_history.html', context)

@login_required
def clear_view_history_view(request):
    """Очистка истории просмотров"""
    ViewHistory.objects.filter(user=request.user).delete()
    messages.success(request, 'История просмотров очищена')
    return redirect('view_history')

# ===== УПРАВЛЕНИЕ СТАТУСОМ =====
@login_required
def change_status_view(request, fanfic_id, new_status):
    """Универсальная функция для изменения статуса"""
    allowed_statuses = ['draft', 'published', 'archived']
    
    if new_status not in allowed_statuses:
        messages.error(request, 'Недопустимый статус')
        return redirect('profile')
    
    fanfic = get_object_or_404(Fanfic, pk=fanfic_id, author=request.user)
    
    if fanfic.status == new_status:
        messages.warning(request, f'Фанфик "{fanfic.title}" уже имеет статус "{new_status}"')
    else:
        fanfic.status = new_status
        
        # Автоматически устанавливаем даты
        if new_status == 'archived':
            fanfic.archived_at = timezone.now()
            fanfic.deleted_at = None
            fanfic.purge_at = None
        elif new_status == 'deleted':
            fanfic.deleted_at = timezone.now()
            fanfic.purge_at = timezone.now() + timedelta(days=30)
            fanfic.archived_at = None
        elif new_status == 'published':
            fanfic.archived_at = None
            fanfic.deleted_at = None
            fanfic.purge_at = None
        
        fanfic.save()
        
        status_names = {
            'draft': 'черновик',
            'published': 'опубликован',
            'archived': 'архивирован'
        }
        
        messages.success(request, f'Фанфик "{fanfic.title}" перемещен в {status_names.get(new_status, new_status)}')
    
    return redirect('profile')

# ===== ПРОСМОТР ЧУЖИХ ФАНФИКОВ =====
def user_fanfics_view(request, username):
    """Фанфики конкретного пользователя"""
    user = get_object_or_404(CustomUser, username=username)
    
    published_fanfics = Fanfic.objects.filter(
        author=user, 
        status='published'
    ).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(published_fanfics, 12)
    page = request.GET.get('page')
    
    try:
        fanfics_page = paginator.page(page)
    except PageNotAnInteger:
        fanfics_page = paginator.page(1)
    except EmptyPage:
        fanfics_page = paginator.page(paginator.num_pages)
    
    context = {
        'profile_user': user,
        'fanfics': fanfics_page,
        'page_obj': fanfics_page,
    }
    
    return render(request, 'users/user_fanfics.html', context)

# ===== МОИ КОММЕНТАРИИ =====
@login_required
def my_comments_view(request):
    """Страница с комментариями пользователя"""
    comments = Comment.objects.filter(
        author=request.user, 
        is_deleted=False
    ).select_related('fanfic').order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(comments, 20)
    page = request.GET.get('page')
    
    try:
        comments_page = paginator.page(page)
    except PageNotAnInteger:
        comments_page = paginator.page(1)
    except EmptyPage:
        comments_page = paginator.page(paginator.num_pages)
    
    context = {
        'comments': comments_page,
        'total_comments': comments.count(),
        'page_obj': comments_page,
    }
    
    return render(request, 'users/my_comments.html', context)

# ===== СТРАНИЦА ОШИБКИ 404 =====
def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

# ===== СТРАНИЦА ОШИБКИ 500 =====
def custom_500_view(request):
    return render(request, '500.html', status=500)

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def get_latest_comments(request, limit=10):
    """Получить последние комментарии (для боковой панели)"""
    comments = Comment.objects.filter(
        is_deleted=False
    ).select_related('author', 'fanfic').order_by('-created_at')[:limit]
    
    return {
        'latest_comments': comments
    }

def get_most_commented_fanfics(request, limit=5):
    """Получить самые комментируемые фанфики"""
    fanfics = Fanfic.objects.filter(
        status='published'
    ).annotate(
        comments_count=F('comments__id')
    ).order_by('-comments_count', '-created_at')[:limit]
    
    return {
        'most_commented_fanfics': fanfics
    }