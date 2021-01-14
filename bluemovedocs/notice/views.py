from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from allauth.socialaccount.models import SocialAccount
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
from .forms import NoticeContentForm


@permission_required('auth.add_permission', raise_exception=True)
def write(request):
    form = NoticeContentForm()
    return render(request, 'notice/write.html', {'form': form})


@permission_required('auth.add_permission', raise_exception=True)
def create(request):
    if request.method == "POST":
        form = NoticeContentForm(request.POST, request.FILES)
        if form.is_valid():
            notice_category = request.POST.get('category')
            notice_title = request.POST.get('title')
            notice_writer = request.user
            notice_image = request.FILES.get('image')
            form.save(category=notice_category, title=notice_title, writer = notice_writer, image=notice_image)
    return redirect('notice:main') # POST와 GET 모두 notice:main으로 redirect


@login_required
def create_comment(request, id):
    if request.method == "POST":
        notice = get_object_or_404(Notice, pk=id)
        # 유저가 Google 계정으로 로그인했을 경우 (블루무버 또는 게스트인 경우)
        if SocialAccount.objects.filter(user=request.user):
            comment_avatar_src = SocialAccount.objects.filter(user=request.user)[0].extra_data['picture']
        # 유저가 Google 계정으로 로그인하지 않았을 경우 (사무국 또는 어드민일 경우)
        else:
            comment_avatar_src = ''
        comment_writer = request.user
        comment_content = request.POST.get('content')
        Comment.objects.create(avatar_src=comment_avatar_src, writer=comment_writer, content=comment_content, notice=notice)
    return redirect('notice:read', notice.id)


def main(request):
    all_notices = Notice.objects.all().order_by('-id')
    page = request.GET.get('page', 1)
    paginator = Paginator(all_notices, 10)
    try:
        all_notices = paginator.page(page)
    except PageNotAnInteger:
        all_notices = paginator.page(1)
    except EmptyPage:
        all_notices = paginator.page(paginator.num_pages)
    return render(request, 'notice/main.html', {'all_notices': all_notices})


def read(request, id):
    notice = Notice.objects.get(pk=id)
    all_notices = Notice.objects.all().order_by('-id')
    all_comments = notice.comments.all().order_by('-id')
    page = request.GET.get('page', 1)
    paginator = Paginator(all_notices, 10)
    try:
        all_notices = paginator.page(page)
    except PageNotAnInteger:
        all_notices = paginator.page(1)
    except EmptyPage:
        all_notices = paginator.page(paginator.num_pages)
    return render(request, 'notice/read.html', {'notice': notice, 'all_notices': all_notices, 'all_comments': all_comments})


@login_required
def notice_favorite(request, id):
    notice = get_object_or_404(Notice, pk=id)
    
    if request.user in notice.favorite_user_set.all():
        notice.favorite_user_set.remove(request.user)
    else:
        notice.favorite_user_set.add(request.user)

    if 'next' in request.GET:
        return redirect(request.GET['next'])
    else:
        return redirect('notice:main')


@permission_required('auth.add_permission', raise_exception=True)
def update(request, id):
    notice = get_object_or_404(Notice, pk=id)
    form = NoticeContentForm(instance=notice)
    if request.method == "POST":
        form = NoticeContentForm(request.POST, instance=notice)
        if form.is_valid():
            notice_category = request.POST.get('category')
            notice_title = request.POST.get('title')
            form.update(category=notice_category, title=notice_title)
        return redirect('notice:read', notice.id)
    return render(request, 'notice/update.html', {'notice': notice, 'form': form})


@permission_required('auth.add_permission', raise_exception=True)
def updateimage(request, id):
    notice = get_object_or_404(Notice, pk=id)
    form = NoticeContentForm(instance=notice)
    if request.method == "POST":
        notice.image = request.FILES.get('image')
        notice.save(update_fields=['image', 'updated_at'])
        return redirect('notice:read', notice.id)
    return render(request, 'notice/updateimage.html', {'notice': notice, 'form': form})


@login_required
def updatecomment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    notice = Notice.objects.get(pk=comment.notice.id)
    all_notices = Notice.objects.all().order_by('-id')
    all_comments = notice.comments.all().order_by('-id')
    if request.method == "POST":
        comment.content = request.POST['content']
        comment.save()
        return redirect('notice:read', id=comment.notice.id)
    return render(request, 'notice/updatecomment.html', {'comment': comment, 'notice': notice, 'all_notices': all_notices, 'all_comments': all_comments})


@permission_required('auth.add_permission', raise_exception=True)
def delete(request, id):
    notice = get_object_or_404(Notice, pk=id)
    notice.delete()
    return redirect('notice:main')


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.delete()
    return redirect('notice:read', id=comment.notice.id)