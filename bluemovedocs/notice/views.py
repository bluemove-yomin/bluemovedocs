from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from .models import *


@permission_required('auth.add_permission', raise_exception=True)
def write(request):
    return render(request, 'notice/write.html')


@permission_required('auth.add_permission', raise_exception=True)
def create(request):
    if request.method == "POST":
        notice_category = request.POST.get('category')
        notice_title = request.POST.get('title')
        notice_writer = request.user
        notice_content = request.POST.get('content')
        notice_image = request.FILES.get('image')
        Notice.objects.create(category=notice_category, title=notice_title, writer=notice_writer, content=notice_content, image=notice_image)
    return redirect('notice:main')


@login_required
def create_comment(request, id):
    if request.method == "POST":
        notice = get_object_or_404(Notice, pk=id)
        comment_writer = request.user
        comment_content = request.POST.get('content')
        Comment.objects.create(writer=comment_writer, content=comment_content, notice=notice)
    return redirect('notice:read', notice.id)


def main(request):
    all_notices = Notice.objects.all().order_by('-id')
    return render(request, 'notice/main.html', {'all_notices': all_notices})


def read(request, id):
    notice = Notice.objects.get(pk=id)
    all_notices = Notice.objects.all().order_by('-id')
    all_comments = notice.comments.all().order_by('-id')
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
    if request.method == "POST":
        notice.category = request.POST['category']
        notice.title = request.POST['title']
        notice.content = request.POST['content']
        notice.save()
        return redirect('notice:read', notice.id)
    return render(request, 'notice/update.html', {'notice': notice})


@permission_required('auth.add_permission', raise_exception=True)
def updateimage(request, id):
    notice = get_object_or_404(Notice, pk=id)
    if request.method == "POST":
        notice.category = request.POST.get('category')
        notice.title = request.POST.get('title')
        notice.content = request.POST.get('content')
        notice.image = request.FILES.get('image')
        notice.save(update_fields=['image', 'updated_at'])
        return redirect('notice:read', notice.id)
    return render(request, 'notice/updateimage.html', {'notice': notice})


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