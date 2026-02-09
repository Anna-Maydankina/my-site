from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import re
from .models import CustomUser, Fanfic, Comment
from .countries import COUNTRIES 

class RegistrationForm(UserCreationForm):
    nickname = forms.CharField(
        max_length=50, 
        required=True,
        label='Никнейм',
        help_text='Ваше отображаемое имя на сайте',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        label='Email',
        help_text='Введите действующий email адрес',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    country = forms.ChoiceField(
        choices=COUNTRIES,
        required=True,
        label='Страна',
        help_text='Выберите вашу страну проживания',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # === ДОБАВЛЕНО ПОЛЕ ТЕЛЕФОНА ===
    phone = forms.CharField(
        max_length=17,
        required=False,
        label='Номер телефона',
        help_text='Необязательно. Формат: +79991234567',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+79991234567'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'nickname', 'email', 'country', 'phone', 'password1', 'password2']
        error_messages = {
            'username': {
                'required': 'Обязательное поле.',
                'max_length': 'Не более 150 символов.',
                'invalid': 'Только буквы, цифры и @/./+/-/_.',
                'unique': 'Пользователь с таким именем уже существует.',
            },
            'email': {
                'required': 'Обязательное поле.',
                'invalid': 'Введите корректный email адрес.',
                'unique': 'Пользователь с таким email уже существует.',
            },
            'nickname': {
                'required': 'Обязательное поле.',
            }
        }
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username or username.strip() == '':
            raise ValidationError('Имя пользователя не может быть пустым')
        if len(username) < 3:
            raise ValidationError('Имя пользователя должно содержать минимум 3 символа')
        if get_user_model().objects.filter(username=username).exists():
            raise ValidationError('Пользователь с таким именем уже существует')
        return username.strip()
    
    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if not nickname or nickname.strip() == '':
            raise ValidationError('Никнейм не может быть пустым')
        if len(nickname) < 2:
            raise ValidationError('Никнейм должен содержать минимум 2 символа')
        return nickname.strip()
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email or email.strip() == '':
            raise ValidationError('Email не может быть пустым')
        if get_user_model().objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email.strip()
    
    def clean_country(self):
        country = self.cleaned_data.get('country')
        if not country:
            raise ValidationError('Пожалуйста, выберите страну')
        return country
    
    # === ДОБАВЛЕН МЕТОД ДЛЯ ВАЛИДАЦИИ ТЕЛЕФОНА ===
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        
        # Если поле пустое - разрешаем
        if not phone:
            return None
            
        # Удаляем все пробелы, дефисы, скобки
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Валидация формата
        phone_regex = r'^\+?1?\d{9,15}$'
        if not re.match(phone_regex, phone):
            raise ValidationError(
                "Номер телефона должен быть в формате: '+79991234567'. "
                "Максимум 15 цифр. Без пробелов и дефисов."
            )
        
        # Проверка уникальности
        if get_user_model().objects.filter(phone=phone).exists():
            raise ValidationError("Этот номер телефона уже используется.")
        
        return phone
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Пароли не совпадают')
        
        if password2 and len(password2) < 8:
            raise ValidationError('Пароль должен содержать минимум 8 символов')
            
        return password2
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'
        self.fields['username'].help_text = 'Обязательное поле. Не более 150 символов. Только буквы, цифры и @/./+/-/_.'
        self.fields['password1'].help_text = '''
        <ul class="mb-0">
            <li>Ваш пароль не должен быть слишком похож на другую вашу личную информацию.</li>
            <li>Ваш пароль должен содержать как минимум 8 символов.</li>
            <li>Ваш пароль не может быть commonly used паролем.</li>
            <li>Ваш пароль не может состоять только из цифр.</li>
        </ul>
        '''
        self.fields['password2'].help_text = 'Для подтверждения введите, пожалуйста, пароль ещё раз.'
        
        # Добавляем кастомные сообщения об ошибках для паролей
        self.fields['password1'].error_messages = {
            'required': 'Обязательное поле.',
            'password_too_short': 'Пароль должен содержать минимум 8 символов.',
            'password_too_common': 'Пароль слишком распространенный.',
            'password_entirely_numeric': 'Пароль не может состоять только из цифр.',
        }
        self.fields['password2'].error_messages = {
            'required': 'Обязательное поле.',
        }
        
        for field in self.fields.values():
            if not field.widget.attrs.get('class'):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs['class'] = 'form-select'
                else:
                    field.widget.attrs['class'] = 'form-control'

class LoginForm(forms.Form):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Обязательное поле.',
        }
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Обязательное поле.',
        }
    )

class ProfileEditForm(forms.ModelForm):
    # === ДОБАВЛЕНО ПОЛЕ ТЕЛЕФОНА ===
    phone = forms.CharField(
        max_length=17,
        required=False,
        label='Номер телефона',
        help_text='Формат: +79991234567',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+79991234567'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'nickname', 'email', 'country', 'phone']
        labels = {
            'username': 'Имя пользователя',
            'nickname': 'Никнейм', 
            'email': 'Email',
            'country': 'Страна',
            'phone': 'Номер телефона',
        }
        help_texts = {
            'username': 'Обязательное поле. Не более 150 символов. Только буквы, цифры и @/./+/-/_.',
        }
        error_messages = {
            'username': {
                'required': 'Обязательное поле.',
                'max_length': 'Не более 150 символов.',
                'invalid': 'Только буквы, цифры и @/./+/-/_.',
                'unique': 'Пользователь с таким именем уже существует.',
            },
            'email': {
                'required': 'Обязательное поле.',
                'invalid': 'Введите корректный email адрес.',
                'unique': 'Пользователь с таким email уже существует.',
            },
            'nickname': {
                'required': 'Обязательное поле.',
            },
            'country': {
                'required': 'Пожалуйста, выберите страну.',
            }
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username or username.strip() == '':
            raise ValidationError('Имя пользователя не может быть пустым')
        if self.user and get_user_model().objects.filter(username=username).exclude(pk=self.user.pk).exists():
            raise ValidationError('Пользователь с таким именем уже существует')
        
        return username.strip()
    
    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if not nickname or nickname.strip() == '':
            raise ValidationError('Никнейм не может быть пустым')
        return nickname.strip()
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email or email.strip() == '':
            raise ValidationError('Email не может быть пустым')
        
        if self.user and get_user_model().objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        
        return email.strip()
    
    def clean_country(self):
        country = self.cleaned_data.get('country')
        if not country:
            raise ValidationError('Пожалуйста, выберите страну')
        return country
    
    # === ДОБАВЛЕН МЕТОД ДЛЯ ВАЛИДАЦИИ ТЕЛЕФОНА ===
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        
        # Если поле пустое - разрешаем
        if not phone:
            return None
            
        # Удаляем все пробелы, дефисы, скобки
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Валидация формата
        phone_regex = r'^\+?1?\d{9,15}$'
        if not re.match(phone_regex, phone):
            raise ValidationError(
                "Номер телефона должен быть в формате: '+79991234567'. "
                "Максимум 15 цифр. Без пробелов и дефисов."
            )
        
        # Проверка уникальности
        if self.user and get_user_model().objects.filter(phone=phone).exclude(pk=self.user.pk).exists():
            raise ValidationError("Этот номер телефона уже используется.")
        
        return phone

class FanficForm(forms.ModelForm):
  
    
    class Meta:
        model = Fanfic
        fields = ['title', 'description', 'content', 'tags']
        labels = {
            'title': 'Название фанфика',
            'description': 'Описание',
            'content': 'Текст фанфика',
            'tags': 'Теги',
        }
        help_texts = {
            'tags': 'Введите теги через запятую (например: романтика, приключения, фэнтези)',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название вашего фанфика',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Краткое описание сюжета...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control fanfic-editor',
                'rows': 20,
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'романтика, приключения, фэнтези'
            }),
        }
        error_messages = {
            'title': {
                'required': 'Обязательное поле.',
                'max_length': 'Название слишком длинное.',
            },
            'description': {
                'required': 'Обязательное поле.',
            },
            'content': {
                'required': 'Обязательное поле.',
            },
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or title.strip() == '':
            raise ValidationError('Название не может быть пустым')
        return title.strip()
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or content.strip() == '':
            raise ValidationError('Содержание не может быть пустым')
        return content.strip()
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        if tags:
            # Очищаем теги от лишних запятых и пробелов
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            if not tag_list:
                raise ValidationError('Введите хотя бы один тег')
            # Ограничиваем количество тегов
            if len(tag_list) > 10:
                raise ValidationError('Максимальное количество тегов - 10')
            return ', '.join(tag_list)
        return tags

class CommentForm(forms.ModelForm):
    parent_id = forms.IntegerField(
        widget=forms.HiddenInput(attrs={
            'id': 'parent_id',
            'class': 'comment-parent-id'
        }),
        required=False,
        initial=None
    )
    
    class Meta:
        model = Comment
        fields = ['content', 'parent_id']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control comment-textarea',
                'rows': 3,
                'placeholder': 'Напишите комментарий...',
                'maxlength': '5000',
                'style': 'resize: vertical; min-height: 100px;',
                'data-min-length': '3',
                'data-max-length': '5000'
            }),
        }
        labels = {
            'content': '',
        }
        error_messages = {
            'content': {
                'required': 'Пожалуйста, введите текст комментария',
                'max_length': 'Комментарий слишком длинный (максимум 5000 символов)',
            }
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        
        if len(content) < 3:
            raise ValidationError(
                'Комментарий слишком короткий (минимум 3 символа)',
                code='too_short'
            )
        
        if len(content) > 5000:
            raise ValidationError(
                'Комментарий слишком длинный (максимум 5000 символов)',
                code='too_long'
            )
        
        # Проверка на запрещенные слова (опционально)
        forbidden_words = ['спам', 'реклама', 'оскорбление']  # Пример
        content_lower = content.lower()
        for word in forbidden_words:
            if word in content_lower:
                raise ValidationError(
                    'Комментарий содержит запрещенные слова',
                    code='forbidden_content'
                )
        
        return content
    
    def clean_parent_id(self):
        parent_id = self.cleaned_data.get('parent_id')
        
        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id, is_deleted=False)
                
                # Проверяем глубину вложенности
                if parent_comment.get_reply_depth() >= 5:
                    raise ValidationError(
                        'Превышена максимальная глубина вложенности комментариев (5 уровней)',
                        code='max_depth_exceeded'
                    )
                
                # Проверяем, что родительский комментарий принадлежит тому же фанфику
                # (эта проверка будет в view, но можно и здесь)
                
            except Comment.DoesNotExist:
                raise ValidationError(
                    'Родительский комментарий не найден или был удален',
                    code='parent_not_found'
                )
        
        return parent_id
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) if 'user' in kwargs else None
        self.fanfic = kwargs.pop('fanfic', None) if 'fanfic' in kwargs else None
        super().__init__(*args, **kwargs)
        
        # Устанавливаем кастомные атрибуты для валидации на клиенте
        self.fields['content'].widget.attrs.update({
            'minlength': '3',
            'maxlength': '5000',
            'data-msg-minlength': 'Минимум 3 символа',
            'data-msg-maxlength': 'Максимум 5000 символов',
            'data-msg-required': 'Введите текст комментария',
        })

class CommentEditForm(forms.ModelForm):
    """Форма для редактирования комментария"""
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control comment-edit-textarea',
                'rows': 3,
                'placeholder': 'Отредактируйте комментарий...',
                'maxlength': '5000',
                'style': 'resize: vertical; min-height: 100px;',
            }),
        }
        labels = {
            'content': '',
        }
        error_messages = {
            'content': {
                'required': 'Пожалуйста, введите текст комментария',
                'max_length': 'Комментарий слишком длинный (максимум 5000 символов)',
            }
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        
        if len(content) < 3:
            raise ValidationError(
                'Комментарий слишком короткий (минимум 3 символа)',
                code='too_short'
            )
        
        if len(content) > 5000:
            raise ValidationError(
                'Комментарий слишком длинный (максимум 5000 символов)',
                code='too_long'
            )
        
        return content
    
    def __init__(self, *args, **kwargs):
        self.comment = kwargs.pop('comment', None) if 'comment' in kwargs else None
        super().__init__(*args, **kwargs)
        
        if self.comment:
            # Показываем текущий текст комментария
            self.fields['content'].initial = self.comment.content

class FanficDeleteForm(forms.Form):
    """Форма для подтверждения удаления фанфика"""
    confirm = forms.BooleanField(
        required=True,
        label='Я подтверждаю удаление',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    permanent = forms.BooleanField(
        required=False,
        label='Удалить навсегда (без возможности восстановления)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Если не отмечено, фанфик переместится в корзину на 30 дней'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['confirm'].error_messages = {
            'required': 'Необходимо подтвердить удаление'
        }

class FanficRestoreForm(forms.Form):
    """Форма для восстановления фанфика из корзины"""
    restore_status = forms.ChoiceField(
        choices=[
            ('draft', 'Вернуть как черновик'),
            ('archived', 'Вернуть в архив'),
            ('published', 'Опубликовать сразу'),
        ],
        required=True,
        label='Статус при восстановлении',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Выберите статус фанфика после восстановления'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['restore_status'].initial = 'draft'

class EmptyTrashForm(forms.Form):
    """Форма для очистки всей корзины"""
    confirm = forms.BooleanField(
        required=True,
        label='Я подтверждаю, что хочу очистить всю корзину',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['confirm'].error_messages = {
            'required': 'Необходимо подтвердить очистку корзины'
        }

class BulkActionForm(forms.Form):
    """Форма для массовых действий с фанфиками"""
    ACTION_CHOICES = [
        ('publish', 'Опубликовать выбранные'),
        ('archive', 'Переместить в архив'),
        ('trash', 'Переместить в корзину'),
        ('delete', 'Удалить навсегда'),
        ('restore', 'Восстановить из корзины'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        required=True,
        label='Действие',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    fanfic_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    def clean_fanfic_ids(self):
        """Преобразуем строку с ID в список чисел"""
        ids_str = self.cleaned_data.get('fanfic_ids', '')
        try:
            # Ожидаем строку вида "1,2,3,4"
            ids = [int(id_str.strip()) for id_str in ids_str.split(',') if id_str.strip()]
            if not ids:
                raise ValidationError('Не выбрано ни одного фанфика')
            return ids
        except ValueError:
            raise ValidationError('Некорректный формат ID фанфиков')

class FanficSearchForm(forms.Form):
    """Форма для поиска фанфиков в корзине"""
    search = forms.CharField(
        required=False,
        label='Поиск в корзине',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию или описанию...'
        })
    )
    days_left = forms.ChoiceField(
        choices=[
            ('', 'Все'),
            ('7', 'Меньше 7 дней'),
            ('3', 'Меньше 3 дней'),
            ('1', 'Меньше 1 дня'),
        ],
        required=False,
        label='Осталось дней',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('deleted_at', 'Дате удаления (сначала новые)'),
            ('-deleted_at', 'Дате удаления (сначала старые)'),
            ('purge_at', 'Дате окончательного удаления'),
            ('title', 'Названию'),
        ],
        required=False,
        label='Сортировка',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class CommentDeleteForm(forms.Form):
    """Форма для подтверждения удаления комментария"""
    confirm = forms.BooleanField(
        required=True,
        label='Я подтверждаю удаление комментария',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    delete_replies = forms.BooleanField(
        required=False,
        label='Удалить также все ответы на этот комментарий',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        initial=False,
        help_text='Если отмечено, все ответы на этот комментарий также будут удалены'
    )
    
    def __init__(self, *args, **kwargs):
        self.comment = kwargs.pop('comment', None)
        super().__init__(*args, **kwargs)
        
        if self.comment:
            replies_count = self.comment.replies_count
            if replies_count > 0:
                self.fields['delete_replies'].help_text = f'Если отмечено, все {replies_count} ответов на этот комментарий также будут удалены'
        
        self.fields['confirm'].error_messages = {
            'required': 'Необходимо подтвердить удаление'
        }

class CommentSearchForm(forms.Form):
    """Форма для поиска комментариев"""
    search = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по тексту комментария...'
        })
    )
    author = forms.CharField(
        required=False,
        label='Автор',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Имя автора...'
        })
    )
    date_from = forms.DateField(
        required=False,
        label='С даты',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        label='По дату',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Сначала новые'),
            ('created_at', 'Сначала старые'),
            ('-updated_at', 'Сначала недавно измененные'),
            ('author', 'По автору (А-Я)'),
            ('-author', 'По автору (Я-А)'),
        ],
        required=False,
        label='Сортировка',
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='-created_at'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError('Дата "с" не может быть позже даты "по"')
        
        return cleaned_data

class TagSearchForm(forms.Form):
    """Форма для поиска по тегам"""
    tags = forms.CharField(
        required=True,
        label='Теги',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите теги через запятую...'
        }),
        help_text='Например: романтика, фэнтези, приключения'
    )
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '').strip()
        if not tags:
            raise ValidationError('Пожалуйста, введите хотя бы один тег')
        
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        if len(tag_list) > 5:
            raise ValidationError('Максимальное количество тегов для поиска - 5')
        
        return tags

class CommentReportForm(forms.Form):
    """Форма для жалобы на комментарий"""
    REASON_CHOICES = [
        ('spam', 'Спам или реклама'),
        ('offensive', 'Оскорбительное содержание'),
        ('hate_speech', 'Разжигание ненависти'),
        ('harassment', 'Преследование или домогательство'),
        ('inappropriate', 'Неуместный контент'),
        ('other', 'Другое'),
    ]
    
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        required=True,
        label='Причина жалобы',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    details = forms.CharField(
        required=False,
        label='Подробности',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Опишите проблему подробнее...',
            'maxlength': '1000'
        }),
        help_text='Необязательно, но поможет модераторам'
    )
    
    def clean_details(self):
        details = self.cleaned_data.get('details', '').strip()
        if details and len(details) > 1000:
            raise ValidationError('Слишком длинное описание (максимум 1000 символов)')
        return details

class CommentModerationForm(forms.Form):
    """Форма для модерации комментариев (админы/модераторы)"""
    ACTION_CHOICES = [
        ('approve', 'Одобрить'),
        ('delete', 'Удалить'),
        ('warn', 'Вынести предупреждение'),
        ('ban_user', 'Заблокировать пользователя'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        required=True,
        label='Действие',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    reason = forms.CharField(
        required=True,
        label='Причина',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Укажите причину действия...',
            'maxlength': '500'
        })
    )
    notify_user = forms.BooleanField(
        required=False,
        label='Уведомить пользователя',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        initial=True,
        help_text='Отправить пользователю уведомление о принятом действии'
    )
    
    def clean_reason(self):
        reason = self.cleaned_data.get('reason', '').strip()
        if len(reason) < 5:
            raise ValidationError('Пожалуйста, укажите более подробную причину')
        if len(reason) > 500:
            raise ValidationError('Слишком длинное описание (максимум 500 символов)')
        return reason