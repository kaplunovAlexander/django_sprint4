from django.contrib import admin

from .models import Post, Location, Category, Comments


class PostInline(admin.TabularInline):
    model = Post
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'title',
        'slug',
        'is_published',
    )
    list_editable = (
        'is_published',
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'name',
        'is_published',
    )
    list_editable = (
        'is_published',
    )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_published',
        'created_at',
        'pub_date',
        'author',
        'location',
        'category',
    )
    list_editable = (
        'is_published',
        'pub_date',
        'category',
        'location',
    )


@admin.register(Comments)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'text',
        'author',
        'created_at',
        'post',
    )
    list_display_links = (
        'text',
    )


admin.site.empty_value_display = 'Не задано'
