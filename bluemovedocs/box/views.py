from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
import datetime
from .forms import BoxContentForm
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from allauth.socialaccount.models import SocialToken, SocialApp, SocialAccount
from users.models import Profile


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
def create_doc(request, id):
    # 회원가입 실명등록 시작
    profile = Profile.objects.get(user=request.user)
    name_verified = profile.name_update_flag
    if not name_verified == True:
        return redirect('users:write_name', request.user.id)
    else:
    # 회원가입 실명등록 끝
        box = get_object_or_404(Box, pk=id)
        # Google Drive API 호출하기
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
        # 유저 My Drive에 블루무브 폴더 생성하기
        file_metadata = {
            'name': '블루무브',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        file = drive_service.files().create(body=file_metadata,
                                            fields='id').execute()
        folder_id = file.get('id')
        # 블루무브 폴더에 템플릿 문서 복사하기
        application_id = box.document_id ### 템플릿 문서 ID ###
        body = {
            'name': '4기 블루무버 지원서 - ' + SocialAccount.objects.filter(user=request.user)[0].extra_data['name'],
            'parents': [folder_id],
            'writersCanShare': True,
        }
        drive_response = drive_service.files().copy(
            fileId=application_id, body=body).execute()
        file_id = drive_response.get('id') ### 유저 문서 ID ###
        name = drive_response.get('name')
        # 유저의 문서 정보 저장하기
        doc_user = request.user
        doc_name = name
        doc_file_id = file_id
        Doc.objects.create(user=doc_user, name=doc_name, file_id=doc_file_id, box=box)
        if 'next' in request.GET:
            return redirect(request.GET['next']) # 나중에 next 파라미터로 뭐 받을 수도 있을 거 같아서 일단 넣어둠
        else:
            return redirect('box:read', box.id)


def main(request):
    # 회원가입 실명등록 시작
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        name_verified = profile.name_update_flag
        if not name_verified == True:
            return redirect('users:write_name', request.user.id)
        else:
            opened_boxes = Box.objects.filter(deadline__gte=datetime.date.today()).order_by('deadline')
            closed_boxes = Box.objects.filter(deadline__lt=datetime.date.today()).order_by('deadline')
            page = request.GET.get('page', 1)
            opened_paginator = Paginator(opened_boxes, 9)
            closed_paginator = Paginator(closed_boxes, 9)
            try:
                opened_boxes = opened_paginator.page(page)
                closed_boxes = closed_paginator.page(page)
            except PageNotAnInteger:
                opened_boxes = opened_paginator.page(1)
                closed_boxes = closed_paginator.page(1)
            except EmptyPage:
                opened_boxes = opened_paginator.page(opened_paginator.num_pages)
                closed_boxes = closed_paginator.page(closed_paginator.num_pages)
            return render(request, 'box/main.html', {'opened_boxes': opened_boxes, 'closed_boxes': closed_boxes})
    else:
    # 회원가입 실명등록 끝
        opened_boxes = Box.objects.filter(deadline__gte=datetime.date.today()).order_by('deadline')
        closed_boxes = Box.objects.filter(deadline__lt=datetime.date.today()).order_by('deadline')
        page = request.GET.get('page', 1)
        opened_paginator = Paginator(opened_boxes, 9)
        closed_paginator = Paginator(closed_boxes, 9)
        try:
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
    # 회원가입 실명등록 시작
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        name_verified = profile.name_update_flag
        if not name_verified == True:
            return redirect('users:write_name', request.user.id)
        else:
            box = Box.objects.get(pk=id)
            opened_boxes = Box.objects.filter(deadline__gte=datetime.date.today()).order_by('deadline')
            closed_boxes = Box.objects.filter(deadline__lt=datetime.date.today()).order_by('deadline')
            page = request.GET.get('page', 1)
            opened_paginator = Paginator(opened_boxes, 9)
            closed_paginator = Paginator(closed_boxes, 9)
            try:
                opened_boxes = opened_paginator.page(page)
                closed_boxes = closed_paginator.page(page)
            except PageNotAnInteger:
                opened_boxes = opened_paginator.page(1)
                closed_boxes = closed_paginator.page(1)
            except EmptyPage:
                opened_boxes = opened_paginator.page(opened_paginator.num_pages)
                closed_boxes = closed_paginator.page(closed_paginator.num_pages)
            if request.user.is_authenticated:
                all_docs = box.docs.filter(user=request.user)
            else:
                all_docs = None
            return render(request, 'box/read.html', {'box': box, 'opened_boxes': opened_boxes, 'closed_boxes': closed_boxes, 'all_docs': all_docs})
    else:
    # 회원가입 실명등록 끝
        box = Box.objects.get(pk=id)
        opened_boxes = Box.objects.filter(deadline__gte=datetime.date.today()).order_by('deadline')
        closed_boxes = Box.objects.filter(deadline__lt=datetime.date.today()).order_by('deadline')
        page = request.GET.get('page', 1)
        opened_paginator = Paginator(opened_boxes, 9)
        closed_paginator = Paginator(closed_boxes, 9)
        try:
            opened_boxes = opened_paginator.page(page)
            closed_boxes = closed_paginator.page(page)
        except PageNotAnInteger:
            opened_boxes = opened_paginator.page(1)
            closed_boxes = closed_paginator.page(1)
        except EmptyPage:
            opened_boxes = opened_paginator.page(opened_paginator.num_pages)
            closed_boxes = closed_paginator.page(closed_paginator.num_pages)
        if request.user.is_authenticated:
            all_docs = box.docs.filter(user=request.user)
        else:
            all_docs = None
        return render(request, 'box/read.html', {'box': box, 'opened_boxes': opened_boxes, 'closed_boxes': closed_boxes, 'all_docs': all_docs})


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


@login_required
def delete_doc(request, doc_id):
    doc = get_object_or_404(Doc, pk=doc_id)
    doc.delete()
    return redirect('box:read', id=doc.box.id)


@login_required
def submit_doc(request, doc_id):
    doc = get_object_or_404(Doc, pk=doc_id)
    file_id = doc.file_id
    # Google Drive API 호출하기
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
    # 유저 Permission ID 불러오기
    def callback_for_permissions_list(request_id, response, exception):
        if exception:
            return redirect('box:read', id=doc.box.id)
        else:
            permissions_list = response.get('permissions') ### 유저 Permissions List ###
            for permissions_data in permissions_list:
                user_permission_id = permissions_data['id'] ### 유저 Permission ID ###
        # 지원서 소유권 블루무브로 이전하기
        def callback_for_bluemove_ownership(request_id, response, exception):
            if exception:
                return redirect('box:read', id=doc.box.id)
            else:
                bluemove_permission_id = response.get('id') ### 블루무브 Permission ID ###
                doc.box_permission_id = bluemove_permission_id
                doc.save(update_fields=['box_permission_id'])
        batch = drive_service.new_batch_http_request(callback=callback_for_bluemove_ownership)
        bluemove_permission_owner = {
            'type': 'user',
            'role': 'owner',
            'emailAddress': 'bwbluemove@gmail.com', ### 블루무브 이메일 주소 ###
        }
        batch.add(drive_service.permissions().create(
                fileId=file_id,
                body=bluemove_permission_owner,
                transferOwnership=True,
                moveToNewOwnersRoot=True,
                fields='id',
        ))
        batch.execute()
        # 유저 권한을 뷰어로 변경하기
        def callback_for_update_permission(request_id, response, exception):
            if exception:
                return redirect('box:read', id=doc.box.id)
            else:
                updated_user_permission_id = response.get('id') ### 업데이트된 유저 Permission ID ###
            doc.user_permission_id = updated_user_permission_id
            doc.submit_flag = True
            doc.save()
            # return redirect('box:read', id=doc.box.id)
        batch = drive_service.new_batch_http_request(callback=callback_for_update_permission)
        user_permission_reader = {
            'role': 'reader',
        }
        batch.add(drive_service.permissions().update(
                fileId=file_id,
                permissionId=user_permission_id,
                body=user_permission_reader,
        ))
        batch.execute()
    batch = drive_service.new_batch_http_request(callback=callback_for_permissions_list)
    batch.add(drive_service.permissions().list(
            fileId=file_id,
    ))
    batch.execute()
    return redirect('box:read', id=doc.box.id)