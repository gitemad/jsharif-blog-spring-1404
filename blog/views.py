from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import (
    Paginator,
    EmptyPage,
    PageNotAnInteger,
)
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count

# Create your views here.
class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 2
    template_name = 'blog/post/list.html'

def post_list(request, tag_slug=None):
    posts = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(
            Tag,
            slug=tag_slug,
        )
        posts = posts.filter(tags__in=[tag])

    paginator = Paginator(posts, 2)
    page_number = request.GET.get('page', 1)
    
    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        posts = paginator.page(1)

    return render(
        request,
        'blog/post/list.html',
        {
            'posts': posts,
            'tag': tag,
        }
    )

def post_detail(request, year, month, day, slug):
    post = get_object_or_404(
        Post,
        publish__year=year,
        publish__month=month,
        publish__day=day,
        slug=slug,
        status=Post.Status.PUBLISHED,
    )

    comments = post.comments.filter(active=True)

    form = CommentForm()

    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(
        tags__in=post_tags_ids
    ).exclude(id=post.id)
    similar_posts = similar_posts.annotate(
        same_tags=Count('tags')
    ).order_by('-same_tags', '-publish')[:3]
    
    return render(
        request,
        'blog/post/detail.html',
        {
            'post': post,
            'comments': comments,
            'form': form,
            'similar_posts': similar_posts,
        }
    )

def post_share(request, post_id):
    post = get_object_or_404(
        Post,
        id=post_id,
        status=Post.Status.PUBLISHED,
    )
    sent = False

    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            post_url = request.build_absolute_uri(
                post.get_absolute_url()
            )
            subject = f'"{cleaned_data['name']}" recommends you to read "{post.title}"'
            message = f'Read "{post.title}" at {post_url}\n\n\
            "{cleaned_data['name']}\'s comment: {cleaned_data['comment']}"\
            '
            from_email = 'a@a.com'
            to = [cleaned_data['to']]

            send_mail(subject, message, from_email, to)
            sent = True
    else:
        form = EmailPostForm()
    
    return render(
        request,
        'blog/post/share.html',
        {
            'post': post,
            'form': form,
            'sent': sent,
        }
    )

@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(
        Post,
        id=post_id,
        status=Post.Status.PUBLISHED,
    )
    comment = None
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    
    return render(
        request,
        'blog/post/comment.html',
        {
            'form': form,
            'post': post,
            'comment': comment,
        }
    )
