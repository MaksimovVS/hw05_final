from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    """Тестирование URL приложения posts"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.author_client = Client()

        cls.user = User.objects.create_user(username='HasNoName')
        cls.user_author = User.objects.create_user(username='author')

        cls.authorized_client.force_login(cls.user)
        cls.author_client.force_login(cls.user_author)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост!!!'
        )

    def test_urls_uses_correct_template(self):
        """
        URL-адрес использует соответствующий шаблон и дает правильный ответ
        клинту-автору.
        """
        templates_url_names = {
            '/': ('posts/index.html', 'OK'),
            '/group/test-slug/': ('posts/group_list.html', 'OK'),
            '/create/': ('posts/create_post.html', 'OK'),
            '/posts/1/edit/': ('posts/create_post.html', 'OK'),
            '/profile/HasNoName/': ('posts/profile.html', 'OK'),
            '/posts/1/': ('posts/post_detail.html', 'OK'),
        }

        for address, parameters in templates_url_names.items():
            template, status_code = parameters
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Неверный шаблон {template} страницы {address}'
                )
                self.assertEqual(
                    response.reason_phrase,
                    status_code,
                    f'Неверный статус {response.reason_phrase} {address}'
                )

    def test_status_code_404(self):
        """Проверяем, что обращение на несуществующую страницу вернет 404"""
        self.assertEqual(
            self.guest_client.get('/unexisting_page/').reason_phrase,
            'Not Found'
        )

    def test_urls_exists_at_desired_location_auth_user(self):
        """Проверяем ответ страницы для авторизованного пользователя"""
        status_code_url = {
            '/create/': 'OK',
            '/posts/1/edit/': 'Found',
        }
        for address, status_code in status_code_url.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.reason_phrase, status_code)

    def test_urls_exists_at_desired_location_no_auth_user(self):
        """
        Проверяем ответ страницы редактирования поста и добавления комментария
        для неавторизованного пользователя
        """
        status_code_url = {
            '/posts/1/edit/': 'Found',
            '/posts/1/comment/': 'Found',
        }
        for address, status_code in status_code_url.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.reason_phrase, status_code)
