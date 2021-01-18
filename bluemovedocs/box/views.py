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
    name_verified = profile.info_update_flag
    if not name_verified == True:
        return redirect('users:write_info', request.user.id)
    else:
    # 회원가입 실명등록 끝
        box = get_object_or_404(Box, pk=id)
        # Google Drive, Google Docs API 호출하기
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
        docs_service = build('docs', 'v1', credentials=credentials)
        # 유저 My Drive에 블루무브 폴더 생성하기
        file_metadata = {
            'name': '블루무브',
            'mimeType': 'application/vnd.google-apps.folder',
        }
        file = drive_service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        folder_id = file.get('id')
        # 블루무브 폴더에 템플릿 문서 복사하기
        application_id = box.document_id ### 템플릿 문서 ID ###
        body = {
            'name': '4기 블루무버 지원서 - ' + request.user.last_name + request.user.first_name,
            'parents': [folder_id],
            'writersCanShare': True,
            # 'contentRestrictions': [
            #     {
            #         'readOnly': True,
            #         'reason': '문서가 제출되었습니다. 접수자가 검토를 마칠 때까지 수정할 수 없습니다.',
            #     }
            # ],
        }
        drive_response = drive_service.files().copy(
            fileId=application_id,
            body=body
        ).execute()
        file_id = drive_response.get('id') ### 유저 문서 ID ###
        name = drive_response.get('name')
        # 문서의 pageToken 시작하기
        drive_response = drive_service.files().watch(
            fileId = file_id
        )
        # 문서에 이름, 휴대전화 번호, 이메일 주소 입력하기
        requests = [
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{user-name}}',
                        'matchCase':  'true'
                    },
                    'replaceText': request.user.last_name + request.user.first_name,
                }
            },
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{user-phone}}',
                        'matchCase':  'true'
                    },
                    'replaceText': request.user.profile.phone,
                }
            },
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{user-email}}',
                        'matchCase':  'true'
                    },
                    'replaceText': request.user.email,
                }
            }
        ]

        docs_service.documents().batchUpdate(
            documentId=file_id,
            body = {
                'requests': requests
            }
        ).execute()
        # 유저의 문서 정보 저장하기
        doc_user = request.user
        doc_name = name
        doc_file_id = file_id
        if SocialAccount.objects.filter(user=request.user):
            doc_avatar_src = SocialAccount.objects.filter(user=request.user)[0].extra_data['picture']
        else:
            doc_avatar_src = '/static/images/favicons/favicon-96x96.png'
        Doc.objects.create(user=doc_user, name=doc_name, file_id=doc_file_id, avatar_src=doc_avatar_src, box=box)
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
                all_docs = box.docs.filter(submit_flag=True)
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
    # 문서 잠그기
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
    # 유저 Permission ID 불러오기
    drive_response = drive_service.permissions().list(
        fileId=file_id,
    ).execute()
    permissions_list = drive_response.get('permissions')
    for permissions_data in permissions_list:
        user_permission_id = permissions_data['id']
    # 문서 소유권 접수자에게 이전하기
    bluemove_permission_owner = {
        'type': 'user',
        'role': 'owner',
        'emailAddress': doc.box.writer.email, ### 블루무브 이메일 주소 ###
    }
    drive_response = drive_service.permissions().create(
        fileId=file_id,
        body=bluemove_permission_owner,
        transferOwnership=True,
        moveToNewOwnersRoot=True,
        fields='id',
    ).execute()
    bluemove_permission_id = drive_response.get('id')
    # 유저 권한을 뷰어로 변경하기
    user_permission_reader = {
        'role': 'reader',
    }
    drive_response = drive_service.permissions().update(
        fileId=file_id,
        permissionId=user_permission_id,
        body=user_permission_reader,
    ).execute()
    updated_user_permission_id = drive_response.get('id')
    doc.box_permission_id = bluemove_permission_id
    doc.user_permission_id = updated_user_permission_id
    doc.submit_flag = True
    doc.save()
    return redirect('box:read', id=doc.box.id)