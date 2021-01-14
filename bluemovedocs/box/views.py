from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
import datetime
from .forms import BoxContentForm
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from allauth.socialaccount.models import SocialToken, SocialApp


@permission_required('auth.add_permission', raise_exception=True)
def write(request):
    form = BoxContentForm()
    return render(request, 'box/write.html', {'form': form})


@permission_required('auth.add_permission', raise_exception=True)
def create(request):
    if request.method == "POST":
        form = BoxContentForm(request.POST, request.FILES)
        if form.is_valid():
            box_category = request.POST.get('category')
            box_title = request.POST.get('title')
            box_writer = request.user
            box_document_id = request.POST.get('document_id')
            box_deadline = request.POST.get('deadline')
            box_image = request.FILES.get('image')
            form.save(category=box_category, title=box_title, writer=box_writer, document_id=box_document_id, deadline=box_deadline, image=box_image)
    return redirect('box:main') # POST와 GET 모두 box:main으로 redirect


@login_required
def create_doc(request):
    # 00. Google Drive API 호출하기
    # scope: settings.py -> SOCIALACCOUNT_PROVIDERS
    token = SocialToken.objects.get(account__user=request.user, account__provider='google')
    credentials = Credentials(
        client_id='54744281802-ccr39h4ohfts06d55oat9m8u6asud66r.apps.googleusercontent.com',
        client_secret='r4qzaZaNBq1u4X7ANuaf1vsf',
        token_uri='https://oauth2.googleapis.com/token',
        token=token.token,
        refresh_token=token.token_secret,
    )
    drive_service = build('drive', 'v3', credentials=credentials)

    # 01. 유저 My Drive에 블루무브 폴더 생성하기
    file_metadata = {
        'name': '블루무브',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    file = drive_service.files().create(body=file_metadata,
                                        fields='id').execute()
    folder_id = file.get('id')

    application_id = '1mRPI5haxz1IrjDw5oXVIXYSd89HKB_8hOhGxC09sq58' ### 지원서 File ID ###
    body = {
        'name': '4기 블루무버 지원서', # 나중에 제출일시 및 이름 추가하기
        'parents': [folder_id],
        'writersCanShare': True,
    }
    drive_response = drive_service.files().copy(
        fileId=application_id, body=body).execute()
    file_id = drive_response.get('id') ### File ID ###
    return redirect('https://drive.google.com/')


def main(request):
    opened_boxes = Box.objects.filter(deadline__gte=datetime.date.today()).order_by('deadline')
    closed_boxes = Box.objects.filter(deadline__lt=datetime.date.today()).order_by('deadline')
    # opened_page = request.GET.get('opened_page', 1)
    # closed_page = request.GET.get('closed_page', 1)
    page = request.GET.get('page', 1)
    opened_paginator = Paginator(opened_boxes, 9)
    closed_paginator = Paginator(closed_boxes, 9)
    try:
        # opened_boxes = opened_paginator.page(opened_page)
        # closed_boxes = closed_paginator.page(closed_page)
        opened_boxes = opened_paginator.page(page)
        closed_boxes = closed_paginator.page(page)
    except PageNotAnInteger:
        opened_boxes = opened_paginator.page(1)
        closed_boxes = closed_paginator.page(1)
    except EmptyPage:
        opened_boxes = opened_paginator.page(opened_paginator.num_pages)
        closed_boxes = closed_paginator.page(closed_paginator.num_pages)
    return render(request, 'box/main.html', {'opened_boxes': opened_boxes, 'closed_boxes': closed_boxes})


def read(request, id):
    box = Box.objects.get(pk=id)
    opened_boxes = Box.objects.filter(deadline__gte=datetime.date.today()).order_by('deadline')
    closed_boxes = Box.objects.filter(deadline__lt=datetime.date.today()).order_by('deadline')
    # opened_page = request.GET.get('opened_page', 1)
    # closed_page = request.GET.get('closed_page', 1)
    page = request.GET.get('page', 1)
    opened_paginator = Paginator(opened_boxes, 9)
    closed_paginator = Paginator(closed_boxes, 9)
    try:
        # opened_boxes = opened_paginator.page(opened_page)
        # closed_boxes = closed_paginator.page(closed_page)
        opened_boxes = opened_paginator.page(page)
        closed_boxes = closed_paginator.page(page)
    except PageNotAnInteger:
        opened_boxes = opened_paginator.page(1)
        closed_boxes = closed_paginator.page(1)
    except EmptyPage:
        opened_boxes = opened_paginator.page(opened_paginator.num_pages)
        closed_boxes = closed_paginator.page(closed_paginator.num_pages)
    return render(request, 'box/read.html', {'box': box, 'opened_boxes': opened_boxes, 'closed_boxes': closed_boxes})


@login_required
def box_favorite(request, id):
    box = get_object_or_404(Box, pk=id)
    
    if request.user in box.box_favorite_user_set.all():
        box.box_favorite_user_set.remove(request.user)
    else:
        box.box_favorite_user_set.add(request.user)

    if 'next' in request.GET:
        return redirect(request.GET['next'])
    else:
        return redirect('box:main')


@permission_required('auth.add_permission', raise_exception=True)
def update(request, id):
    box = get_object_or_404(Box, pk=id)
    form = BoxContentForm(instance=box)
    if request.method == "POST":
        form = BoxContentForm(request.POST, instance=box)
        if form.is_valid():
            box_category = request.POST.get('category')
            box_title = request.POST.get('title')
            box_document_id = request.POST.get('document_id')
            box_deadline = request.POST.get('deadline')
            form.update(category=box_category, title=box_title, document_id=box_document_id, deadline=box_deadline)
        return redirect('box:read', box.id)
    return render(request, 'box/update.html', {'box': box, 'form': form})


@permission_required('auth.add_permission', raise_exception=True)
def updateimage(request, id):
    box = get_object_or_404(Box, pk=id)
    form = BoxContentForm(instance=box)
    if request.method == "POST":
        box.image = request.FILES.get('image')
        box.save(update_fields=['image'])
        return redirect('box:read', box.id)
    return render(request, 'box/updateimage.html', {'box': box, 'form': form})


@permission_required('auth.add_permission', raise_exception=True)
def delete(request, id):
    box = get_object_or_404(Box, pk=id)
    box.delete()
    return redirect('box:main')