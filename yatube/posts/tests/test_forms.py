import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsCreateFormsTests(TestCase):
    """Тестируем Forms приложения posts"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.auth_client = Client()
        cls.user = User.objects.create_user(username='author')
        cls.auth_client.force_login(cls.user)

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост!!!',
        )
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
        cls.uploaded2 = SimpleUploadedFile(
            name='small2.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост!',
            'group': 1,
            'image': self.uploaded,
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:profile', args=['author'])
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text='Тестовый пост!',
            group=1,
            author=self.user,
            image='posts/small.gif'
        ).exists())

    def test_edit_post(self):
        """Валидная форма изменяет запись в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Пост тестовый!',
            'group': 2,
            'image': self.uploaded2,
        }
        response = self.auth_client.post(
            reverse('posts:post_edit', args=[self.post.pk]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=[self.post.pk])
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(
            text='Пост тестовый!',
            group=2,
            author=self.user,
            image='posts/small2.gif'
        ).exists())

    def test_add_comment(self):
        """Валидная форма создает комментарий и сохраняет в БД."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.auth_client.post(
            reverse('posts:add_comment', args=[self.post.pk]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=[self.post.pk])
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(Comment.objects.filter(
            text='Тестовый комментарий',
            post=self.post,
            author=self.user,
        ).exists())
