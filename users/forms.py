from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class RegistrationForm(UserCreationForm):
    nickname = forms.CharField(
        max_length=50, 
        required=True,
        label='Никнейм',
        help_text='Ваше отображаемое имя на сайте'
    )
    email = forms.EmailField(
        required=True,
        label='Email',
        help_text='Введите действующий email адрес'
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'nickname', 'email', 'password1', 'password2']
    
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
        
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class LoginForm(forms.Form):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
