from django.contrib import admin
from .models import CustomUser, Fanfic
from django.utils import timezone

@admin.register(Fanfic)
class FanficAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'created_at', 'deleted_at', 'purge_at', 'days_left', 'should_purge')
    list_filter = ('status', 'author', 'created_at', 'deleted_at')
    search_fields = ('title', 'description', 'tags')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'purge_at', 'days_left_display')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'author', 'description', 'content', 'tags')
        }),
        ('Статус и даты', {
            'fields': ('status', 'created_at', 'updated_at', 'deleted_at', 'purge_at')
        }),
        ('Информация об удалении', {
            'fields': ('days_left_display', 'should_purge_display')
        }),
    )
    
    def days_left(self, obj):
        """Количество дней до удаления (для списка)"""
        return obj.days_until_purge
    days_left.short_description = 'Дней до удаления'
    
    def days_left_display(self, obj):
        """Количество дней до удаления (для детального просмотра)"""
        days = obj.days_until_purge
        if days is not None:
            if days == 0:
                return f"<span style='color: red; font-weight: bold;'>УДАЛИТЬ СЕГОДНЯ!</span>"
            elif days <= 7:
                return f"<span style='color: orange; font-weight: bold;'>{days} дней</span>"
            else:
                return f"{days} дней"
        return "Не в корзине"
    days_left_display.short_description = 'Дней до удаления'
    days_left_display.allow_tags = True
    
    def should_purge(self, obj):
        """Нужно ли удалять (для списка)"""
        return obj.should_be_purged
    should_purge.short_description = 'Удалить?'
    should_purge.boolean = True
    
    def should_purge_display(self, obj):
        """Нужно ли удалять (для детального просмотра)"""
        if obj.should_be_purged:
            return "<span style='color: red; font-weight: bold;'>ДА, нужно удалить!</span>"
        return "Нет, еще рано"
    should_purge_display.short_description = 'Нужно удалить?'
    should_purge_display.allow_tags = True
    
    # Действие для админки - принудительное удаление
    actions = ['purge_selected']
    
    def purge_selected(self, request, queryset):
        """Действие для удаления выбранных фанфиков"""
        deleted_count = 0
        for fanfic in queryset:
            if fanfic.status == 'deleted' and fanfic.should_be_purged:
                fanfic.delete()
                deleted_count += 1
        
        if deleted_count:
            self.message_user(request, f"Удалено {deleted_count} фанфиков")
        else:
            self.message_user(request, "Нет фанфиков для удаления")
    purge_selected.short_description = "Удалить выбранные (если срок истек)"

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'nickname', 'country', 'date_joined')
    list_filter = ('country', 'date_joined')
    search_fields = ('username', 'email', 'nickname')