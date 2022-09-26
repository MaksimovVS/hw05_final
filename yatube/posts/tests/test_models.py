from django.test import TestCase

from posts.models import Group, Post, User


class PostsModelTest(TestCase):
    """Тестирование моделей приложения posts"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост!!!'
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        method__str__models = {
            self.group: 'Тестовая группа',
            self.post: 'Тестовый пост!!'
        }
        for model, expected_value in method__str__models.items():
            with self.subTest(model=model):
                self.assertEqual(
                    model.__str__(), expected_value)

    def test_verbose_name_and_help_text(self):
        """verbose_name и help_text в полях совпадает с ожидаемым."""
        models_field_verboses = {
            Group: {
                'title': 'Название группы',
                'slug': 'slug группы',
                'description': 'Описание группы',
            },
            Post: {
                'text': 'Текст поста',
                'pub_date': 'Дата публикации',
                'author': 'Автор',
                'group': 'Группа',
            }
        }
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for model, field_verboses in models_field_verboses.items():
            for field, expected_value in field_verboses.items():
                with self.subTest(model=model):
                    self.assertEqual(
                        model._meta.get_field(field).verbose_name,
                        expected_value,
                        f'Verbose_name {model} {field} неверно!'
                    )
                if field in field_help_text:
                    self.assertEqual(model._meta.get_field(field).help_text,
                                     field_help_text[field],
                                     f'help_text {model} {field} неверен!')
