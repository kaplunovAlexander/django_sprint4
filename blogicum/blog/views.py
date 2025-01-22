from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
from django.db.models import Count
from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.urls import reverse, reverse_lazy

from .forms import MyUserChangeForm, PostForm, CommentForm
from .models import Post, Category, Comments


User = get_user_model()


class PostListView(ListView):
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
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset: QuerySet[Any] | None = ...) -> Model:

        obj = get_object_or_404(Post, pk=self.kwargs.get('pk'))

        if not obj.is_viewable(timezone.now(), self.request.user):
            raise Http404("Публикация не найдена.")

        return obj

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            Comments.objects.filter(post=self.object).select_related('author')
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
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


class CategoryListView(ListView):
    model = Category
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])

        if not self.category.is_published:
            raise Http404('Категория снята с публикации')

        return self.category.posts.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        self.profile = get_object_or_404(
            User, username=self.kwargs['username']
        )
        return Post.objects.filter(
            author=self.profile
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = MyUserChangeForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Только авторизованные пользователи могут редактировать профиль.")
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comments
    form_class = CommentForm
    template_name = 'blog/detail.html'

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)

    def form_invalid(self, form):
        return redirect('blog:post_detail', pk=self.kwargs['pk'])

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comments
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        comment = get_object_or_404(Comments, id=self.kwargs["comment_id"], post_id=post.pk)
        if comment.author != self.request.user:
            return redirect('blog:post_detail', pk=post.pk)
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
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs["post_id"]})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comments
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        comment = get_object_or_404(Comments, id=self.kwargs["comment_id"], post_id=post.pk)
        if comment.author != self.request.user:
            return redirect('blog:post_detail', pk=post.pk)
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
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs["post_id"]})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs["pk"])
        if post.author != self.request.user:
            return redirect('blog:post_detail', pk=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs["pk"]})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs["pk"])
        if post.author != self.request.user:
            return redirect('blog:post_detail', pk=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context
