from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

# Импортируем views из users (где у вас все функции)
from users.views import index_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ВАЖНО: Главная страница должна вести на index_view, а не на TemplateView
    path('', index_view, name='index'),  # ← ИЗМЕНИТЬ ЭТУ СТРОКУ!
    
    path('users/', include('users.urls')),
]