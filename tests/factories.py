import factory
from django.contrib.auth import get_user_model
from main.models import Fanfic, Comment, Bookmark

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    nickname = factory.Faker('user_name')
    country = 'RU'
    phone = factory.Sequence(lambda n: f'+7999123{n:04d}')

class FanficFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Fanfic
    
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('paragraph')
    content = factory.Faker('text', max_nb_chars=1000)
    author = factory.SubFactory(UserFactory)
    status = 'published'
    tags = factory.Faker('words', nb=3, ext_word_list=['фэнтези', 'романтика', 'драма', 'комедия'])
    views_count = 0

class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment
    
    fanfic = factory.SubFactory(FanficFactory)
    author = factory.SubFactory(UserFactory)
    content = factory.Faker('paragraph')
    is_deleted = False

class BookmarkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bookmark
    
    user = factory.SubFactory(UserFactory)
    fanfic = factory.SubFactory(FanficFactory)
    notes = factory.Faker('sentence', nb_words=6)