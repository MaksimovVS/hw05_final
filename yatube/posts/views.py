from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.utils import IntegrityError

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User
from posts.services import get_page_obj

CACHE_TIMER_PER_SEC = 20


@cache_page(CACHE_TIMER_PER_SEC, key_prefix='index_page')
def index(request):
    """Возвращает главную страницу"""
    template = 'posts/index.html'
    post_list = Post.objects.select_related('author')
    page_obj = get_page_obj(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Возвращает страницу с постами группы"""
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    post_list = group.posts.select_related('group').all()
    page_obj = get_page_obj(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required(login_url='/auth/login')
def post_create(request):
    """Возвращает страницу создания поста"""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user.username)
    template = 'posts/create_post.html'
    context = {
        'form': form,
    }
    return render(request, template, context)


@login_required(login_url='/auth/login')
def post_edit(request, post_id):
    """Возвращает страницу редактирования поста"""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    is_edit = True
    template = 'posts/create_post.html'
    context = {
        'form': form,
        'post': post,
        'is_edit': is_edit
    }
    return render(request, template, context)


def profile(request, username):
    """Возвращает страницу профайла пользователя"""
    author = get_object_or_404(User, username=username)
    template = 'posts/profile.html'
    following = Follow.objects.filter(
        user=request.user.id,
        author=author.id,
    ).exists()
    post_list = author.posts.all()
    page_obj = get_page_obj(request, post_list)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Возвращает страницу подробной информации о посте"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required(login_url='/auth/login')
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required(login_url='/auth/login')
def follow_index(request):
    """Возвращает страницу с постами авторов, на которых есть подписка"""
    template = 'posts/index.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_obj(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required(login_url='/auth/login')
def profile_follow(request, username):
    """Обрабатывает кнопку 'Подписаться' на странице profile"""
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required(login_url='/auth/login')
def profile_unfollow(request, username):
    """Обрабатывает кнопку 'Отписаться' на странице profile"""
    author = get_object_or_404(User, username=username)
    user = request.user
    Follow.objects.get(user=user, author=author).delete()
    return redirect('posts:profile', username=username)
