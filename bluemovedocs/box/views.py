from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
import datetime
from .forms import BoxContentForm
from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials
from allauth.socialaccount.models import SocialToken, SocialApp, SocialAccount
from oauth2client.service_account import ServiceAccountCredentials
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
    name_verified = profile.info_update_flag
    if not name_verified == True:
        return redirect('users:write_info', request.user.id)
    else:
    # 회원가입 실명등록 끝
        box = get_object_or_404(Box, pk=id)
        # 01. 서비스 계정 Google Drive, Google Docs API 호출
        SERVICE_ACCOUNT_SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
        credentials = ServiceAccountCredentials.from_json_keyfile_name (
            'bluemove-docs-6a11a86cda0e.json',
            SERVICE_ACCOUNT_SCOPES,
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        docs_service = build('docs', 'v1', credentials=credentials)
        # 02. 서비스 계정 My Drive 내 템플릿 문서 생성(복사)
        application_id = box.document_id ##### 템플릿 문서 ID INPUT #####
        drive_response = drive_service.files().copy(
            fileId = application_id,
            body = {
                'name': '블루무브닥스_' + ##### 대분류는 나중에 확정하기(일단 블루무브닥스로 설정) #####
                        box.title.replace(" ","") + ##### 문서 이름 INPUT #####
                        request.user.last_name + request.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                        '_' + datetime.date.today().strftime('%y%m%d'),
                'description': '블루무브 닥스에서 생성된 ' +
                            request.user.last_name + request.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                            '님의 ' +
                            box.title ##### 문서 이름 INPUT #####
                            + '입니다.\n\n' +
                            '📧 생성일자: ' + datetime.date.today().strftime('%Y-%m-%d'), ##### 현재 일자 INPUT #####
            },
            fields = 'id, name'
        ).execute()
        file_id = drive_response.get('id') ##### 문서 ID OUTPUT #####
        name = drive_response.get('name') ##### 문서 이름 + OUTSIDE 클라이언트 성명 OUTPUT #####
        # 03. 문서 내 템플릿 태그 적용
        docs_response = docs_service.documents().batchUpdate(
            documentId = file_id,
            body = {
                'requests': [
                    {
                        'replaceAllText': {
                            'containsText': {
                                'text': '{{user-name}}',
                                'matchCase':  'true'
                            },
                            'replaceText': request.user.last_name + request.user.first_name, ##### OUTSIDE 클라이언트 성명 INPUT #####
                        }
                    },
                    {
                        'replaceAllText': {
                            'containsText': {
                                'text': '{{user-phone}}',
                                'matchCase':  'true'
                            },
                            'replaceText': request.user.profile.phone, ##### OUTSIDE 클라이언트 휴대전화 번호 INPUT #####
                        }
                    },
                    {
                        'replaceAllText': {
                            'containsText': {
                                'text': '{{user-email}}',
                                'matchCase':  'true'
                            },
                            'replaceText': request.user.email, ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
                        }
                    }
                ]
            }
        ).execute()
        # 04. 서비스 계정 권한 ID 조회
        drive_response = drive_service.permissions().list(
            fileId=file_id,
        ).execute()
        permissions_list = drive_response.get('permissions')
        for permissions_data in permissions_list:
            permission_id = permissions_data['id']
            # 05. OUTSIDE 클라이언트 권한 추가 writer
            drive_response = drive_service.permissions().create(
                fileId = file_id,
                body = {
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': request.user.email, ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
                },
            ).execute()
            outside_permission_id = drive_response.get('id') ##### OUTSIDE 클라이언트 권한 ID OUTPUT #####
            doc_user = request.user
            doc_name = name
            doc_file_id = file_id
            doc_outside_permission_id = outside_permission_id
            doc_permission_id = permission_id
            doc_creation_datetime = datetime.date.today().strftime('%Y-%m-%d')
            if SocialAccount.objects.filter(user=request.user):
                doc_avatar_src = SocialAccount.objects.filter(user=request.user)[0].extra_data['picture']
            else:
                doc_avatar_src = '/static/images/favicons/favicon-96x96.png'
            Doc.objects.create(user=doc_user, name=doc_name, file_id=doc_file_id, outside_permission_id=doc_outside_permission_id, permission_id=doc_permission_id, creation_datetime=doc_creation_datetime, avatar_src=doc_avatar_src, box=box)
            if 'next' in request.GET:
                return redirect(request.GET['next']) # 나중에 next 파라미터로 뭐 받을 수도 있을 거 같아서 일단 넣어둠
            else:
                return redirect('box:read', box.id)


def main(request):
    # 회원가입 실명등록 시작
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        name_verified = profile.info_update_flag
        if not name_verified == True:
            return redirect('users:write_info', request.user.id)
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
    # 회원가입 실명등록 끝 (아래 수정했으면 위에도 똑같이 수정해야 반영됨!!!)
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
        name_verified = profile.info_update_flag
        if not name_verified == True:
            return redirect('users:write_info', request.user.id)
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
                if request.user == box.writer:
                    all_docs = box.docs.filter(submit_flag=True)
                else:
                    all_docs = box.docs.filter(user=request.user)
            else:
                all_docs = None
            return render(request, 'box/read.html', {'box': box, 'opened_boxes': opened_boxes, 'closed_boxes': closed_boxes, 'all_docs': all_docs})
    else:
    # 회원가입 실명등록 끝 (아래 수정했으면 위에도 똑같이 수정해야 반영됨!!!)
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
            if request.user == box.writer:
                all_docs = box.docs.filter(submit_flag=True).filter(return_flag=False)
            else:
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
    outside_permission_id = doc.outside_permission_id
    # 01. 서비스 계정 Google Drive, Google Docs API 호출
    SERVICE_ACCOUNT_SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
    credentials = ServiceAccountCredentials.from_json_keyfile_name (
        'bluemove-docs-6a11a86cda0e.json',
        SERVICE_ACCOUNT_SCOPES,
    )
    drive_service = build('drive', 'v3', credentials=credentials)
    docs_service = build('docs', 'v1', credentials=credentials)
    # 06. 문서 잠그기
    drive_response = drive_service.files().update(
        fileId=file_id,
        body={
            "contentRestrictions": [
                {
                    "readOnly": "true",
                    "reason": "문서가 제출되었습니다. 내용 수정 방지를 위해 잠금 설정되었습니다."
                }
            ]
        }
    ).execute()
    # 07. OUTSIDE 클라이언트 권한 변경 writer 2 reader
    drive_response = drive_service.permissions().update(
        fileId = file_id,
        permissionId = outside_permission_id,
        body = {
            'role': 'reader',
        },
    ).execute()
    # 08. 문서 이름 및 설명 변경
    drive_response = drive_service.files().update(
        fileId = file_id,
        body = {
            'name': '블루무브닥스_' + ##### 대분류는 나중에 확정하기(일단 블루무브닥스로 설정) #####
                    doc.box.title.replace(" ","") + ##### 문서 이름 INPUT #####
                    request.user.last_name + request.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                    '_' + datetime.date.today().strftime('%y%m%d'),
            'description': '블루무브 닥스에서 생성된 ' +
                           request.user.last_name + request.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                           '님의 ' +
                           doc.box.title ##### 문서 이름 INPUT #####
                           + '입니다.\n\n' +
                           '📧 생성일자: ' + doc.creation_datetime + '\n' + ##### 문서 생성일자 INPUT #####
                           '📨 제출일자: ' + datetime.date.today().strftime('%Y-%m-%d'), ##### 현재 일자 INPUT #####
        },
        fields = 'name'
    ).execute()
    name = drive_response.get('name')
    # 09. INSIDE 클라이언트 권한 추가 writer
    drive_response = drive_service.permissions().create(
        fileId = file_id,
        body = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': doc.box.writer.email, ##### INSIDE 클라이언트 이메일 주소 INPUT #####
        },
    ).execute()
    inside_permission_id = drive_response.get('id') ##### INSIDE 클라이언트 권한 ID OUTPUT #####
    doc.name = name
    doc.submission_datetime = datetime.date.today().strftime('%Y-%m-%d')
    doc.inside_permission_id = inside_permission_id
    doc.submit_flag = True
    doc.save()
    return redirect('box:read', id=doc.box.id)


@permission_required('auth.add_permission', raise_exception=True)
def return_doc(request, doc_id):
    doc = get_object_or_404(Doc, pk=doc_id)
    file_id = doc.file_id
    inside_permission_id = doc.inside_permission_id
    outside_permission_id = doc.outside_permission_id
    permission_id = doc.permission_id
    # 01. 서비스 계정 Google Drive, Google Docs API 호출
    SERVICE_ACCOUNT_SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
    credentials = ServiceAccountCredentials.from_json_keyfile_name (
        'bluemove-docs-6a11a86cda0e.json',
        SERVICE_ACCOUNT_SCOPES,
    )
    drive_service = build('drive', 'v3', credentials=credentials)
    docs_service = build('docs', 'v1', credentials=credentials)
    # 10. INSIDE 클라이언트 권한 삭제 writer 2 none
    drive_response = drive_service.permissions().delete(
        fileId = file_id,
        permissionId = inside_permission_id,
    ).execute()
    # 11. OUTSIDE 클라이언트 권한 변경 reader 2 owner
    drive_response = drive_service.permissions().update(
        fileId = file_id,
        permissionId = outside_permission_id,
        transferOwnership = True,
        body = {
            'role': 'owner',
        },
    ).execute()
    # 12. 문서 이름 및 설명 변경
    drive_response = drive_service.files().update(
        fileId = file_id,
        body = {
            'name': '블루무브닥스_' + ##### 대분류는 나중에 확정하기(일단 블루무브닥스로 설정) #####
                    doc.box.title.replace(" ","") + ##### 문서 이름 INPUT #####
                    request.user.last_name + request.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                    '_' + datetime.date.today().strftime('%y%m%d'),
            'description': '블루무브 닥스에서 생성된 ' +
                           request.user.last_name + request.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                           '님의 ' +
                           doc.box.title ##### 문서 이름 INPUT #####
                           + '입니다.\n\n' +
                           '📧 생성일자: ' + doc.creation_datetime + '\n' + ##### 문서 생성일자 INPUT #####
                           '📨 제출일자: ' + doc.submission_datetime + '\n' + ##### 문서 제출일자 INPUT #####
                           '📩 반환일자: ' + datetime.date.today().strftime('%Y-%m-%d'), ##### 현재 일자 INPUT #####
        },
        fields = 'name'
    ).execute()
    name = drive_response.get('name') ##### 문서 이름 + OUTSIDE 클라이언트 성명 OUTPUT #####
    # 13. 서비스 계정 권한 삭제 writer 2 none
    drive_response = drive_service.permissions().delete(
        fileId = file_id,
        permissionId = permission_id,
    ).execute()
    return redirect('box:read', id=doc.box.id)