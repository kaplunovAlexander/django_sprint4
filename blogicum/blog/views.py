from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.urls import reverse, reverse_lazy

from .forms import MyUserChangeForm, PostForm, CommentForm
from .models import Post, Category, Comments


User = get_user_model()


class PostListView(ListView):
    """
    Представление для отображения списка публикаций.

    - Отображает 10 публикаций на странице.
    - Сортирует публикации по убыванию даты публикации.
    - Фильтрует опубликованные и доступные к просмотру публикации.
    - Добавляет аннотацию с количеством комментариев.
    """

    model = Post
    template_name = 'blog/index.html'
    ordering = '-pub_date'
    paginate_by = 10
    queryset = Post.objects.select_related(
        'author',
        'category',
        'location',
    ).filter(
        category__is_published=True,
        pub_date__lte=timezone.now(),
        is_published=True,
    ).annotate(
        comment_count=Count('comments')
    )


class PostDetailView(DetailView):
    """
    Представление для отображения деталей публикации.

    - Проверяет доступность публикации перед отображением.
    - Передает форму для комментариев в контекст.
    - Загружает список комментариев к публикации.
    """

    model = Post
    template_name = 'blog/detail.html'

    def get_object(self):

        obj = get_object_or_404(Post, pk=self.kwargs['post_id'])

        if not obj.is_viewable(timezone.now(), self.request.user):
            raise Http404("Публикация не найдена.")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            Comments.objects.filter(post=self.object).select_related('author')
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания новой публикации.

    - Доступно только авторизованным пользователям.
    - Автоматически назначает текущего пользователя автором публикации.
    - После успешного создания перенаправляет на страницу профиля автора.
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={
            'username': self.object.author.username
        })


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """
    Представление для редактирования публикации.

    - Доступно только автору публикации.
    - Если доступ запрещен, перенаправляет на страницу публикации.
    - После успешного обновления перенаправляет обратно к публикации.
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        if post.author != self.request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs["post_id"]})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """
    Представление для удаления публикации.

    - Доступно только автору публикации.
    - Если доступ запрещен, перенаправляет на страницу публикации.
    - После удаления перенаправляет на главную страницу.
    """

    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        if post.author != self.request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context


class ProfileView(ListView):
    """
    Представление для отображения профиля пользователя и его публикаций.

    - Загружает профиль пользователя по username.
    - Отображает 10 публикаций пользователя на странице.
    - Добавляет аннотацию с количеством комментариев.
    """

    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context

    @staticmethod
    def filter_published_posts(queryset, user=None, author=None):
        now = timezone.now()
        if user == author:
            return queryset
        return queryset.filter(
            is_published=True,
            pub_date__lte=now,
            category__is_published=True
        )

    def get_queryset(self):
        self.profile = get_object_or_404(
            User, username=self.kwargs['username']
        )
        queryset = Post.objects.filter(
            author=self.profile
        ).annotate(
            comment_count=Count('comments')
        ).order_by(*Post._meta.ordering)

        return self.filter_published_posts(
            queryset=queryset,
            user=self.request.user,
            author=self.profile
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Представление для обновления профиля пользователя.

    - Доступ к представлению имеют только авторизованные пользователи.
    - После успешного обновления профиля происходит редирект на страницу
      профиля пользователя.
    """

    model = User
    form_class = MyUserChangeForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.object.username}
        )


class CategoryListView(ListView):
    """
    Представление для отображения публикаций по категориям.

    - Проверяет, опубликована ли категория.
    - Если категория снята с публикации, выбрасывает 404.
    - Загружает публикации категории, сортирует их по дате.
    """

    model = Category
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category, slug=self.kwargs['category_slug'])

        if not self.category.is_published:
            raise Http404('Категория снята с публикации')

        return self.category.posts.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
        ).annotate(
            comment_count=Count('comments')
        ).order_by(*Post._meta.ordering)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class AddCommentView(LoginRequiredMixin, CreateView):
    """
    Представление для добавления комментария к публикации.

    - Доступ к представлению имеют только авторизованные пользователи.
    - После успешного добавления комментария происходит редирект на
      страницу публикации.
    """

    model = Comments
    form_class = CommentForm
    template_name = 'blog/detail.html'

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)

    def form_invalid(self, form):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    """
    Представление для редактирования комментария пользователя.

    - Доступ к редактированию имеет только автор комментария.
    - После успешного обновления комментария происходит редирект на
      страницу публикации.
    """

    model = Comments
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        comment = get_object_or_404(
            Comments,
            id=self.kwargs["comment_id"],
            post_id=post.pk
        )
        if comment.author != self.request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        post = get_object_or_404(
            Post,
            pk=self.kwargs["post_id"]
        )
        comment = get_object_or_404(
            Comments,
            id=self.kwargs["comment_id"],
            post_id=post.pk
        )
        return comment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comment = self.get_object()
        context['comment'] = comment
        return context

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs["post_id"]}
        )


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """
    Представление для удаления комментария пользователя.

    - Доступ к удалению имеет только автор комментария.
    - После успешного удаления комментария происходит редирект
      на страницу публикации.
    """

    model = Comments
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        comment = get_object_or_404(
            Comments,
            id=self.kwargs["comment_id"],
            post_id=post.pk
        )
        if comment.author != self.request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        post = get_object_or_404(
            Post,
            pk=self.kwargs["post_id"]
        )
        comment = get_object_or_404(
            Comments,
            id=self.kwargs["comment_id"],
            post_id=post.pk
        )
        return comment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop('form', None)
        context['comment'] = self.get_object()
        return context

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs["post_id"]}
        )
