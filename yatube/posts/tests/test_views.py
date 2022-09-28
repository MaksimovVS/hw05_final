import shutil
import tempfile

from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    """Тестируем views приложения posts"""
    FIRST_OBJ = 0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.client = Client()
        cls.auth_client = Client()
        cls.follower_client = Client()
        cls.unfollower_client = Client()

        cls.user = User.objects.create_user(username='author')
        cls.follower = User.objects.create_user(username='follower')
        cls.unfollower = User.objects.create_user(username='unfollower')

        cls.auth_client.force_login(cls.user)
        cls.follower_client.force_login(cls.follower)
        cls.unfollower_client.force_login(cls.unfollower)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )

        for i in range(1, 12):
            Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост!!![{i}]',
                group_id=1,
                id=i,
            )
        cls.post_to_delete = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки кэша!!!',
            id=13,
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост!!!',
            group_id=1,
            image=cls.uploaded,
            id=14
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )
        cls.following = Follow.objects.create(
            user=cls.follower,
            author=cls.user,
        )

    def setUp(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().setUpClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', args=['author']): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', args=[self.post.pk]): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', args=[self.post.pk]): (
                'posts/create_post.html'
            ),
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Проверяем, что шаблон index получает правильный контекст"""
        response = self.client.get(reverse('posts:index'))
        last_object = response.context['page_obj'][self.FIRST_OBJ]
        self.assertEqual(last_object.text, self.post.text)
        self.assertEqual(last_object.image, self.post.image)

    def test_group_list_show_correct_context(self):
        """Проверяем, что шаблон group_list получает правильный контекст"""
        response = self.auth_client.get(reverse(
            'posts:group_posts', kwargs={'slug': 'test-slug'}
        ))
        context_page_obj = response.context['page_obj'][self.FIRST_OBJ].text
        context_group = response.context['group'].title
        self.assertEqual(context_page_obj, self.post.text)
        self.assertEqual(context_group, self.group.title)

    def test_profile_show_correct_context(self):
        """Проверяем, что шаблон profile получает правильный контекст"""
        response = self.auth_client.get(reverse(
            'posts:profile', args=['author']
        ))
        context_page_obj = response.context['page_obj'][self.FIRST_OBJ].text
        context_author = response.context['author'].username
        self.assertEqual(context_page_obj, 'Тестовый пост!!!')
        self.assertEqual(context_author, 'author')

    def test_post_detail_show_correct_context(self):
        """Проверяем, что шаблон post_detail получает правильный контекст"""
        post = PostsPagesTests.post
        response = self.auth_client.get(reverse(
            'posts:post_detail', args=[post.pk]
        ))
        context_post = response.context['post'].text
        context_comment = response.context['comments'][self.FIRST_OBJ].text
        self.assertEqual(context_post, 'Тестовый пост!!!')
        self.assertEqual(context_comment, 'Тестовый комментарий')

    def test_post_create_show_correct_context(self):
        """Проверяем, что шаблон post_create получает правильный контекст"""
        response = self.auth_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Проверяем, что шаблон post_edit получает правильный контекст"""
        post = PostsPagesTests.post
        response = self.auth_client.get(reverse(
            'posts:post_edit', args=[post.pk]
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        context_is_edit = response.context['is_edit']
        self.assertTrue(context_is_edit)

    def test_pagintator_page_records(self):
        """Проверяем работу Paginator'a"""
        pages_names_paginator = {
            reverse('posts:index'): {
                '': 10,
                '?page=2': Post.objects.all().count() - 10
            },
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}): {
                '': 10,
                '?page=2': self.group.posts.all().count() - 10
            },
            reverse('posts:profile', args=['author']): {
                '': 10,
                '?page=2': Post.objects.filter(author=self.user).count() - 10
            },
        }
        for page_name, paginator in pages_names_paginator.items():
            for address, post_cnt in paginator.items():
                with self.subTest(page_name=page_name):
                    response = self.auth_client.get(page_name + address)
                    context = response.context['page_obj']
                    self.assertEqual(len(context), post_cnt)

    def test_creating_post(self):
        """Проверяем, что пост отображатся где надо"""
        pages_names_presence_post = {
            reverse('posts:index'): True,
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}): True,
            reverse('posts:profile', args=['author']): True,
            reverse('posts:group_posts', kwargs={'slug': 'test-slug2'}): (
                False
            ),
        }
        for page_name, presence_post in pages_names_presence_post.items():
            with self.subTest(page_name=page_name):
                response = self.auth_client.get(page_name)
                post = Post.objects.filter(pk=10)[self.FIRST_OBJ]
                context = response.context['page_obj']
                self.assertEqual(post in context, presence_post)

    def test_save_post_in_cache(self):
        """Пост сохраняется в кэше и пропадает после отчистки кэша"""
        # Первый запрос для того, что бы кэшировались посты на странице
        self.response()
        # даляем пост из БД и запрашиваем пост из кэша
        Post.objects.get(id=self.post_to_delete.id).delete()
        self.assertTrue(
            self.post_to_delete.text.encode() in self.response().content
        )
        # Чистим кэш и снова ищем пост на странице
        cache.clear()
        self.assertFalse(
            self.post_to_delete.text.encode() in self.response().content
        )

    def response(self):
        """Возращает ответ сервера на запрос пользователя страницы index"""
        return self.client.get(reverse('posts:index'))

    def test_authorized_user_subscribe_to_authors(self):
        """
        Авторизованный пользователь может подписаться и отписатьсаться
        на автора
        """
        pages_names_result = {
            reverse('posts:profile_follow', args=['author']): True,
            reverse('posts:profile_unfollow', args=['author']): False,
        }
        for pages_name, result in pages_names_result.items():
            self.unfollower_client.get(pages_name)
            following = Follow.objects.filter(
                user=self.unfollower.id,
                author=self.user.id,
            ).exists()
            self.assertEqual(following, result)

    def test_new_post_appears_in_feed_only_for_subscribers(self):
        """
        Новая запись автора появляется в ленте только у подписанных
        пользователей
        """
        result_and_responses = {
            True: self.follower_client.get(reverse('posts:follow_index')),
            False: self.unfollower_client.get(reverse('posts:follow_index')),
        }
        for result, response in result_and_responses.items():
            context = response.context['page_obj']
            self.assertEqual(self.post in context, result)

    def test_vovkin_test(self):
        """
        Vovkin test
        """
        print(Follow.objects.all())
        self.unfollower_client.get(reverse('posts:profile_follow', args=['author']))
        print(Follow.objects.all())
        self.unfollower_client.get(
            reverse('posts:profile_follow', args=['author']))
        print(Follow.objects.all())