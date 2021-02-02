from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
from django.db.models import Q
import datetime
import base64
import requests
import urllib
from .forms import BoxContentForm
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from email.mime.text import MIMEText
from allauth.socialaccount.models import SocialToken, SocialApp, SocialAccount
from oauth2client.service_account import ServiceAccountCredentials
from users.models import Profile
from slack_sdk import WebClient





@login_required
# @permission_required('auth.add_permission', raise_exception=True)
def write(request):
    form = BoxContentForm()
    client = WebClient(token=slack_bot_token)
    slack_response = client.conversations_list(
        team_id = 'T2EH6PN00'
    )
    all_channels = slack_response.get('channels')
    channels_list = []
    for channels_data in all_channels:
        channels_id = channels_data.get('id')
        channels_name = channels_data.get('name')
        channels_list.append(tuple((channels_id, channels_name)))
    channels_list = sorted(channels_list, key=lambda tup: (tup[1]))
    return render(request, 'box/write.html', {'form': form, 'channels_list': channels_list})


@login_required
# @permission_required('auth.add_permission', raise_exception=True)
def create(request):
    if request.method == "POST":
        form = BoxContentForm(request.POST, request.FILES)
        if form.is_valid() and request.POST.get('category') == 'bluemover':
            box_category = request.POST.get('category')
            box_prefix = request.POST.get('prefix')
            box_title = request.POST.get('title')
            box_writer = request.user
            box_document_id = request.POST.get('document_id').replace("https://docs.google.com/document/d/","")[0:44]
            box_folder_id = request.POST.get('folder_id').replace("https://drive.google.com/drive/folders/","")[0:33]
            box_channel_id = request.POST.get('channel_id')
            box_deadline = request.POST.get('deadline')
            box_image = request.FILES.get('image')
            form.save(category=box_category, prefix=box_prefix, title=box_title, writer=box_writer, document_id=box_document_id, folder_id=box_folder_id, channel_id=box_channel_id, deadline=box_deadline, image=box_image)
        elif form.is_valid() and request.POST.get('category') == 'guest':
            box_category = request.POST.get('category')
            box_title = request.POST.get('title')
            box_writer = request.user
            box_document_id = request.POST.get('document_id').replace("https://docs.google.com/document/d/","")[0:44]
            box_channel_id = request.POST.get('channel_id')
            box_deadline = request.POST.get('deadline')
            box_image = request.FILES.get('image')
            form.save(category=box_category, title=box_title, writer=box_writer, document_id=box_document_id, channel_id=box_channel_id, deadline=box_deadline, image=box_image)
    return redirect('box:main') # POST와 GET 모두 box:main으로 redirect


@login_required
def create_doc(request, id):
    # 회원가입 정보등록 시작
    profile = Profile.objects.get(user=request.user)
    name_verified = profile.info_update_flag
    if not name_verified == True:
        return redirect('users:write_info', request.user.id)
    else:
    # 회원가입 정보등록 끝
        box = get_object_or_404(Box, pk=id)
        # 00. 기한 초과 시 새로고침
        if box.deadline_is_over :
            return redirect('box:read', box.id)
        ###############################################
        ##### OUTSIDE 클라이언트가 bluemover일 경우 #####
        ###############################################
        if request.user.profile.level == 'bluemover':
            # 01. OUTSIDE 클라이언트 Google Drive, Google Docs API 호출
            token = SocialToken.objects.get(account__user=request.user, account__provider='google')
            credentials = Credentials(
                client_id=client_id,
                client_secret=client_secret,
                token_uri='https://oauth2.googleapis.com/token',
                token=token.token,
                refresh_token=token.token_secret,
            )
            drive_service = build('drive', 'v3', credentials=credentials)
            docs_service = build('docs', 'v1', credentials=credentials)
            # 02. OUTSIDE 클라이언트 My Drive 내 템플릿 문서 생성(복사)
            application_id = box.document_id ##### 템플릿 문서 ID INPUT #####
            drive_response = drive_service.files().copy(
                fileId = application_id,
                body = {
                    'name': box.prefix + '_' + ##### 파일 프리픽스 INPUT #####
                            box.title.replace(" ","") + ##### 문서명 INPUT #####
                            request.user.last_name + request.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                            '_' + datetime.date.today().strftime('%y%m%d'),
                    'description': '블루무브 닥스에서 생성된 ' +
                                request.user.last_name + request.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                                '님의 ' +
                                box.title ##### 문서명 INPUT #####
                                + '입니다.\n\n' +
                                '📧 생성일자: ' + datetime.date.today().strftime('%Y-%m-%d'), ##### 현재 일자 INPUT #####
                },
                fields = 'id, name'
            ).execute()
            file_id = drive_response.get('id') ##### 문서 ID OUTPUT #####
            name = drive_response.get('name') ##### 파일 최종 이름 OUTPUT #####
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
            # 04. OUTSIDE 클라이언트 권한 ID 조회
            drive_response = drive_service.permissions().list(
                fileId = file_id,
            ).execute()
            permissions_list = drive_response.get('permissions')
            for permissions_data in permissions_list:
                outside_permission_id = permissions_data['id'] ##### OUTSIDE 클라이언트 권한 ID OUTPUT #####
                # 05. 문서 데이터 DB 반영
                doc_user = request.user
                doc_name = name
                doc_file_id = file_id
                doc_outside_permission_id = outside_permission_id
                doc_creation_date = datetime.date.today().strftime('%Y-%m-%d')
                if SocialAccount.objects.filter(user=request.user):
                    doc_avatar_src = SocialAccount.objects.filter(user=request.user)[0].extra_data['picture']
                else:
                    doc_avatar_src = '/static/images/favicons/favicon-96x96.png'
                Doc.objects.create(user=doc_user, name=doc_name, file_id=doc_file_id, outside_permission_id=doc_outside_permission_id, creation_date=doc_creation_date, avatar_src=doc_avatar_src, box=box)
                if 'next' in request.GET:
                    return redirect(request.GET['next']) # 나중에 next 파라미터로 뭐 받을 수도 있을 거 같아서 일단 넣어둠
                else:
                    return redirect('box:read', box.id)
        ###########################################
        ##### OUTSIDE 클라이언트가 guest일 경우 #####
        ###########################################
        if request.user.profile.level == 'guest':
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
                    'name': '블루무브닥스_' +
                            box.title.replace(" ","") + ##### 문서명 INPUT #####
                            request.user.last_name + request.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                            '_' + datetime.date.today().strftime('%y%m%d'),
                    'description': '블루무브 닥스에서 생성된 ' +
                                request.user.last_name + request.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                                '님의 ' +
                                box.title ##### 문서명 INPUT #####
                                + '입니다.\n\n' +
                                '📧 생성일자: ' + datetime.date.today().strftime('%Y-%m-%d'), ##### 현재 일자 INPUT #####
                },
                fields = 'id, name'
            ).execute()
            file_id = drive_response.get('id') ##### 문서 ID OUTPUT #####
            name = drive_response.get('name') ##### 파일 최종 이름 OUTPUT #####
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
                    sendNotificationEmail = False,
                    body = {
                        'type': 'user',
                        'role': 'writer',
                        'emailAddress': request.user.email, ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
                    },
                ).execute()
                outside_permission_id = drive_response.get('id') ##### OUTSIDE 클라이언트 권한 ID OUTPUT #####
                # 06. 문서 데이터 DB 반영
                doc_user = request.user
                doc_name = name
                doc_file_id = file_id
                doc_outside_permission_id = outside_permission_id
                doc_permission_id = permission_id
                doc_creation_date = datetime.date.today().strftime('%Y-%m-%d')
                if SocialAccount.objects.filter(user=request.user):
                    doc_avatar_src = SocialAccount.objects.filter(user=request.user)[0].extra_data['picture']
                else:
                    doc_avatar_src = '/static/images/favicons/favicon-96x96.png'
                Doc.objects.create(user=doc_user, name=doc_name, file_id=doc_file_id, outside_permission_id=doc_outside_permission_id, permission_id=doc_permission_id, creation_date=doc_creation_date, avatar_src=doc_avatar_src, box=box)
                if 'next' in request.GET:
                    return redirect(request.GET['next']) # 나중에 next 파라미터로 뭐 받을 수도 있을 거 같아서 일단 넣어둠
                else:
                    return redirect('box:read', box.id)


def main(request):
    # 회원가입 정보등록 시작
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        if not profile.info_update_flag == True:
            return redirect('users:write_info', request.user.id)
        else:
            None
    else:
        None
    # 회원가입 정보등록 끝
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
    # 회원가입 정보등록 시작
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        if not profile.info_update_flag == True:
            return redirect('users:write_info', request.user.id)
        else:
            None
    else:
        None
    # 회원가입 정보등록 끝
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
        ###################################
        ##### INSIDE 클라이언트일 경우 #####
        ###################################
        if request.user == box.writer:
            all_docs = box.docs.filter(Q(submit_flag=True) & Q(reject_flag=False) & Q(return_flag=False)).order_by('-id')
            for doc in all_docs:
                if doc.user.profile.level == 'bluemover':
                    doc_src = "https://docs.google.com/document/d/" + doc.file_id
                    try:
                        urllib.request.urlopen(doc_src)
                    except urllib.error.HTTPError:
                        doc.delete()
                        return redirect('box:read', id=doc.box.id)
                    # r = requests.get(doc_src)
                    # if not r.status_code == 200:
                    #     doc.delete()
                    #     return redirect('box:read', id=doc.box.id)
                    # else:
                    #     None
                else:
                    None
        ###########################################
        ##### OUTSIDE 클라이언트가 guest일 경우 #####
        ###########################################
        else:
            all_docs = box.docs.filter(user=request.user)
            ###############################################
            ##### OUTSIDE 클라이언트가 bluemover일 경우 #####
            ###############################################
            for doc in all_docs:
                if doc.user.profile.level == 'bluemover':
                    if doc.delete_flag == True:
                        None
                    else:
                        doc_src = "https://docs.google.com/document/d/" + doc.file_id
                        try:
                            urllib.request.urlopen(doc_src)
                        except urllib.error.HTTPError:
                            if doc.return_flag == True:
                                doc.delete_flag = True
                                doc.save()
                                return redirect('box:read', id=doc.box.id)
                            else:
                                doc.delete()
                                return redirect('box:read', id=doc.box.id)
                        # r = requests.get(doc_src)
                        # if not r.status_code == 200:
                        #     if doc.return_flag == True:
                        #         doc.delete_flag = True
                        #         doc.save()
                        #         return redirect('box:read', id=doc.box.id)
                        #     else:
                        #         doc.delete()
                        #         return redirect('box:read', id=doc.box.id)
                        # else:
                        #     None
                else:
                    None
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


@login_required
# @permission_required('auth.add_permission', raise_exception=True)
def update(request, id):
    box = get_object_or_404(Box, pk=id)
    form = BoxContentForm(instance=box)
    client = WebClient(token=slack_bot_token)
    slack_response = client.conversations_list(
        team_id = 'T2EH6PN00'
    )
    all_channels = slack_response.get('channels')
    channels_list = []
    for channels_data in all_channels:
        channels_id = channels_data.get('id')
        channels_name = channels_data.get('name')
        channels_list.append(tuple((channels_id, channels_name)))
    channels_list = sorted(channels_list, key=lambda tup: (tup[1]))
    if request.method == "POST":
        form = BoxContentForm(request.POST, instance=box)
        if form.is_valid() and box.category == 'bluemover':
            box_prefix = request.POST.get('prefix')
            box_title = request.POST.get('title')
            box_document_id = request.POST.get('document_id').replace("https://docs.google.com/document/d/","")[0:44]
            box_folder_id = request.POST.get('folder_id').replace("https://drive.google.com/drive/folders/","")[0:33]
            box_channel_id = request.POST.get('channel_id')
            box_deadline = request.POST.get('deadline')
            form.update(prefix=box_prefix, title=box_title, document_id=box_document_id, folder_id=box_folder_id, channel_id=box_channel_id, deadline=box_deadline)
        elif form.is_valid() and box.category == 'guest':
            box_title = request.POST.get('title')
            box_document_id = request.POST.get('document_id').replace("https://docs.google.com/document/d/","")[0:44]
            box_channel_id = request.POST.get('channel_id')
            box_deadline = request.POST.get('deadline')
            form.update(title=box_title, document_id=box_document_id, channel_id=box_channel_id, deadline=box_deadline)
        return redirect('box:read', box.id)
    return render(request, 'box/update.html', {'box': box, 'form': form, 'channels_list': channels_list})


@login_required
# @permission_required('auth.add_permission', raise_exception=True)
def updateimage(request, id):
    box = get_object_or_404(Box, pk=id)
    form = BoxContentForm(instance=box)
    client = WebClient(token=slack_bot_token)
    slack_response = client.conversations_list(
        team_id = 'T2EH6PN00'
    )
    all_channels = slack_response.get('channels')
    channels_list = []
    for channels_data in all_channels:
        channels_id = channels_data.get('id')
        channels_name = channels_data.get('name')
        channels_list.append(tuple((channels_id, channels_name)))
    channels_list = sorted(channels_list, key=lambda tup: (tup[1]))
    if request.method == "POST":
        box.image = request.FILES.get('image')
        box.save(update_fields=['image'])
        return redirect('box:read', box.id)
    return render(request, 'box/updateimage.html', {'box': box, 'form': form, 'channels_list': channels_list})


@login_required
# @permission_required('auth.add_permission', raise_exception=True)
def delete(request, id):
    box = get_object_or_404(Box, pk=id)
    box.delete()
    return redirect('box:main')


@login_required
def delete_doc(request, doc_id):
    doc = get_object_or_404(Doc, pk=doc_id)
    file_id = doc.file_id
    ###############################################
    ##### OUTSIDE 클라이언트가 bluemover일 경우 #####
    ###############################################
    if doc.user.profile.level == 'bluemover':
        # 01. OUTSIDE 클라이언트 Google Drive API 호출
        token = SocialToken.objects.get(account__user=request.user, account__provider='google')
        credentials = Credentials(
            client_id=client_id,
            client_secret=client_secret,
            token_uri='https://oauth2.googleapis.com/token',
            token=token.token,
            refresh_token=token.token_secret,
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        # 02. 문서 삭제
        try:
            drive_response = drive_service.files().delete(
                fileId = file_id,
            ).execute()
        except:
            doc.delete()
            return redirect('box:read', id=doc.box.id)
        # 03. 문서 데이터 DB 반영
        doc.delete()
        return redirect('box:read', id=doc.box.id)
    ###########################################
    ##### OUTSIDE 클라이언트가 guest일 경우 #####
    ###########################################
    if doc.user.profile.level == 'guest':
        # 01. 서비스 계정 Google Drive, Gmail API 호출
        SERVICE_ACCOUNT_SCOPES = ['https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name (
            'bluemove-docs-6a11a86cda0e.json',
            SERVICE_ACCOUNT_SCOPES,
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        INSIDE_CLIENT = doc.box.writer.email
        user_id = doc.box.writer.email
        SERVICE_ACCOUNT_GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        gmail_credentials = service_account.Credentials.from_service_account_file(
            'bluemove-docs-6a11a86cda0e.json',
            scopes = SERVICE_ACCOUNT_GMAIL_SCOPES,
        )
        credentials_delegated = gmail_credentials.with_subject(INSIDE_CLIENT)
        mail_service = build('gmail', 'v1', credentials = credentials_delegated)
        # 02. 문서 삭제
        drive_response = drive_service.files().delete(
            fileId = file_id,
        ).execute()
        if doc.submit_flag == True:
            # 03. 메일 생성
            sender = doc.box.writer.email.replace('@bluemove.or.kr', '') + ' at Bluemove ' + '<' + doc.box.writer.email + '>' ##### INSIDE 클라이언트 이메일 주소 INPUT #####
            to = doc.user.email ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
            subject = doc.user.last_name + doc.user.first_name + '님의 문서가 삭제 및 접수 취소되었습니다.' ##### 문서명 INPUT #####
            message_text = \
                """
                <!doctype html>
                <html
                    xmlns="http://www.w3.org/1999/xhtml"
                    xmlns:v="urn:schemas-microsoft-com:vml"
                    xmlns:o="urn:schemas-microsoft-com:office:office">
                    <head>
                        <!-- NAME: 1 COLUMN -->
                        <!--[if gte mso 15]> <xml> <o:OfficeDocumentSettings> <o:AllowPNG/>
                        <o:PixelsPerInch>96</o:PixelsPerInch> </o:OfficeDocumentSettings> </xml>
                        <![endif]-->
                        <meta charset="UTF-8">
                        <meta http-equiv="X-UA-Compatible" content="IE=edge">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <title>블루무브 닥스 - """ + doc.user.last_name + doc.user.first_name + """님의 문서가 삭제 및 접수 취소되었습니다.</title>
                    </head>
                    <body>
                        <center>
                            <table
                                align="center"
                                border="0"
                                cellpadding="0"
                                cellspacing="0"
                                height="100%"
                                width="100%"
                                id="bodyTable">
                                <tr>
                                    <td align="center" valign="top" id="bodyCell">
                                        <!-- BEGIN TEMPLATE // -->
                                        <table align="center" border="0" cellspacing="0"
                                        cellpadding="0" width="600" style="width:600px;"> <tr> <td align="center"
                                        valign="top" width="600" style="width:600px;">
                                        <table
                                            border="0"
                                            cellpadding="0"
                                            cellspacing="0"
                                            width="100%"
                                            class="templateContainer">
                                            <tr>
                                                <td valign="top" id="templatePreheader"></td>
                                            </tr>
                                            <tr>
                                                <td valign="top" id="templateHeader">
                                                    <table
                                                        border="0"
                                                        cellpadding="0"
                                                        cellspacing="0"
                                                        width="100%"
                                                        class="mcnImageBlock"
                                                        style="min-width:100%;">
                                                        <tbody class="mcnImageBlockOuter">
                                                            <tr>
                                                                <td valign="top" style="padding:9px" class="mcnImageBlockInner">
                                                                    <table
                                                                        align="left"
                                                                        width="100%"
                                                                        border="0"
                                                                        cellpadding="0"
                                                                        cellspacing="0"
                                                                        class="mcnImageContentContainer"
                                                                        style="min-width:100%;">
                                                                        <tbody>
                                                                            <tr>
                                                                                <td
                                                                                    class="mcnImageContent"
                                                                                    valign="top"
                                                                                    style="padding-right: 9px; padding-left: 9px; padding-top: 0; padding-bottom: 0;">
                                                                                    <img
                                                                                        align="left"
                                                                                        src="https://mcusercontent.com/8e85249d3fe980e2482c148b1/images/725d4688-6ae7-4f5d-8891-9c0796a9ebf4.png"
                                                                                        width="110"
                                                                                        style="max-width:1000px; padding-bottom: 0; display: inline !important; vertical-align: bottom;"
                                                                                        class="mcnRetinaImage">
                                                                                </td>
                                                                            </tr>
                                                                        </tbody>
                                                                    </table>
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td valign="top" id="templateBody">
                                                    <table
                                                        border="0"
                                                        cellpadding="0"
                                                        cellspacing="0"
                                                        width="100%"
                                                        class="mcnTextBlock"
                                                        style="min-width:100%;">
                                                        <tbody class="mcnTextBlockOuter">
                                                            <tr>
                                                                <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                    <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                    width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                    <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                    <table
                                                                        align="left"
                                                                        border="0"
                                                                        cellpadding="0"
                                                                        cellspacing="0"
                                                                        style="max-width:100%; min-width:100%;"
                                                                        width="100%"
                                                                        class="mcnTextContentContainer">
                                                                        <tbody>
                                                                            <tr>
                                                                                <td
                                                                                    valign="top"
                                                                                    class="mcnTextContent"
                                                                                    style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">
                                                                                    <h1>""" + doc.user.last_name + doc.user.first_name + """님의 문서가 삭제 및 접수 취소되었습니다.</h1>
                                                                                    <p>안녕하세요, 블루무브 """ + doc.box.writer.last_name + doc.box.writer.first_name + """입니다.<br>
                                                                                        """ + doc.user.last_name + doc.user.first_name + """님의 문서가 아래와 같이 삭제 및 접수 취소되었습니다.</p>
                                                                                </td>
                                                                            </tr>
                                                                        </tbody>
                                                                    </table>
                                                                    <!--[if mso]> </td> <![endif]-->

                                                                    <!--[if mso]> </tr> </table> <![endif]-->
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>

                                                    <table
                                                        border="0"
                                                        cellpadding="0"
                                                        cellspacing="0"
                                                        width="100%"
                                                        class="mcnBoxedTextBlock"
                                                        style="min-width:100%;">
                                                        <!--[if gte mso 9]> <table align="center" border="0" cellspacing="0"
                                                        cellpadding="0" width="100%"> <![endif]-->
                                                        <tbody class="mcnBoxedTextBlockOuter">
                                                            <tr>
                                                                <td valign="top" class="mcnBoxedTextBlockInner">

                                                                    <!--[if gte mso 9]> <td align="center" valign="top" "> <![endif]-->
                                                                    <table
                                                                        align="left"
                                                                        border="0"
                                                                        cellpadding="0"
                                                                        cellspacing="0"
                                                                        width="100%"
                                                                        style="min-width:100%;"
                                                                        class="mcnBoxedTextContentContainer">
                                                                        <tbody>
                                                                            <tr>

                                                                                <td
                                                                                    style="padding-top:9px; padding-left:18px; padding-bottom:9px; padding-right:18px;">

                                                                                    <table
                                                                                        border="0"
                                                                                        cellspacing="0"
                                                                                        class="mcnTextContentContainer"
                                                                                        width="100%"
                                                                                        style="min-width: 100% !important;background-color: #F7F7F7;">
                                                                                        <tbody>
                                                                                            <tr>
                                                                                                <td
                                                                                                    valign="top"
                                                                                                    class="mcnTextContent"
                                                                                                    style="padding: 18px;color: #58595B;font-family: Helvetica;font-size: 14px;font-weight: normal;">
                                                                                                    <strong style="color:#222222;">문서명</strong>: """ + doc.box.title + """<br>
                                                                                                    <strong style="color:#222222;">Google 계정</strong>: """ + doc.user.email + """<br>
                                                                                                    <strong style="color:#222222;">생성일자</strong>: """ + doc.creation_date + """<br>
                                                                                                    <strong style="color:#222222;">제출일자</strong>: """ + doc.submission_date + """<br>
                                                                                                    <strong style="color:#222222;">삭제일자(접수 취소일자)</strong>: """ + datetime.date.today().strftime('%Y-%m-%d') + """
                                                                                                </td>
                                                                                            </tr>
                                                                                        </tbody>
                                                                                    </table>
                                                                                </td>
                                                                            </tr>
                                                                        </tbody>
                                                                    </table>
                                                                    <!--[if gte mso 9]> </td> <![endif]-->

                                                                    <!--[if gte mso 9]> </tr> </table> <![endif]-->
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                    <table
                                                        border="0"
                                                        cellpadding="0"
                                                        cellspacing="0"
                                                        width="100%"
                                                        class="mcnTextBlock"
                                                        style="min-width:100%;">
                                                        <tbody class="mcnTextBlockOuter">
                                                            <tr>
                                                                <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                    <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                    width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                    <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                    <table
                                                                        align="left"
                                                                        border="0"
                                                                        cellpadding="0"
                                                                        cellspacing="0"
                                                                        style="max-width:100%; min-width:100%;"
                                                                        width="100%"
                                                                        class="mcnTextContentContainer">
                                                                        <tbody>
                                                                            <tr>

                                                                                <td
                                                                                    valign="top"
                                                                                    class="mcnTextContent"
                                                                                    style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">

                                                                                    """ + doc.user.last_name + doc.user.first_name + """님의 요청에 의해 이미 접수된 문서가 삭제되어 자동으로 접수 취소되었습니다.<br>
                                                                                    다시 제출하시려면 새 문서를 생성하시기 바랍니다.<br>
                                                                                    감사합니다.<br><br>
                                                                                </td>
                                                                            </tr>
                                                                        </tbody>
                                                                    </table>
                                                                    <!--[if mso]> </td> <![endif]-->

                                                                    <!--[if mso]> </tr> </table> <![endif]-->
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                    <table
                                                        border="0"
                                                        cellpadding="0"
                                                        cellspacing="0"
                                                        width="100%"
                                                        class="mcnButtonBlock"
                                                        style="min-width:100%;">
                                                        <tbody class="mcnButtonBlockOuter">
                                                            <tr>
                                                                <td
                                                                    style="padding-top:0; padding-right:18px; padding-bottom:18px; padding-left:18px;"
                                                                    valign="top"
                                                                    align="center"
                                                                    class="mcnButtonBlockInner">
                                                                    <a
                                                                        href="http://127.0.0.1:8000/"
                                                                        target="_blank"
                                                                        style="text-decoration:none;">
                                                                        <table
                                                                            border="0"
                                                                            cellpadding="0"
                                                                            cellspacing="0"
                                                                            width="100%"
                                                                            class="mcnButtonContentContainer"
                                                                            style="border-collapse: separate !important;border-radius: 4px;background-color: #007DC5;">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td
                                                                                        align="center"
                                                                                        valign="middle"
                                                                                        class="mcnButtonContent"
                                                                                        style="font-family: Arial; font-size: 16px; padding-left: 12px; padding-top: 8px; padding-bottom: 8px; padding-right: 12px;">
                                                                                        <a
                                                                                            class="mcnButton"
                                                                                            title="블루무브 닥스 열기"
                                                                                            href="http://127.0.0.1:8000/"
                                                                                            target="_blank"
                                                                                            style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">블루무브 닥스 열기</a>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </a>
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td valign="top" id="templateFooter">
                                                    <table
                                                        border="0"
                                                        cellpadding="0"
                                                        cellspacing="0"
                                                        width="100%"
                                                        class="mcnTextBlock"
                                                        style="min-width:100%;">
                                                        <tbody class="mcnTextBlockOuter">
                                                            <tr>
                                                                <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                    <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                    width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                    <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                    <table
                                                                        align="left"
                                                                        border="0"
                                                                        cellpadding="0"
                                                                        cellspacing="0"
                                                                        style="max-width:100%; min-width:100%;"
                                                                        width="100%"
                                                                        class="mcnTextContentContainer">
                                                                        <tbody>
                                                                            <tr>

                                                                                <td
                                                                                    valign="top"
                                                                                    class="mcnTextContent"
                                                                                    style="padding: 0px 18px 9px; text-align: left;">
                                                                                    <hr style="border:0;height:.5px;background-color:#EEEEEE;">
                                                                                    <small style="color: #58595B;">
                                                                                        이 메일은 블루무브 닥스를 통해 자동 발신되었습니다. 궁금하신 점이 있을 경우 이 주소로 회신해주시거나 사무국 연락처로 문의해주시기 바랍니다.<br>
                                                                                        ⓒ 파란물결 블루무브
                                                                                    </small>
                                                                                </td>
                                                                            </tr>
                                                                        </tbody>
                                                                    </table>
                                                                    <!--[if mso]> </td> <![endif]-->

                                                                    <!--[if mso]> </tr> </table> <![endif]-->
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                        </td> </tr> </table>
                                        <!-- // END TEMPLATE -->
                                    </td>
                                </tr>
                            </table>
                        </center>
                    </body>
                </html>
                """
            message = MIMEText(message_text, 'html')
            message['from'] = sender
            message['to'] = to
            message['subject'] = subject
            message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')}
            # 04. 메일 발신
            message = (
                mail_service.users().messages().send(
                    userId = user_id,
                    body = message,
                ).execute()
            )
            # message_id = message['id']
            # 05. 슬랙 메시지 수정
            client = WebClient(token=slack_bot_token)
            client.chat_update(
                channel=doc.box.channel_id,
                link_names=True,
                ts=doc.slack_ts,
                blocks=[
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📩 " + doc.user.last_name + doc.user.first_name + "님의 문서가 접수되었습니다.",
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*`" + datetime.date.today().strftime('%Y-%m-%d') + " 업데이트:`*\n`" + doc.user.last_name + doc.user.first_name + "님이 문서 제출을 포기하여 자동으로 접수 취소되었습니다.`\n`더 이상 이 문서에 액세스할 수 없습니다.`" + "\n\n~<@" + doc.box.writer.email.replace('@bluemove.or.kr', '').lower() + ">님, " + doc.user.last_name + doc.user.first_name + "님이 제출한 문서를 확인하세요.~\n\n~*<https://docs.google.com/document/d/" + doc.file_id + "|" + doc.name + ">*~"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*~문서명:~*\n~" + doc.box.title + "~\n\n*~Google 계정:~*\n~" +  doc.user.email + "~\n\n*~제출일자:~*\n~" + doc.submission_date + "~"
                        },
                        "accessory": {
                            "type": "image",
                            "image_url": doc.avatar_src,
                            "alt_text": doc.user.last_name + doc.user.first_name + "님의 프로필 사진"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "문서함 열기"
                                },
                                "value": "open_box",
                                "url": "http://127.0.0.1:8000/box/" + str(doc.box.id) + "/#docPosition"
                            }
                        ]
                    }
                ],
                text=f"📩 " + doc.user.last_name + doc.user.first_name + "님의 문서가 접수되었습니다.",
            )
            # 06. 슬랙 메시지 발신
            try:
                client.conversations_join(
                    channel = doc.box.channel_id
                )
            except:
                None
            client.chat_postMessage(
                channel = doc.box.channel_id,
                link_names = True,
                blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "💥 " + doc.user.last_name + doc.user.first_name + "님의 문서가 접수 취소되었습니다.",
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "<@" + doc.box.writer.email.replace('@bluemove.or.kr', '').lower() + ">님, " + doc.user.last_name + doc.user.first_name + "님이 문서 제출을 포기하였습니다.\n더 이상 이 문서에 액세스할 수 없습니다.\n\n*" + doc.name + "*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*문서명:*\n" + doc.box.title + "\n\n*Google 계정:*\n" +  doc.user.email + "\n\n*제출일자:*\n" +  doc.submission_date + "\n\n*접수 취소일자:*\n" + datetime.date.today().strftime('%Y-%m-%d')
                        },
                        "accessory": {
                            "type": "image",
                            "image_url": doc.avatar_src,
                            "alt_text": doc.user.last_name + doc.user.first_name + "님의 프로필 사진"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "문서함 열기"
                                },
                                "value": "open_box",
                                "url": "http://127.0.0.1:8000/box/" + str(doc.box.id) + "/#docPosition"
                            }
                        ]
                    }
                ],
                text = f"💥 " + doc.user.last_name + doc.user.first_name + "님의 문서가 접수 취소되었습니다.",
            )
        # 07. 문서 데이터 DB 반영
        doc.delete()
        return redirect('box:read', id=doc.box.id)


@login_required
def submit_doc(request, doc_id):
    doc = get_object_or_404(Doc, pk=doc_id)
    file_id = doc.file_id
    outside_permission_id = doc.outside_permission_id
    # 00. 기한 초과 시 새로고침
    if doc.box.deadline_is_over :
        return redirect('box:read', doc.box.id)
    ###############################################
    ##### OUTSIDE 클라이언트가 bluemover일 경우 #####
    ###############################################
    if doc.user.profile.level == 'bluemover':
        # 01. OUTSIDE 클라이언트 Google Drive, 서비스 계정 Gmail API 호출
        token = SocialToken.objects.get(account__user=request.user, account__provider='google')
        credentials = Credentials(
            client_id=client_id,
            client_secret=client_secret,
            token_uri='https://oauth2.googleapis.com/token',
            token=token.token,
            refresh_token=token.token_secret,
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        INSIDE_CLIENT = doc.box.writer.email
        user_id = doc.box.writer.email
        SERVICE_ACCOUNT_GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        gmail_credentials = service_account.Credentials.from_service_account_file(
            'bluemove-docs-6a11a86cda0e.json',
            scopes = SERVICE_ACCOUNT_GMAIL_SCOPES,
        )
        credentials_delegated = gmail_credentials.with_subject(INSIDE_CLIENT)
        mail_service = build('gmail', 'v1', credentials = credentials_delegated)
        # 02. 문서 잠금 해제
        drive_response = drive_service.files().update(
            fileId=file_id,
            body={
                "contentRestrictions": [
                    {
                        "readOnly": "false",
                    }
                ]
            }
        ).execute()
        # 03. 문서명 및 설명 변경
        drive_response = drive_service.files().update(
            fileId = file_id,
            body = {
                'name': doc.box.prefix + '_' + ##### 파일 프리픽스 INPUT #####
                        doc.box.title.replace(" ","") + ##### 문서명 INPUT #####
                        doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                        '_' + datetime.date.today().strftime('%y%m%d'),
                'description': '블루무브 닥스에서 생성된 ' +
                            doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                            '님의 ' +
                            doc.box.title ##### 문서명 INPUT #####
                            + '입니다.\n\n' +
                            '📧 생성일자: ' + doc.creation_date + '\n' + ##### 문서 생성일자 INPUT #####
                            '📨 제출일자: ' + datetime.date.today().strftime('%Y-%m-%d'), ##### 현재 일자 INPUT #####
            },
            fields = 'name'
        ).execute()
        name = drive_response.get('name') ##### 파일 최종 이름 OUTPUT #####
        # 04. INSIDE 클라이언트 권한 추가 owner
        drive_response = drive_service.permissions().create(
            fileId = file_id,
            transferOwnership = True,
            moveToNewOwnersRoot = True,
            body = {
                'type': 'user',
                'role': 'owner',
                'emailAddress': doc.box.writer.email, ##### INSIDE 클라이언트 이메일 주소 INPUT #####
            },
        ).execute()
        inside_permission_id = drive_response.get('id') ##### INSIDE 클라이언트 권한 ID OUTPUT #####
        # 05. 문서 잠금
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
        # 06. OUTSIDE 클라이언트 권한 변경 writer 2 reader
        drive_response = drive_service.permissions().update(
            fileId = file_id,
            permissionId = outside_permission_id,
            body = {
                'role': 'reader',
            },
        ).execute()
        # 07. 문서 데이터 DB 반영
        doc.name = name
        doc.submission_date = datetime.date.today().strftime('%Y-%m-%d')
        doc.inside_permission_id = inside_permission_id
        doc.submit_flag = True
        doc.reject_flag = False
        doc.save()
        # 08. 메일 생성
        sender = doc.box.writer.email.replace('@bluemove.or.kr', '').capitalize() + ' at Bluemove ' + '<' + doc.box.writer.email + '>' ##### INSIDE 클라이언트 이메일 주소 INPUT #####
        to = doc.user.email ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
        subject = doc.user.last_name + doc.user.first_name + '님의 문서가 접수되었습니다.' ##### 문서명 INPUT #####
        message_text = \
            """
            <!doctype html>
            <html
                xmlns="http://www.w3.org/1999/xhtml"
                xmlns:v="urn:schemas-microsoft-com:vml"
                xmlns:o="urn:schemas-microsoft-com:office:office">
                <head>
                    <!-- NAME: 1 COLUMN -->
                    <!--[if gte mso 15]> <xml> <o:OfficeDocumentSettings> <o:AllowPNG/>
                    <o:PixelsPerInch>96</o:PixelsPerInch> </o:OfficeDocumentSettings> </xml>
                    <![endif]-->
                    <meta charset="UTF-8">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>블루무브 닥스 - """ + doc.user.last_name + doc.user.first_name + """님의 문서가 접수되었습니다.</title>
                </head>
                <body>
                    <center>
                        <table
                            align="center"
                            border="0"
                            cellpadding="0"
                            cellspacing="0"
                            height="100%"
                            width="100%"
                            id="bodyTable">
                            <tr>
                                <td align="center" valign="top" id="bodyCell">
                                    <!-- BEGIN TEMPLATE // -->
                                    <table align="center" border="0" cellspacing="0"
                                    cellpadding="0" width="600" style="width:600px;"> <tr> <td align="center"
                                    valign="top" width="600" style="width:600px;">
                                    <table
                                        border="0"
                                        cellpadding="0"
                                        cellspacing="0"
                                        width="100%"
                                        class="templateContainer">
                                        <tr>
                                            <td valign="top" id="templatePreheader"></td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateHeader">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnImageBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnImageBlockOuter">
                                                        <tr>
                                                            <td valign="top" style="padding:9px" class="mcnImageBlockInner">
                                                                <table
                                                                    align="left"
                                                                    width="100%"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    class="mcnImageContentContainer"
                                                                    style="min-width:100%;">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                class="mcnImageContent"
                                                                                valign="top"
                                                                                style="padding-right: 9px; padding-left: 9px; padding-top: 0; padding-bottom: 0;">
                                                                                <img
                                                                                    align="left"
                                                                                    src="https://mcusercontent.com/8e85249d3fe980e2482c148b1/images/725d4688-6ae7-4f5d-8891-9c0796a9ebf4.png"
                                                                                    width="110"
                                                                                    style="max-width:1000px; padding-bottom: 0; display: inline !important; vertical-align: bottom;"
                                                                                    class="mcnRetinaImage">
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateBody">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">
                                                                                <h1>""" + doc.user.last_name + doc.user.first_name + """님의 문서가 접수되었습니다.</h1>
                                                                                <p>안녕하세요, 블루무브 """ + doc.box.writer.last_name + doc.box.writer.first_name + """입니다.<br>
                                                                                    """ + doc.user.last_name + doc.user.first_name + """님의 문서가 아래와 같이 접수되었습니다.</p>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>

                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnBoxedTextBlock"
                                                    style="min-width:100%;">
                                                    <!--[if gte mso 9]> <table align="center" border="0" cellspacing="0"
                                                    cellpadding="0" width="100%"> <![endif]-->
                                                    <tbody class="mcnBoxedTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnBoxedTextBlockInner">

                                                                <!--[if gte mso 9]> <td align="center" valign="top" "> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    width="100%"
                                                                    style="min-width:100%;"
                                                                    class="mcnBoxedTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                style="padding-top:9px; padding-left:18px; padding-bottom:9px; padding-right:18px;">

                                                                                <table
                                                                                    border="0"
                                                                                    cellspacing="0"
                                                                                    class="mcnTextContentContainer"
                                                                                    width="100%"
                                                                                    style="min-width: 100% !important;background-color: #F7F7F7;">
                                                                                    <tbody>
                                                                                        <tr>
                                                                                            <td
                                                                                                valign="top"
                                                                                                class="mcnTextContent"
                                                                                                style="padding: 18px;color: #58595B;font-family: Helvetica;font-size: 14px;font-weight: normal;">
                                                                                                <strong style="color:#222222;">문서명</strong>: """ + doc.box.title + """<br>
                                                                                                <strong style="color:#222222;">블루무버 계정</strong>: """ + doc.user.email + """<br>
                                                                                                <strong style="color:#222222;">생성일자</strong>: """ + doc.creation_date + """<br>
                                                                                                <strong style="color:#222222;">제출일자</strong>: """ + doc.submission_date + """
                                                                                            </td>
                                                                                        </tr>
                                                                                    </tbody>
                                                                                </table>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if gte mso 9]> </td> <![endif]-->

                                                                <!--[if gte mso 9]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">

                                                                                블루무브 닥스 문서함에서 문서를 조회할 수 있습니다.<br>
                                                                                문서 검토가 완료되면 다시 연락드리겠습니다.<br>
                                                                                감사합니다.<br><br>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnButtonBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnButtonBlockOuter">
                                                        <tr>
                                                            <td
                                                                style="padding-top:0; padding-right:18px; padding-bottom:18px; padding-left:18px;"
                                                                valign="top"
                                                                align="center"
                                                                class="mcnButtonBlockInner">
                                                                <a
                                                                    href="http://127.0.0.1:8000/box/""" + str(doc.box.id) + """/"
                                                                    target="_blank"
                                                                    style="text-decoration:none;">
                                                                    <table
                                                                        border="0"
                                                                        cellpadding="0"
                                                                        cellspacing="0"
                                                                        width="100%"
                                                                        class="mcnButtonContentContainer"
                                                                        style="border-collapse: separate !important;border-radius: 4px;background-color: #007DC5;">
                                                                        <tbody>
                                                                            <tr>
                                                                                <td
                                                                                    align="center"
                                                                                    valign="middle"
                                                                                    class="mcnButtonContent"
                                                                                    style="font-family: Arial; font-size: 16px; padding-left: 12px; padding-top: 8px; padding-bottom: 8px; padding-right: 12px;">
                                                                                    <a
                                                                                        class="mcnButton"
                                                                                        title="블루무브 닥스 문서함 열기"
                                                                                        href="http://127.0.0.1:8000/box/""" + str(doc.box.id) + """/"
                                                                                        target="_blank"
                                                                                        style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">블루무브 닥스 문서함 열기</a>
                                                                                </td>
                                                                            </tr>
                                                                        </tbody>
                                                                    </table>
                                                                </a>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateFooter">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding: 0px 18px 9px; text-align: left;">
                                                                                <hr style="border:0;height:.5px;background-color:#EEEEEE;">
                                                                                <small style="color: #58595B;">
                                                                                    이 메일은 블루무브 닥스를 통해 자동 발신되었습니다.<br>
                                                                                    ⓒ 파란물결 블루무브
                                                                                </small>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    </td> </tr> </table>
                                    <!-- // END TEMPLATE -->
                                </td>
                            </tr>
                        </table>
                    </center>
                </body>
            </html>
            """
        message = MIMEText(message_text, 'html')
        message['from'] = sender
        message['to'] = to
        message['subject'] = subject
        message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')}
        # 09. 메일 발신
        message = (
            mail_service.users().messages().send(
                userId = user_id,
                body = message,
            ).execute()
        )
        # message_id = message['id']
        # 10. 슬랙 메시지 발신
        client = WebClient(token=slack_bot_token)
        try:
            client.conversations_join(
                channel = doc.box.channel_id
            )
        except:
            None
        slack = client.chat_postMessage(
            channel = doc.box.channel_id,
            link_names = True,
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📩 " + doc.user.last_name + doc.user.first_name + "님의 문서가 접수되었습니다.",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<@" + doc.box.writer.email.replace('@bluemove.or.kr', '').lower() + ">님, " + doc.user.last_name + doc.user.first_name + "님이 제출한 문서를 확인하세요.\n\n*<https://docs.google.com/document/d/" + doc.file_id + "|" + doc.name + ">*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*문서명:*\n" + doc.box.title + "\n\n*블루무버 계정:*\n" +  doc.user.email + "\n\n*생성일자:*\n" + doc.creation_date + "\n\n*제출일자:*\n" + doc.submission_date
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": doc.avatar_src,
                        "alt_text": doc.user.last_name + doc.user.first_name + "님의 프로필 사진"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "문서함 열기"
                            },
                            "value": "open_box",
                            "url": "http://127.0.0.1:8000/box/" + str(doc.box.id) + "/#docPosition"
                        }
                    ]
                }
            ],
            text = f"📩 " + doc.user.last_name + doc.user.first_name + "님의 문서가 접수되었습니다.",
        )
        doc.slack_ts = slack['ts']
        # 11. OUTSIDE 클라이언트 슬랙 메시지 발신
        client.chat_postMessage(
            channel = doc.user.profile.slack_user_id,
            link_names = True,
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📨 " + doc.user.last_name + doc.user.first_name + "님의 문서가 제출되었습니다.",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<@" + doc.user.email.replace('@bluemove.or.kr', '').lower() + ">님의 문서가 아래와 같이 제출되었습니다.\n\n*<https://docs.google.com/document/d/" + doc.file_id + "|" + doc.name + ">*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*문서명:*\n" + doc.box.title + "\n\n*블루무버 계정:*\n" +  doc.user.email + "\n\n*생성일자:*\n" + doc.creation_date + "\n\n*제출일자:*\n" + doc.submission_date
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": doc.avatar_src,
                        "alt_text": doc.user.last_name + doc.user.first_name + "님의 프로필 사진"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "문서함 열기"
                            },
                            "value": "open_box",
                            "url": "http://127.0.0.1:8000/box/" + str(doc.box.id) + "/#docPosition"
                        }
                    ]
                }
            ],
            text = f"📨 " + doc.user.last_name + doc.user.first_name + "님의 문서가 제출되었습니다.",
        )
        doc.save()
        return redirect('box:read', id=doc.box.id)
    ###########################################
    ##### OUTSIDE 클라이언트가 guest일 경우 #####
    ###########################################
    if doc.user.profile.level == 'guest':
        # 01. 서비스 계정 Google Drive, Gmail API 호출
        SERVICE_ACCOUNT_SCOPES = ['https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name (
            'bluemove-docs-6a11a86cda0e.json',
            SERVICE_ACCOUNT_SCOPES,
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        INSIDE_CLIENT = doc.box.writer.email
        user_id = doc.box.writer.email
        SERVICE_ACCOUNT_GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        gmail_credentials = service_account.Credentials.from_service_account_file(
            'bluemove-docs-6a11a86cda0e.json',
            scopes = SERVICE_ACCOUNT_GMAIL_SCOPES,
        )
        credentials_delegated = gmail_credentials.with_subject(INSIDE_CLIENT)
        mail_service = build('gmail', 'v1', credentials = credentials_delegated)
        # 02. 문서 잠금 해제
        drive_response = drive_service.files().update(
            fileId=file_id,
            body={
                "contentRestrictions": [
                    {
                        "readOnly": "false",
                    }
                ]
            }
        ).execute()
        # 03. OUTSIDE 클라이언트 권한 변경 writer 2 reader
        drive_response = drive_service.permissions().update(
            fileId = file_id,
            permissionId = outside_permission_id,
            body = {
                'role': 'reader',
            },
        ).execute()
        # 04. 문서명 및 설명 변경
        drive_response = drive_service.files().update(
            fileId = file_id,
            body = {
                'name': '블루무브닥스_' +
                        doc.box.title.replace(" ","") + ##### 문서명 INPUT #####
                        doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                        '_' + datetime.date.today().strftime('%y%m%d'),
                'description': '블루무브 닥스에서 생성된 ' +
                            doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                            '님의 ' +
                            doc.box.title ##### 문서명 INPUT #####
                            + '입니다.\n\n' +
                            '📧 생성일자: ' + doc.creation_date + '\n' + ##### 문서 생성일자 INPUT #####
                            '📨 제출일자: ' + datetime.date.today().strftime('%Y-%m-%d'), ##### 현재 일자 INPUT #####
            },
            fields = 'name'
        ).execute()
        name = drive_response.get('name') ##### 파일 최종 이름 OUTPUT #####
        # 05. INSIDE 클라이언트 권한 추가 writer
        drive_response = drive_service.permissions().create(
            fileId = file_id,
            sendNotificationEmail = False,
            body = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': doc.box.writer.email, ##### INSIDE 클라이언트 이메일 주소 INPUT #####
            },
        ).execute()
        inside_permission_id = drive_response.get('id') ##### INSIDE 클라이언트 권한 ID OUTPUT #####
        # 06. 문서 잠금
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
        # 07. 문서 데이터 DB 반영
        doc.name = name
        doc.submission_date = datetime.date.today().strftime('%Y-%m-%d')
        doc.inside_permission_id = inside_permission_id
        doc.submit_flag = True
        doc.reject_flag = False
        doc.save()
        # 08. 메일 생성
        sender = doc.box.writer.email.replace('@bluemove.or.kr', '').capitalize() + ' at Bluemove ' + '<' + doc.box.writer.email + '>' ##### INSIDE 클라이언트 이메일 주소 INPUT #####
        to = doc.user.email ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
        subject = doc.user.last_name + doc.user.first_name + '님의 문서가 접수되었습니다.' ##### 문서명 INPUT #####
        message_text = \
            """
            <!doctype html>
            <html
                xmlns="http://www.w3.org/1999/xhtml"
                xmlns:v="urn:schemas-microsoft-com:vml"
                xmlns:o="urn:schemas-microsoft-com:office:office">
                <head>
                    <!-- NAME: 1 COLUMN -->
                    <!--[if gte mso 15]> <xml> <o:OfficeDocumentSettings> <o:AllowPNG/>
                    <o:PixelsPerInch>96</o:PixelsPerInch> </o:OfficeDocumentSettings> </xml>
                    <![endif]-->
                    <meta charset="UTF-8">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>블루무브 닥스 - """ + doc.user.last_name + doc.user.first_name + """님의 문서가 접수되었습니다.</title>
                </head>
                <body>
                    <center>
                        <table
                            align="center"
                            border="0"
                            cellpadding="0"
                            cellspacing="0"
                            height="100%"
                            width="100%"
                            id="bodyTable">
                            <tr>
                                <td align="center" valign="top" id="bodyCell">
                                    <!-- BEGIN TEMPLATE // -->
                                    <table align="center" border="0" cellspacing="0"
                                    cellpadding="0" width="600" style="width:600px;"> <tr> <td align="center"
                                    valign="top" width="600" style="width:600px;">
                                    <table
                                        border="0"
                                        cellpadding="0"
                                        cellspacing="0"
                                        width="100%"
                                        class="templateContainer">
                                        <tr>
                                            <td valign="top" id="templatePreheader"></td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateHeader">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnImageBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnImageBlockOuter">
                                                        <tr>
                                                            <td valign="top" style="padding:9px" class="mcnImageBlockInner">
                                                                <table
                                                                    align="left"
                                                                    width="100%"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    class="mcnImageContentContainer"
                                                                    style="min-width:100%;">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                class="mcnImageContent"
                                                                                valign="top"
                                                                                style="padding-right: 9px; padding-left: 9px; padding-top: 0; padding-bottom: 0;">
                                                                                <img
                                                                                    align="left"
                                                                                    src="https://mcusercontent.com/8e85249d3fe980e2482c148b1/images/725d4688-6ae7-4f5d-8891-9c0796a9ebf4.png"
                                                                                    width="110"
                                                                                    style="max-width:1000px; padding-bottom: 0; display: inline !important; vertical-align: bottom;"
                                                                                    class="mcnRetinaImage">
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateBody">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">
                                                                                <h1>""" + doc.user.last_name + doc.user.first_name + """님의 문서가 접수되었습니다.</h1>
                                                                                <p>안녕하세요, 블루무브 """ + doc.box.writer.last_name + doc.box.writer.first_name + """입니다.<br>
                                                                                    """ + doc.user.last_name + doc.user.first_name + """님의 문서가 아래와 같이 접수되었습니다.</p>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>

                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnBoxedTextBlock"
                                                    style="min-width:100%;">
                                                    <!--[if gte mso 9]> <table align="center" border="0" cellspacing="0"
                                                    cellpadding="0" width="100%"> <![endif]-->
                                                    <tbody class="mcnBoxedTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnBoxedTextBlockInner">

                                                                <!--[if gte mso 9]> <td align="center" valign="top" "> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    width="100%"
                                                                    style="min-width:100%;"
                                                                    class="mcnBoxedTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                style="padding-top:9px; padding-left:18px; padding-bottom:9px; padding-right:18px;">

                                                                                <table
                                                                                    border="0"
                                                                                    cellspacing="0"
                                                                                    class="mcnTextContentContainer"
                                                                                    width="100%"
                                                                                    style="min-width: 100% !important;background-color: #F7F7F7;">
                                                                                    <tbody>
                                                                                        <tr>
                                                                                            <td
                                                                                                valign="top"
                                                                                                class="mcnTextContent"
                                                                                                style="padding: 18px;color: #58595B;font-family: Helvetica;font-size: 14px;font-weight: normal;">
                                                                                                <strong style="color:#222222;">문서명</strong>: """ + doc.box.title + """<br>
                                                                                                <strong style="color:#222222;">Google 계정</strong>: """ + doc.user.email + """<br>
                                                                                                <strong style="color:#222222;">생성일자</strong>: """ + doc.creation_date + """<br>
                                                                                                <strong style="color:#222222;">제출일자</strong>: """ + doc.submission_date + """
                                                                                            </td>
                                                                                        </tr>
                                                                                    </tbody>
                                                                                </table>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if gte mso 9]> </td> <![endif]-->

                                                                <!--[if gte mso 9]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">

                                                                                블루무브 닥스 문서함에서 문서를 조회하거나 삭제할 수 있습니다.<br>
                                                                                문서 검토가 완료되면 다시 연락드리겠습니다.<br>
                                                                                감사합니다.<br><br>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnButtonBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnButtonBlockOuter">
                                                        <tr>
                                                            <td
                                                                style="padding-top:0; padding-right:18px; padding-bottom:18px; padding-left:18px;"
                                                                valign="top"
                                                                align="center"
                                                                class="mcnButtonBlockInner">
                                                                <a
                                                                    href="http://127.0.0.1:8000/box/""" + str(doc.box.id) + """/"
                                                                    target="_blank"
                                                                    style="text-decoration:none;">
                                                                    <table
                                                                        border="0"
                                                                        cellpadding="0"
                                                                        cellspacing="0"
                                                                        width="100%"
                                                                        class="mcnButtonContentContainer"
                                                                        style="border-collapse: separate !important;border-radius: 4px;background-color: #007DC5;">
                                                                        <tbody>
                                                                            <tr>
                                                                                <td
                                                                                    align="center"
                                                                                    valign="middle"
                                                                                    class="mcnButtonContent"
                                                                                    style="font-family: Arial; font-size: 16px; padding-left: 12px; padding-top: 8px; padding-bottom: 8px; padding-right: 12px;">
                                                                                    <a
                                                                                        class="mcnButton"
                                                                                        title="블루무브 닥스 문서함 열기"
                                                                                        href="http://127.0.0.1:8000/box/""" + str(doc.box.id) + """/"
                                                                                        target="_blank"
                                                                                        style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">블루무브 닥스 문서함 열기</a>
                                                                                </td>
                                                                            </tr>
                                                                        </tbody>
                                                                    </table>
                                                                </a>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateFooter">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding: 0px 18px 9px; text-align: left;">
                                                                                <hr style="border:0;height:.5px;background-color:#EEEEEE;">
                                                                                <small style="color: #58595B;">
                                                                                    이 메일은 블루무브 닥스를 통해 자동 발신되었습니다. 궁금하신 점이 있을 경우 이 주소로 회신해주시거나 사무국 연락처로 문의해주시기 바랍니다.<br>
                                                                                    ⓒ 파란물결 블루무브
                                                                                </small>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    </td> </tr> </table>
                                    <!-- // END TEMPLATE -->
                                </td>
                            </tr>
                        </table>
                    </center>
                </body>
            </html>
            """
        message = MIMEText(message_text, 'html')
        message['from'] = sender
        message['to'] = to
        message['subject'] = subject
        message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')}
        # 09. 메일 발신
        message = (
            mail_service.users().messages().send(
                userId = user_id,
                body = message,
            ).execute()
        )
        # message_id = message['id']
        # 10. 슬랙 메시지 발신
        client = WebClient(token=slack_bot_token)
        try:
            client.conversations_join(
                channel = doc.box.channel_id
            )
        except:
            None
        slack = client.chat_postMessage(
            channel = doc.box.channel_id,
            link_names = True,
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📩 " + doc.user.last_name + doc.user.first_name + "님의 문서가 접수되었습니다.",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<@" + doc.box.writer.email.replace('@bluemove.or.kr', '').lower() + ">님, " + doc.user.last_name + doc.user.first_name + "님이 제출한 문서를 확인하세요.\n\n*<https://docs.google.com/document/d/" + doc.file_id + "|" + doc.name + ">*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*문서명:*\n" + doc.box.title + "\n\n*Google 계정:*\n" +  doc.user.email + "\n\n*제출일자:*\n" + doc.submission_date
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": doc.avatar_src,
                        "alt_text": doc.user.last_name + doc.user.first_name + "님의 프로필 사진"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "문서함 열기"
                            },
                            "value": "open_box",
                            "url": "http://127.0.0.1:8000/box/" + str(doc.box.id) + "/#docPosition"
                        }
                    ]
                }
            ],
            text = f"📩 " + doc.user.last_name + doc.user.first_name + "님의 문서가 접수되었습니다.",
        )
        doc.slack_ts = slack['ts']
        doc.save()
        return redirect('box:read', id=doc.box.id)


@login_required
# @permission_required('auth.add_permission', raise_exception=True)
def reject_doc(request, doc_id):
    doc = get_object_or_404(Doc, pk=doc_id)
    file_id = doc.file_id
    inside_permission_id = doc.inside_permission_id
    outside_permission_id = doc.outside_permission_id
    ###################################
    ##### INSIDE 클라이언트일 경우 #####
    ###################################
    if doc.user.profile.level == 'bluemover':
        # 01. INSIDE 클라이언트 Google Drive, 서비스 계정 Gmail API 호출
        token = SocialToken.objects.get(account__user=request.user, account__provider='google')
        credentials = Credentials(
            client_id=client_id,
            client_secret=client_secret,
            token_uri='https://oauth2.googleapis.com/token',
            token=token.token,
            refresh_token=token.token_secret,
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        INSIDE_CLIENT = doc.box.writer.email
        user_id = doc.box.writer.email
        SERVICE_ACCOUNT_GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        gmail_credentials = service_account.Credentials.from_service_account_file(
            'bluemove-docs-6a11a86cda0e.json',
            scopes = SERVICE_ACCOUNT_GMAIL_SCOPES,
        )
        credentials_delegated = gmail_credentials.with_subject(INSIDE_CLIENT)
        mail_service = build('gmail', 'v1', credentials = credentials_delegated)
        # 02. 문서 잠금 해제
        drive_response = drive_service.files().update(
            fileId=file_id,
            body={
                "contentRestrictions": [
                    {
                        "readOnly": "false",
                    }
                ]
            }
        ).execute()
        # 03. 문서명 및 설명 변경
        drive_response = drive_service.files().update(
            fileId = file_id,
            body = {
                'name': doc.box.prefix + '_' + ##### 파일 프리픽스 INPUT #####
                        doc.box.title.replace(" ","") + ##### 문서명 INPUT #####
                        doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                        '_' + datetime.date.today().strftime('%y%m%d'),
                'description': '블루무브 닥스에서 생성된 ' +
                            doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                            '님의 ' +
                            doc.box.title ##### 문서명 INPUT #####
                            + '입니다.\n\n' +
                            '📧 생성일자: ' + doc.creation_date + '\n' + ##### 문서 생성일자 INPUT #####
                            '📨 제출일자: ' + doc.submission_date + '\n' + ##### 문서 제출일자 INPUT #####
                            '📩 반려일자: ' + datetime.date.today().strftime('%Y-%m-%d'), ##### 현재 일자 INPUT #####
            },
            fields = 'name'
        ).execute()
        name = drive_response.get('name') ##### 파일 최종 이름 OUTPUT #####
        # 04. 문서 잠금
        drive_response = drive_service.files().update(
            fileId=file_id,
            body={
                "contentRestrictions": [
                    {
                        "readOnly": "true",
                        "reason": "문서가 반려되었습니다. 내용 수정 방지를 위해 잠금 설정되었습니다."
                    }
                ]
            }
        ).execute()
        # 05. OUTSIDE 클라이언트 권한 변경 reader 2 owner
        drive_response = drive_service.permissions().update(
            fileId = file_id,
            permissionId = outside_permission_id,
            transferOwnership = True,
            body = {
                'role': 'owner',
            },
        ).execute()
        # 06. INSIDE 클라이언트 권한 삭제 owner 2 none
        drive_response = drive_service.permissions().delete(
            fileId = file_id,
            permissionId = inside_permission_id,
        ).execute()
        # 07. 문서 데이터 DB 반영
        doc.name = name
        doc.submit_flag = False
        doc.reject_flag = True
        doc.reject_reason = request.POST.get('reject_reason')
        doc.rejection_date = datetime.date.today().strftime('%Y-%m-%d')
        doc.save()
        # 08. 메일 생성
        sender = doc.box.writer.email.replace('@bluemove.or.kr', '').capitalize() + ' at Bluemove ' + '<' + doc.box.writer.email + '>' ##### INSIDE 클라이언트 이메일 주소 INPUT #####
        to = doc.user.email ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
        subject = doc.user.last_name + doc.user.first_name + '님의 문서가 반려되었습니다.' ##### 문서명 INPUT #####
        message_text = \
            """
            <!doctype html>
            <html
                xmlns="http://www.w3.org/1999/xhtml"
                xmlns:v="urn:schemas-microsoft-com:vml"
                xmlns:o="urn:schemas-microsoft-com:office:office">
                <head>
                    <!-- NAME: 1 COLUMN -->
                    <!--[if gte mso 15]> <xml> <o:OfficeDocumentSettings> <o:AllowPNG/>
                    <o:PixelsPerInch>96</o:PixelsPerInch> </o:OfficeDocumentSettings> </xml>
                    <![endif]-->
                    <meta charset="UTF-8">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>블루무브 닥스 - """ + doc.user.last_name + doc.user.first_name + """님의 문서가 반려되었습니다.</title>
                </head>
                <body>
                    <center>
                        <table
                            align="center"
                            border="0"
                            cellpadding="0"
                            cellspacing="0"
                            height="100%"
                            width="100%"
                            id="bodyTable">
                            <tr>
                                <td align="center" valign="top" id="bodyCell">
                                    <!-- BEGIN TEMPLATE // -->
                                    <table align="center" border="0" cellspacing="0"
                                    cellpadding="0" width="600" style="width:600px;"> <tr> <td align="center"
                                    valign="top" width="600" style="width:600px;">
                                    <table
                                        border="0"
                                        cellpadding="0"
                                        cellspacing="0"
                                        width="100%"
                                        class="templateContainer">
                                        <tr>
                                            <td valign="top" id="templatePreheader"></td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateHeader">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnImageBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnImageBlockOuter">
                                                        <tr>
                                                            <td valign="top" style="padding:9px" class="mcnImageBlockInner">
                                                                <table
                                                                    align="left"
                                                                    width="100%"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    class="mcnImageContentContainer"
                                                                    style="min-width:100%;">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                class="mcnImageContent"
                                                                                valign="top"
                                                                                style="padding-right: 9px; padding-left: 9px; padding-top: 0; padding-bottom: 0;">
                                                                                <img
                                                                                    align="left"
                                                                                    src="https://mcusercontent.com/8e85249d3fe980e2482c148b1/images/725d4688-6ae7-4f5d-8891-9c0796a9ebf4.png"
                                                                                    width="110"
                                                                                    style="max-width:1000px; padding-bottom: 0; display: inline !important; vertical-align: bottom;"
                                                                                    class="mcnRetinaImage">
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateBody">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">
                                                                                <h1>""" + doc.user.last_name + doc.user.first_name + """님의 문서가 반려되었습니다.</h1>
                                                                                <p>안녕하세요, 블루무브 """ + doc.box.writer.last_name + doc.box.writer.first_name + """입니다.<br>
                                                                                    """ + doc.user.last_name + doc.user.first_name + """님의 문서가 아래와 같이 반려되었습니다.</p>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>

                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnBoxedTextBlock"
                                                    style="min-width:100%;">
                                                    <!--[if gte mso 9]> <table align="center" border="0" cellspacing="0"
                                                    cellpadding="0" width="100%"> <![endif]-->
                                                    <tbody class="mcnBoxedTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnBoxedTextBlockInner">

                                                                <!--[if gte mso 9]> <td align="center" valign="top" "> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    width="100%"
                                                                    style="min-width:100%;"
                                                                    class="mcnBoxedTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                style="padding-top:9px; padding-left:18px; padding-bottom:9px; padding-right:18px;">

                                                                                <table
                                                                                    border="0"
                                                                                    cellspacing="0"
                                                                                    class="mcnTextContentContainer"
                                                                                    width="100%"
                                                                                    style="min-width: 100% !important;background-color: #F7F7F7;">
                                                                                    <tbody>
                                                                                        <tr>
                                                                                            <td
                                                                                                valign="top"
                                                                                                class="mcnTextContent"
                                                                                                style="padding: 18px;color: #58595B;font-family: Helvetica;font-size: 14px;font-weight: normal;">
                                                                                                <strong style="color:#222222;">문서명</strong>: """ + doc.box.title + """<br>
                                                                                                <strong style="color:#222222;">블루무버 계정</strong>: """ + doc.user.email + """<br>
                                                                                                <strong style="color:#222222;">생성일자</strong>: """ + doc.creation_date + """<br>
                                                                                                <strong style="color:#222222;">제출일자</strong>: """ + doc.submission_date + """<br>
                                                                                                <strong style="color:#222222;">반려일자</strong>: """ + doc.rejection_date + """<br>
                                                                                                <strong style="color:#222222;">반려 사유</strong>: """ + doc.reject_reason + """
                                                                                            </td>
                                                                                        </tr>
                                                                                    </tbody>
                                                                                </table>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if gte mso 9]> </td> <![endif]-->

                                                                <!--[if gte mso 9]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">

                                                                                블루무브 닥스 문서함에서 문서를 수정하거나 삭제할 수 있습니다.<br>
                                                                                반려 사유를 해소하여 """ + doc.box.deadline.strftime('%Y-%m-%d') + """ 이내에 다시 제출해주시기 바랍니다.<br>
                                                                                감사합니다.<br><br>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnButtonBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnButtonBlockOuter">
                                                        <tr>
                                                            <td
                                                                style="padding-top:0; padding-right:18px; padding-bottom:18px; padding-left:18px;"
                                                                valign="top"
                                                                align="center"
                                                                class="mcnButtonBlockInner">
                                                                <a
                                                                    href="http://127.0.0.1:8000/box/""" + str(doc.box.id) + """/"
                                                                    target="_blank"
                                                                    style="text-decoration:none;">
                                                                    <table
                                                                        border="0"
                                                                        cellpadding="0"
                                                                        cellspacing="0"
                                                                        width="100%"
                                                                        class="mcnButtonContentContainer"
                                                                        style="border-collapse: separate !important;border-radius: 4px;background-color: #007DC5;">
                                                                        <tbody>
                                                                            <tr>
                                                                                <td
                                                                                    align="center"
                                                                                    valign="middle"
                                                                                    class="mcnButtonContent"
                                                                                    style="font-family: Arial; font-size: 16px; padding-left: 12px; padding-top: 8px; padding-bottom: 8px; padding-right: 12px;">
                                                                                    <a
                                                                                        class="mcnButton"
                                                                                        title="블루무브 닥스 문서함 열기"
                                                                                        href="http://127.0.0.1:8000/box/""" + str(doc.box.id) + """/"
                                                                                        target="_blank"
                                                                                        style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">블루무브 닥스 문서함 열기</a>
                                                                                </td>
                                                                            </tr>
                                                                        </tbody>
                                                                    </table>
                                                                </a>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateFooter">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding: 0px 18px 9px; text-align: left;">
                                                                                <hr style="border:0;height:.5px;background-color:#EEEEEE;">
                                                                                <small style="color: #58595B;">
                                                                                    이 메일은 블루무브 닥스를 통해 자동 발신되었습니다.<br>
                                                                                    ⓒ 파란물결 블루무브
                                                                                </small>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    </td> </tr> </table>
                                    <!-- // END TEMPLATE -->
                                </td>
                            </tr>
                        </table>
                    </center>
                </body>
            </html>
            """
        message = MIMEText(message_text, 'html')
        message['from'] = sender
        message['to'] = to
        message['subject'] = subject
        message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')}
        # 09. 메일 발신
        message = (
            mail_service.users().messages().send(
                userId = user_id,
                body = message,
            ).execute()
        )
        # message_id = message['id']
        # 10. 슬랙 메시지 발신
        client = WebClient(token=slack_bot_token)
        try:
            client.conversations_join(
                channel = doc.box.channel_id
            )
        except:
            None
        slack = client.chat_postMessage(
            channel = doc.box.channel_id,
            link_names = True,
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📨 " + doc.user.last_name + doc.user.first_name + "님의 문서가 반려되었습니다.",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<@" + doc.box.writer.email.replace('@bluemove.or.kr', '').lower() + ">님이 " + doc.user.last_name + doc.user.first_name + "님의 문서를 아래와 같이 반려했습니다.\n\n*<https://docs.google.com/document/d/" + doc.file_id + "|" + doc.name + ">*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*문서명:*\n" + doc.box.title + "\n\n*블루무버 계정:*\n" +  doc.user.email + "\n\n*생성일자:*\n" + doc.creation_date + "\n\n*제출일자:*\n" + doc.submission_date + "\n\n*반려일자:*\n" + doc.rejection_date + "\n\n*반려 사유:*\n" + doc.reject_reason
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": doc.avatar_src,
                        "alt_text": doc.user.last_name + doc.user.first_name + "님의 프로필 사진"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "문서함 열기"
                            },
                            "value": "open_box",
                            "url": "http://127.0.0.1:8000/box/" + str(doc.box.id) + "/#docPosition"
                        }
                    ]
                }
            ],
            text = f"📨 " + doc.user.last_name + doc.user.first_name + "님의 문서가 반려되었습니다.",
        )
        doc.slack_ts = slack['ts']
        # 11. OUTSIDE 클라이언트 슬랙 메시지 발신
        client.chat_postMessage(
            channel = doc.user.profile.slack_user_id,
            link_names = True,
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📩 " + doc.user.last_name + doc.user.first_name + "님의 문서가 반려되었습니다.",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<@" + doc.user.email.replace('@bluemove.or.kr', '').lower() + ">님의 문서가 아래와 같이 반려되었습니다.\n반려 사유를 해소하여 " + str(doc.box.deadline) + " 이내에 다시 제출해주시기 바랍니다." + "\n\n*<https://docs.google.com/document/d/" + doc.file_id + "|" + doc.name + ">*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*문서명:*\n" + doc.box.title + "\n\n*블루무버 계정:*\n" +  doc.user.email + "\n\n*생성일자:*\n" + doc.creation_date + "\n\n*제출일자:*\n" + doc.submission_date + "\n\n*반려일자:*\n" + doc.rejection_date + "\n\n*반려 사유:*\n" + doc.reject_reason
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": doc.avatar_src,
                        "alt_text": doc.user.last_name + doc.user.first_name + "님의 프로필 사진"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "문서함 열기"
                            },
                            "value": "open_box",
                            "url": "http://127.0.0.1:8000/box/" + str(doc.box.id) + "/#docPosition"
                        }
                    ]
                }
            ],
            text = f"📩 " + doc.user.last_name + doc.user.first_name + "님의 문서가 반려되었습니다.",
        )
        doc.save()
        return redirect('box:read', id=doc.box.id)
    ###########################################
    ##### OUTSIDE 클라이언트가 guest일 경우 #####
    ###########################################
    if doc.user.profile.level == 'guest':
        # 01. 서비스 계정 Google Drive, Gmail API 호출
        SERVICE_ACCOUNT_SCOPES = ['https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name (
            'bluemove-docs-6a11a86cda0e.json',
            SERVICE_ACCOUNT_SCOPES,
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        INSIDE_CLIENT = doc.box.writer.email
        user_id = doc.box.writer.email
        SERVICE_ACCOUNT_GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        gmail_credentials = service_account.Credentials.from_service_account_file(
            'bluemove-docs-6a11a86cda0e.json',
            scopes = SERVICE_ACCOUNT_GMAIL_SCOPES,
        )
        credentials_delegated = gmail_credentials.with_subject(INSIDE_CLIENT)
        mail_service = build('gmail', 'v1', credentials = credentials_delegated)
        # 02. 문서 잠금 해제
        drive_response = drive_service.files().update(
            fileId=file_id,
            body={
                "contentRestrictions": [
                    {
                        "readOnly": "false",
                    }
                ]
            }
        ).execute()
        # 03. INSIDE 클라이언트 권한 삭제 writer 2 none
        drive_response = drive_service.permissions().delete(
            fileId = file_id,
            permissionId = inside_permission_id,
        ).execute()
        # 04. OUTSIDE 클라이언트 권한 변경 reader 2 writer
        drive_response = drive_service.permissions().update(
            fileId = file_id,
            permissionId = outside_permission_id,
            body = {
                'role': 'writer',
            },
        ).execute()
        # 05. 문서명 및 설명 변경
        drive_response = drive_service.files().update(
            fileId = file_id,
            body = {
                'name': '블루무브닥스_' +
                        doc.box.title.replace(" ","") + ##### 문서명 INPUT #####
                        doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                        '_' + datetime.date.today().strftime('%y%m%d'),
                'description': '블루무브 닥스에서 생성된 ' +
                            doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                            '님의 ' +
                            doc.box.title ##### 문서명 INPUT #####
                            + '입니다.\n\n' +
                            '📧 생성일자: ' + doc.creation_date + '\n' + ##### 문서 생성일자 INPUT #####
                            '📨 제출일자: ' + doc.submission_date + '\n' + ##### 문서 제출일자 INPUT #####
                            '📩 반려일자: ' + datetime.date.today().strftime('%Y-%m-%d'), ##### 현재 일자 INPUT #####
            },
            fields = 'name'
        ).execute()
        name = drive_response.get('name') ##### 파일 최종 이름 OUTPUT #####
        # 06. 문서 잠금
        drive_response = drive_service.files().update(
            fileId=file_id,
            body={
                "contentRestrictions": [
                    {
                        "readOnly": "true",
                        "reason": "문서가 반려되었습니다. 내용 수정 방지를 위해 잠금 설정되었습니다."
                    }
                ]
            }
        ).execute()
        # 07. 문서 데이터 DB 반영
        doc.name = name
        doc.submit_flag = False
        doc.reject_flag = True
        doc.reject_reason = request.POST.get('reject_reason')
        doc.rejection_date = datetime.date.today().strftime('%Y-%m-%d')
        doc.save()
        # 08. 메일 생성
        sender = doc.box.writer.email.replace('@bluemove.or.kr', '').capitalize() + ' at Bluemove ' + '<' + doc.box.writer.email + '>' ##### INSIDE 클라이언트 이메일 주소 INPUT #####
        to = doc.user.email ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
        subject = doc.user.last_name + doc.user.first_name + '님의 문서가 반려되었습니다.' ##### 문서명 INPUT #####
        message_text = \
            """
            <!doctype html>
            <html
                xmlns="http://www.w3.org/1999/xhtml"
                xmlns:v="urn:schemas-microsoft-com:vml"
                xmlns:o="urn:schemas-microsoft-com:office:office">
                <head>
                    <!-- NAME: 1 COLUMN -->
                    <!--[if gte mso 15]> <xml> <o:OfficeDocumentSettings> <o:AllowPNG/>
                    <o:PixelsPerInch>96</o:PixelsPerInch> </o:OfficeDocumentSettings> </xml>
                    <![endif]-->
                    <meta charset="UTF-8">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>블루무브 닥스 - """ + doc.user.last_name + doc.user.first_name + """님의 문서가 반려되었습니다.</title>
                </head>
                <body>
                    <center>
                        <table
                            align="center"
                            border="0"
                            cellpadding="0"
                            cellspacing="0"
                            height="100%"
                            width="100%"
                            id="bodyTable">
                            <tr>
                                <td align="center" valign="top" id="bodyCell">
                                    <!-- BEGIN TEMPLATE // -->
                                    <table align="center" border="0" cellspacing="0"
                                    cellpadding="0" width="600" style="width:600px;"> <tr> <td align="center"
                                    valign="top" width="600" style="width:600px;">
                                    <table
                                        border="0"
                                        cellpadding="0"
                                        cellspacing="0"
                                        width="100%"
                                        class="templateContainer">
                                        <tr>
                                            <td valign="top" id="templatePreheader"></td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateHeader">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnImageBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnImageBlockOuter">
                                                        <tr>
                                                            <td valign="top" style="padding:9px" class="mcnImageBlockInner">
                                                                <table
                                                                    align="left"
                                                                    width="100%"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    class="mcnImageContentContainer"
                                                                    style="min-width:100%;">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                class="mcnImageContent"
                                                                                valign="top"
                                                                                style="padding-right: 9px; padding-left: 9px; padding-top: 0; padding-bottom: 0;">
                                                                                <img
                                                                                    align="left"
                                                                                    src="https://mcusercontent.com/8e85249d3fe980e2482c148b1/images/725d4688-6ae7-4f5d-8891-9c0796a9ebf4.png"
                                                                                    width="110"
                                                                                    style="max-width:1000px; padding-bottom: 0; display: inline !important; vertical-align: bottom;"
                                                                                    class="mcnRetinaImage">
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateBody">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">
                                                                                <h1>""" + doc.user.last_name + doc.user.first_name + """님의 문서가 반려되었습니다.</h1>
                                                                                <p>안녕하세요, 블루무브 """ + doc.box.writer.last_name + doc.box.writer.first_name + """입니다.<br>
                                                                                    """ + doc.user.last_name + doc.user.first_name + """님의 문서가 아래와 같이 반려되었습니다.</p>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>

                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnBoxedTextBlock"
                                                    style="min-width:100%;">
                                                    <!--[if gte mso 9]> <table align="center" border="0" cellspacing="0"
                                                    cellpadding="0" width="100%"> <![endif]-->
                                                    <tbody class="mcnBoxedTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnBoxedTextBlockInner">

                                                                <!--[if gte mso 9]> <td align="center" valign="top" "> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    width="100%"
                                                                    style="min-width:100%;"
                                                                    class="mcnBoxedTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                style="padding-top:9px; padding-left:18px; padding-bottom:9px; padding-right:18px;">

                                                                                <table
                                                                                    border="0"
                                                                                    cellspacing="0"
                                                                                    class="mcnTextContentContainer"
                                                                                    width="100%"
                                                                                    style="min-width: 100% !important;background-color: #F7F7F7;">
                                                                                    <tbody>
                                                                                        <tr>
                                                                                            <td
                                                                                                valign="top"
                                                                                                class="mcnTextContent"
                                                                                                style="padding: 18px;color: #58595B;font-family: Helvetica;font-size: 14px;font-weight: normal;">
                                                                                                <strong style="color:#222222;">문서명</strong>: """ + doc.box.title + """<br>
                                                                                                <strong style="color:#222222;">Google 계정</strong>: """ + doc.user.email + """<br>
                                                                                                <strong style="color:#222222;">생성일자</strong>: """ + doc.creation_date + """<br>
                                                                                                <strong style="color:#222222;">제출일자</strong>: """ + doc.submission_date + """<br>
                                                                                                <strong style="color:#222222;">반려일자</strong>: """ + doc.rejection_date + """<br>
                                                                                                <strong style="color:#222222;">반려 사유</strong>: """ + doc.reject_reason + """
                                                                                            </td>
                                                                                        </tr>
                                                                                    </tbody>
                                                                                </table>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if gte mso 9]> </td> <![endif]-->

                                                                <!--[if gte mso 9]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">

                                                                                블루무브 닥스 문서함에서 문서를 수정하거나 삭제할 수 있습니다.<br>
                                                                                반려 사유를 해소하여 """ + doc.box.deadline.strftime('%Y-%m-%d') + """ 이내에 다시 제출해주시기 바랍니다.<br>
                                                                                감사합니다.<br><br>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnButtonBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnButtonBlockOuter">
                                                        <tr>
                                                            <td
                                                                style="padding-top:0; padding-right:18px; padding-bottom:18px; padding-left:18px;"
                                                                valign="top"
                                                                align="center"
                                                                class="mcnButtonBlockInner">
                                                                <a
                                                                    href="http://127.0.0.1:8000/box/""" + str(doc.box.id) + """/"
                                                                    target="_blank"
                                                                    style="text-decoration:none;">
                                                                    <table
                                                                        border="0"
                                                                        cellpadding="0"
                                                                        cellspacing="0"
                                                                        width="100%"
                                                                        class="mcnButtonContentContainer"
                                                                        style="border-collapse: separate !important;border-radius: 4px;background-color: #007DC5;">
                                                                        <tbody>
                                                                            <tr>
                                                                                <td
                                                                                    align="center"
                                                                                    valign="middle"
                                                                                    class="mcnButtonContent"
                                                                                    style="font-family: Arial; font-size: 16px; padding-left: 12px; padding-top: 8px; padding-bottom: 8px; padding-right: 12px;">
                                                                                    <a
                                                                                        class="mcnButton"
                                                                                        title="블루무브 닥스 문서함 열기"
                                                                                        href="http://127.0.0.1:8000/box/""" + str(doc.box.id) + """/"
                                                                                        target="_blank"
                                                                                        style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">블루무브 닥스 문서함 열기</a>
                                                                                </td>
                                                                            </tr>
                                                                        </tbody>
                                                                    </table>
                                                                </a>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateFooter">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding: 0px 18px 9px; text-align: left;">
                                                                                <hr style="border:0;height:.5px;background-color:#EEEEEE;">
                                                                                <small style="color: #58595B;">
                                                                                    이 메일은 블루무브 닥스를 통해 자동 발신되었습니다. 궁금하신 점이 있을 경우 이 주소로 회신해주시거나 사무국 연락처로 문의해주시기 바랍니다.<br>
                                                                                    ⓒ 파란물결 블루무브
                                                                                </small>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    </td> </tr> </table>
                                    <!-- // END TEMPLATE -->
                                </td>
                            </tr>
                        </table>
                    </center>
                </body>
            </html>
            """
        message = MIMEText(message_text, 'html')
        message['from'] = sender
        message['to'] = to
        message['subject'] = subject
        message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')}
        # 09. 메일 발신
        message = (
            mail_service.users().messages().send(
                userId = user_id,
                body = message,
            ).execute()
        )
        # message_id = message['id']
        # 10. 슬랙 메시지 발신
        client = WebClient(token=slack_bot_token)
        try:
            client.conversations_join(
                channel = doc.box.channel_id
            )
        except:
            None
        slack = client.chat_postMessage(
            channel = doc.box.channel_id,
            link_names = True,
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📨 " + doc.user.last_name + doc.user.first_name + "님의 문서가 반려되었습니다.",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<@" + doc.box.writer.email.replace('@bluemove.or.kr', '').lower() + ">님이 " + doc.user.last_name + doc.user.first_name + "님의 문서를 아래와 같이 반려했습니다.\n\n*<https://docs.google.com/document/d/" + doc.file_id + "|" + doc.name + ">*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*문서명:*\n" + doc.box.title + "\n\n*Google 계정:*\n" +  doc.user.email + "\n\n*생성일자:*\n" + doc.creation_date + "\n\n*제출일자:*\n" + doc.submission_date + "\n\n*반려일자:*\n" + doc.rejection_date + "\n\n*반려 사유:*\n" + doc.reject_reason
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": doc.avatar_src,
                        "alt_text": doc.user.last_name + doc.user.first_name + "님의 프로필 사진"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "문서함 열기"
                            },
                            "value": "open_box",
                            "url": "http://127.0.0.1:8000/box/" + str(doc.box.id) + "/#docPosition"
                        }
                    ]
                }
            ],
            text = f"📨 " + doc.user.last_name + doc.user.first_name + "님의 문서가 반려되었습니다.",
        )
        doc.slack_ts = slack['ts']
        return redirect('box:read', id=doc.box.id)


@login_required
# @permission_required('auth.add_permission', raise_exception=True)
def return_doc(request, doc_id):
    doc = get_object_or_404(Doc, pk=doc_id)
    file_id = doc.file_id
    inside_permission_id = doc.inside_permission_id
    outside_permission_id = doc.outside_permission_id
    permission_id = doc.permission_id
    ###################################
    ##### INSIDE 클라이언트일 경우 #####
    ###################################
    if doc.user.profile.level == 'bluemover':
        # 01. INSIDE 클라이언트 Google Drive, 서비스 계정 Gmail API 호출
        token = SocialToken.objects.get(account__user=request.user, account__provider='google')
        credentials = Credentials(
            client_id=client_id,
            client_secret=client_secret,
            token_uri='https://oauth2.googleapis.com/token',
            token=token.token,
            refresh_token=token.token_secret,
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        INSIDE_CLIENT = doc.box.writer.email
        user_id = doc.box.writer.email
        SERVICE_ACCOUNT_GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        gmail_credentials = service_account.Credentials.from_service_account_file(
            'bluemove-docs-6a11a86cda0e.json',
            scopes = SERVICE_ACCOUNT_GMAIL_SCOPES,
        )
        credentials_delegated = gmail_credentials.with_subject(INSIDE_CLIENT)
        mail_service = build('gmail', 'v1', credentials = credentials_delegated)
        # 02. 문서 잠금 해제
        drive_response = drive_service.files().update(
            fileId=file_id,
            body={
                "contentRestrictions": [
                    {
                        "readOnly": "false",
                    }
                ]
            }
        ).execute()
        # 03. 문서명 및 설명 변경
        drive_response = drive_service.files().update(
            fileId = file_id,
            body = {
                'name': doc.box.prefix + '_' + ##### 파일 프리픽스 INPUT #####
                        doc.box.title.replace(" ","") + ##### 문서명 INPUT #####
                        doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                        '_' + datetime.date.today().strftime('%y%m%d'),
                'description': '블루무브 닥스에서 생성된 ' +
                            doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                            '님의 ' +
                            doc.box.title ##### 문서명 INPUT #####
                            + '입니다.\n\n' +
                            '📧 생성일자: ' + doc.creation_date + '\n' + ##### 문서 생성일자 INPUT #####
                            '📨 제출일자: ' + doc.submission_date + '\n' + ##### 문서 제출일자 INPUT #####
                            '🙆 승인일자: ' + datetime.date.today().strftime('%Y-%m-%d'), ##### 현재 일자 INPUT #####
            },
            fields = 'name'
        ).execute()
        name = drive_response.get('name') ##### 파일 최종 이름 OUTPUT #####
        # 04. 문서 잠금
        drive_response = drive_service.files().update(
            fileId=file_id,
            body={
                "contentRestrictions": [
                    {
                        "readOnly": "true",
                        "reason": "문서가 승인되었습니다. 내용 수정 방지를 위해 잠금 설정되었습니다."
                    }
                ],
            }
        ).execute()
        # 05. 문서 이동
        drive_response = drive_service.files().update(
            fileId = file_id,
            addParents = doc.box.folder_id,
            supportsAllDrives = True,
            useContentAsIndexableText = True,
        ).execute()
        # 06. 문서 데이터 DB 반영
        doc.submit_flag = False
        doc.return_flag = True
        doc.return_date = datetime.date.today().strftime('%Y-%m-%d')
        doc.folder = request.POST.get('folder')
        doc.outside_permission_id = None
        doc.inside_permission_id = None
        doc.save()
        # 07. 메일 생성
        sender = doc.box.writer.email.replace('@bluemove.or.kr', '') + ' at Bluemove ' + '<' + doc.box.writer.email + '>' ##### INSIDE 클라이언트 이메일 주소 INPUT #####
        to = doc.user.email ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
        subject = doc.user.last_name + doc.user.first_name + '님의 문서가 승인되었습니다.' ##### 문서명 INPUT #####
        message_text = \
            """
            <!doctype html>
            <html
                xmlns="http://www.w3.org/1999/xhtml"
                xmlns:v="urn:schemas-microsoft-com:vml"
                xmlns:o="urn:schemas-microsoft-com:office:office">
                <head>
                    <!-- NAME: 1 COLUMN -->
                    <!--[if gte mso 15]> <xml> <o:OfficeDocumentSettings> <o:AllowPNG/>
                    <o:PixelsPerInch>96</o:PixelsPerInch> </o:OfficeDocumentSettings> </xml>
                    <![endif]-->
                    <meta charset="UTF-8">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>블루무브 닥스 - """ + doc.user.last_name + doc.user.first_name + """님의 문서가 승인되었습니다.</title>
                </head>
                <body>
                    <center>
                        <table
                            align="center"
                            border="0"
                            cellpadding="0"
                            cellspacing="0"
                            height="100%"
                            width="100%"
                            id="bodyTable">
                            <tr>
                                <td align="center" valign="top" id="bodyCell">
                                    <!-- BEGIN TEMPLATE // -->
                                    <table align="center" border="0" cellspacing="0"
                                    cellpadding="0" width="600" style="width:600px;"> <tr> <td align="center"
                                    valign="top" width="600" style="width:600px;">
                                    <table
                                        border="0"
                                        cellpadding="0"
                                        cellspacing="0"
                                        width="100%"
                                        class="templateContainer">
                                        <tr>
                                            <td valign="top" id="templatePreheader"></td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateHeader">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnImageBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnImageBlockOuter">
                                                        <tr>
                                                            <td valign="top" style="padding:9px" class="mcnImageBlockInner">
                                                                <table
                                                                    align="left"
                                                                    width="100%"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    class="mcnImageContentContainer"
                                                                    style="min-width:100%;">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                class="mcnImageContent"
                                                                                valign="top"
                                                                                style="padding-right: 9px; padding-left: 9px; padding-top: 0; padding-bottom: 0;">
                                                                                <img
                                                                                    align="left"
                                                                                    src="https://mcusercontent.com/8e85249d3fe980e2482c148b1/images/725d4688-6ae7-4f5d-8891-9c0796a9ebf4.png"
                                                                                    width="110"
                                                                                    style="max-width:1000px; padding-bottom: 0; display: inline !important; vertical-align: bottom;"
                                                                                    class="mcnRetinaImage">
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateBody">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">
                                                                                <h1>""" + doc.user.last_name + doc.user.first_name + """님의 문서가 승인되었습니다.</h1>
                                                                                <p>안녕하세요, 블루무브 """ + doc.box.writer.last_name + doc.box.writer.first_name + """입니다.<br>
                                                                                    """ + doc.user.last_name + doc.user.first_name + """님의 문서가 아래와 같이 승인되었습니다.</p>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>

                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnBoxedTextBlock"
                                                    style="min-width:100%;">
                                                    <!--[if gte mso 9]> <table align="center" border="0" cellspacing="0"
                                                    cellpadding="0" width="100%"> <![endif]-->
                                                    <tbody class="mcnBoxedTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnBoxedTextBlockInner">

                                                                <!--[if gte mso 9]> <td align="center" valign="top" "> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    width="100%"
                                                                    style="min-width:100%;"
                                                                    class="mcnBoxedTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                style="padding-top:9px; padding-left:18px; padding-bottom:9px; padding-right:18px;">

                                                                                <table
                                                                                    border="0"
                                                                                    cellspacing="0"
                                                                                    class="mcnTextContentContainer"
                                                                                    width="100%"
                                                                                    style="min-width: 100% !important;background-color: #F7F7F7;">
                                                                                    <tbody>
                                                                                        <tr>
                                                                                            <td
                                                                                                valign="top"
                                                                                                class="mcnTextContent"
                                                                                                style="padding: 18px;color: #58595B;font-family: Helvetica;font-size: 14px;font-weight: normal;">
                                                                                                <strong style="color:#222222;">문서명</strong>: """ + doc.box.title + """<br>
                                                                                                <strong style="color:#222222;">블루무버 계정</strong>: """ + doc.user.email + """<br>
                                                                                                <strong style="color:#222222;">생성일자</strong>: """ + doc.creation_date + """<br>
                                                                                                <strong style="color:#222222;">제출일자</strong>: """ + doc.submission_date + """<br>
                                                                                                <strong style="color:#222222;">승인일자</strong>: """ + doc.return_date + """
                                                                                            </td>
                                                                                        </tr>
                                                                                    </tbody>
                                                                                </table>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if gte mso 9]> </td> <![endif]-->

                                                                <!--[if gte mso 9]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">

                                                                                문서가 승인되어 보관 폴더로 이동되었습니다.<br>
                                                                                문서에 대한 권한은 보관 폴더 설정에 따릅니다.<br>
                                                                                감사합니다.<br><br>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnButtonBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnButtonBlockOuter">
                                                        <tr>
                                                            <td
                                                                style="padding-top:0; padding-right:18px; padding-bottom:18px; padding-left:18px;"
                                                                valign="top"
                                                                align="center"
                                                                class="mcnButtonBlockInner">
                                                                <a
                                                                    href="https://drive.google.com/drive/search?q=""" + doc.box.title.replace(' ', '') + doc.user.last_name + doc.user.first_name + """"
                                                                    target="_blank"
                                                                    style="text-decoration:none;">
                                                                    <table
                                                                        border="0"
                                                                        cellpadding="0"
                                                                        cellspacing="0"
                                                                        width="100%"
                                                                        class="mcnButtonContentContainer"
                                                                        style="border-collapse: separate !important;border-radius: 4px;background-color: #007DC5;">
                                                                        <tbody>
                                                                            <tr>
                                                                                <td
                                                                                    align="center"
                                                                                    valign="middle"
                                                                                    class="mcnButtonContent"
                                                                                    style="font-family: Arial; font-size: 16px; padding-left: 12px; padding-top: 8px; padding-bottom: 8px; padding-right: 12px;">
                                                                                    <a
                                                                                        class="mcnButton"
                                                                                        title="블루무브 닥스 문서함 열기"
                                                                                        href="http://127.0.0.1:8000/box/""" + str(doc.box.id) + """/"
                                                                                        target="_blank"
                                                                                        style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">블루무브 닥스 문서함 열기</a>
                                                                                </td>
                                                                            </tr>
                                                                        </tbody>
                                                                    </table>
                                                                </a>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateFooter">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding: 0px 18px 9px; text-align: left;">
                                                                                <hr style="border:0;height:.5px;background-color:#EEEEEE;">
                                                                                <small style="color: #58595B;">
                                                                                    이 메일은 블루무브 닥스를 통해 자동 발신되었습니다.<br>
                                                                                    ⓒ 파란물결 블루무브
                                                                                </small>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    </td> </tr> </table>
                                    <!-- // END TEMPLATE -->
                                </td>
                            </tr>
                        </table>
                    </center>
                </body>
            </html>
            """
        message = MIMEText(message_text, 'html')
        message['from'] = sender
        message['to'] = to
        message['subject'] = subject
        message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')}
        # 08. 메일 발신
        message = (
            mail_service.users().messages().send(
                userId = user_id,
                body = message,
            ).execute()
        )
        # message_id = message['id']
        # 09. 슬랙 메시지 발신
        client = WebClient(token=slack_bot_token)
        try:
            client.conversations_join(
                channel = doc.box.channel_id
            )
        except:
            None
        slack = client.chat_postMessage(
            channel = doc.box.channel_id,
            link_names = True,
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🙆 " + doc.user.last_name + doc.user.first_name + "님의 문서가 승인되었습니다.",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<@" + doc.box.writer.email.replace('@bluemove.or.kr', '').lower() + ">님이 " + doc.user.last_name + doc.user.first_name + "님의 문서를 아래와 같이 승인했습니다.\n\n*<https://docs.google.com/document/d/" + doc.file_id + "|" + doc.name + ">*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*문서명:*\n" + doc.box.title + "\n\n*블루무버 계정:*\n" +  doc.user.email + "\n\n*생성일자:*\n" + doc.creation_date + "\n\n*제출일자:*\n" + doc.submission_date + "\n\n*승인일자:*\n" + doc.return_date
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": doc.avatar_src,
                        "alt_text": doc.user.last_name + doc.user.first_name + "님의 프로필 사진"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "문서함 열기"
                            },
                            "value": "open_box",
                            "url": "http://127.0.0.1:8000/box/" + str(doc.box.id) + "/#docPosition"
                        }
                    ]
                }
            ],
            text = f"🙆 " + doc.user.last_name + doc.user.first_name + "님의 문서가 승인되었습니다.",
        )
        doc.slack_ts = slack['ts']
        # 10. OUTSIDE 클라이언트 슬랙 메시지 발신
        client.chat_postMessage(
            channel = doc.user.profile.slack_user_id,
            link_names = True,
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🙆 " + doc.user.last_name + doc.user.first_name + "님의 문서가 승인되었습니다.",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<@" + doc.user.email.replace('@bluemove.or.kr', '').lower() + ">님의 문서가 아래와 같이 승인되었습니다.\n\n*<https://docs.google.com/document/d/" + doc.file_id + "|" + doc.name + ">*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*문서명:*\n" + doc.box.title + "\n\n*블루무버 계정:*\n" +  doc.user.email + "\n\n*생성일자:*\n" + doc.creation_date + "\n\n*제출일자:*\n" + doc.submission_date + "\n\n*승인일자:*\n" + doc.return_date
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": doc.avatar_src,
                        "alt_text": doc.user.last_name + doc.user.first_name + "님의 프로필 사진"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "문서함 열기"
                            },
                            "value": "open_box",
                            "url": "http://127.0.0.1:8000/box/" + str(doc.box.id) + "/#docPosition"
                        }
                    ]
                }
            ],
            text = f"🙆 " + doc.user.last_name + doc.user.first_name + "님의 문서가 승인되었습니다.",
        )
        doc.save()
        return redirect('box:read', id=doc.box.id)
    ###########################################
    ##### OUTSIDE 클라이언트가 guest일 경우 #####
    ###########################################
    if doc.user.profile.level == 'guest':
        # 01. 서비스 계정 Google Drive, Gmail API 호출
        SERVICE_ACCOUNT_SCOPES = ['https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name (
            'bluemove-docs-6a11a86cda0e.json',
            SERVICE_ACCOUNT_SCOPES,
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        INSIDE_CLIENT = doc.box.writer.email
        user_id = doc.box.writer.email
        SERVICE_ACCOUNT_GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        gmail_credentials = service_account.Credentials.from_service_account_file(
            'bluemove-docs-6a11a86cda0e.json',
            scopes = SERVICE_ACCOUNT_GMAIL_SCOPES,
        )
        credentials_delegated = gmail_credentials.with_subject(INSIDE_CLIENT)
        mail_service = build('gmail', 'v1', credentials = credentials_delegated)
        # 02. 문서 잠금 해제
        drive_response = drive_service.files().update(
            fileId=file_id,
            body={
                "contentRestrictions": [
                    {
                        "readOnly": "false",
                    }
                ]
            }
        ).execute()
        # 03. INSIDE 클라이언트 권한 삭제 writer 2 none
        drive_response = drive_service.permissions().delete(
            fileId = file_id,
            permissionId = inside_permission_id,
        ).execute()
        # 04. OUTSIDE 클라이언트 권한 변경 reader 2 owner
        drive_response = drive_service.permissions().update(
            fileId = file_id,
            permissionId = outside_permission_id,
            transferOwnership = True,
            body = {
                'role': 'owner',
            },
        ).execute()
        # 05. 문서명 및 설명 변경
        drive_response = drive_service.files().update(
            fileId = file_id,
            body = {
                'name': '블루무브닥스_' +
                        doc.box.title.replace(" ","") + ##### 문서명 INPUT #####
                        doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                        '_' + datetime.date.today().strftime('%y%m%d'),
                'description': '블루무브 닥스에서 생성된 ' +
                            doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                            '님의 ' +
                            doc.box.title ##### 문서명 INPUT #####
                            + '입니다.\n\n' +
                            '📧 생성일자: ' + doc.creation_date + '\n' + ##### 문서 생성일자 INPUT #####
                            '📨 제출일자: ' + doc.submission_date + '\n' + ##### 문서 제출일자 INPUT #####
                            '📩 반환일자: ' + datetime.date.today().strftime('%Y-%m-%d'), ##### 현재 일자 INPUT #####
            },
            fields = 'name'
        ).execute()
        name = drive_response.get('name') ##### 파일 최종 이름 OUTPUT #####
        # 06. 문서 잠금
        drive_response = drive_service.files().update(
            fileId=file_id,
            body={
                "contentRestrictions": [
                    {
                        "readOnly": "true",
                        "reason": "문서가 반환되었습니다. 내용 수정 방지를 위해 잠금 설정되었습니다."
                    }
                ]
            }
        ).execute()
        # 07. 서비스 계정 권한 삭제 writer 2 none
        drive_response = drive_service.permissions().delete(
            fileId = file_id,
            permissionId = permission_id,
        ).execute()
        # 08. 문서 데이터 DB 반영
        doc.submit_flag = False
        doc.return_flag = True
        doc.return_date = datetime.date.today().strftime('%Y-%m-%d')
        doc.outside_permission_id = None
        doc.permission_id = None
        doc.inside_permission_id = None
        doc.save()
        # 09. 메일 생성
        sender = doc.box.writer.email.replace('@bluemove.or.kr', '') + ' at Bluemove ' + '<' + doc.box.writer.email + '>' ##### INSIDE 클라이언트 이메일 주소 INPUT #####
        to = doc.user.email ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
        subject = doc.user.last_name + doc.user.first_name + '님의 문서가 반환되었습니다.' ##### 문서명 INPUT #####
        message_text = \
            """
            <!doctype html>
            <html
                xmlns="http://www.w3.org/1999/xhtml"
                xmlns:v="urn:schemas-microsoft-com:vml"
                xmlns:o="urn:schemas-microsoft-com:office:office">
                <head>
                    <!-- NAME: 1 COLUMN -->
                    <!--[if gte mso 15]> <xml> <o:OfficeDocumentSettings> <o:AllowPNG/>
                    <o:PixelsPerInch>96</o:PixelsPerInch> </o:OfficeDocumentSettings> </xml>
                    <![endif]-->
                    <meta charset="UTF-8">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>블루무브 닥스 - """ + doc.user.last_name + doc.user.first_name + """님의 문서가 반환되었습니다.</title>
                </head>
                <body>
                    <center>
                        <table
                            align="center"
                            border="0"
                            cellpadding="0"
                            cellspacing="0"
                            height="100%"
                            width="100%"
                            id="bodyTable">
                            <tr>
                                <td align="center" valign="top" id="bodyCell">
                                    <!-- BEGIN TEMPLATE // -->
                                    <table align="center" border="0" cellspacing="0"
                                    cellpadding="0" width="600" style="width:600px;"> <tr> <td align="center"
                                    valign="top" width="600" style="width:600px;">
                                    <table
                                        border="0"
                                        cellpadding="0"
                                        cellspacing="0"
                                        width="100%"
                                        class="templateContainer">
                                        <tr>
                                            <td valign="top" id="templatePreheader"></td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateHeader">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnImageBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnImageBlockOuter">
                                                        <tr>
                                                            <td valign="top" style="padding:9px" class="mcnImageBlockInner">
                                                                <table
                                                                    align="left"
                                                                    width="100%"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    class="mcnImageContentContainer"
                                                                    style="min-width:100%;">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                class="mcnImageContent"
                                                                                valign="top"
                                                                                style="padding-right: 9px; padding-left: 9px; padding-top: 0; padding-bottom: 0;">
                                                                                <img
                                                                                    align="left"
                                                                                    src="https://mcusercontent.com/8e85249d3fe980e2482c148b1/images/725d4688-6ae7-4f5d-8891-9c0796a9ebf4.png"
                                                                                    width="110"
                                                                                    style="max-width:1000px; padding-bottom: 0; display: inline !important; vertical-align: bottom;"
                                                                                    class="mcnRetinaImage">
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateBody">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">
                                                                                <h1>""" + doc.user.last_name + doc.user.first_name + """님의 문서가 반환되었습니다.</h1>
                                                                                <p>안녕하세요, 블루무브 """ + doc.box.writer.last_name + doc.box.writer.first_name + """입니다.<br>
                                                                                    """ + doc.user.last_name + doc.user.first_name + """님의 문서가 아래와 같이 반환되었습니다.</p>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>

                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnBoxedTextBlock"
                                                    style="min-width:100%;">
                                                    <!--[if gte mso 9]> <table align="center" border="0" cellspacing="0"
                                                    cellpadding="0" width="100%"> <![endif]-->
                                                    <tbody class="mcnBoxedTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnBoxedTextBlockInner">

                                                                <!--[if gte mso 9]> <td align="center" valign="top" "> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    width="100%"
                                                                    style="min-width:100%;"
                                                                    class="mcnBoxedTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                style="padding-top:9px; padding-left:18px; padding-bottom:9px; padding-right:18px;">

                                                                                <table
                                                                                    border="0"
                                                                                    cellspacing="0"
                                                                                    class="mcnTextContentContainer"
                                                                                    width="100%"
                                                                                    style="min-width: 100% !important;background-color: #F7F7F7;">
                                                                                    <tbody>
                                                                                        <tr>
                                                                                            <td
                                                                                                valign="top"
                                                                                                class="mcnTextContent"
                                                                                                style="padding: 18px;color: #58595B;font-family: Helvetica;font-size: 14px;font-weight: normal;">
                                                                                                <strong style="color:#222222;">문서명</strong>: """ + doc.box.title + """<br>
                                                                                                <strong style="color:#222222;">Google 계정</strong>: """ + doc.user.email + """<br>
                                                                                                <strong style="color:#222222;">생성일자</strong>: """ + doc.creation_date + """<br>
                                                                                                <strong style="color:#222222;">제출일자</strong>: """ + doc.submission_date + """<br>
                                                                                                <strong style="color:#222222;">반환일자</strong>: """ + doc.return_date + """
                                                                                            </td>
                                                                                        </tr>
                                                                                    </tbody>
                                                                                </table>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if gte mso 9]> </td> <![endif]-->

                                                                <!--[if gte mso 9]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">

                                                                                문서 소유 권한이 """ + doc.user.last_name + doc.user.first_name + """님에게 이전되어 더 이상 블루무브 닥스에서 이 문서에 액세스할 수 없습니다.<br>
                                                                                Google 드라이브에서 문서명을 검색하거나 '<a href="https://drive.google.com/drive/recent" style="color:#007DC5;">최근 문서함</a>'을 확인하시기 바랍니다.<br>
                                                                                감사합니다.<br><br>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnButtonBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnButtonBlockOuter">
                                                        <tr>
                                                            <td
                                                                style="padding-top:0; padding-right:18px; padding-bottom:18px; padding-left:18px;"
                                                                valign="top"
                                                                align="center"
                                                                class="mcnButtonBlockInner">
                                                                <a
                                                                    href="https://drive.google.com/drive/search?q=""" + doc.box.title.replace(' ', '') + doc.user.last_name + doc.user.first_name + """"
                                                                    target="_blank"
                                                                    style="text-decoration:none;">
                                                                    <table
                                                                        border="0"
                                                                        cellpadding="0"
                                                                        cellspacing="0"
                                                                        width="100%"
                                                                        class="mcnButtonContentContainer"
                                                                        style="border-collapse: separate !important;border-radius: 4px;background-color: #007DC5;">
                                                                        <tbody>
                                                                            <tr>
                                                                                <td
                                                                                    align="center"
                                                                                    valign="middle"
                                                                                    class="mcnButtonContent"
                                                                                    style="font-family: Arial; font-size: 16px; padding-left: 12px; padding-top: 8px; padding-bottom: 8px; padding-right: 12px;">
                                                                                    <a
                                                                                        class="mcnButton"
                                                                                        title="Google 드라이브에서 찾아보기"
                                                                                        href="https://drive.google.com/drive/search?q=""" + doc.box.title.replace(' ', '') + doc.user.last_name + doc.user.first_name + """"
                                                                                        target="_blank"
                                                                                        style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">Google 드라이브에서 찾아보기</a>
                                                                                </td>
                                                                            </tr>
                                                                        </tbody>
                                                                    </table>
                                                                </a>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="top" id="templateFooter">
                                                <table
                                                    border="0"
                                                    cellpadding="0"
                                                    cellspacing="0"
                                                    width="100%"
                                                    class="mcnTextBlock"
                                                    style="min-width:100%;">
                                                    <tbody class="mcnTextBlockOuter">
                                                        <tr>
                                                            <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                                <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                                width="100%" style="width:100%;"> <tr> <![endif]-->

                                                                <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                                <table
                                                                    align="left"
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    style="max-width:100%; min-width:100%;"
                                                                    width="100%"
                                                                    class="mcnTextContentContainer">
                                                                    <tbody>
                                                                        <tr>

                                                                            <td
                                                                                valign="top"
                                                                                class="mcnTextContent"
                                                                                style="padding: 0px 18px 9px; text-align: left;">
                                                                                <hr style="border:0;height:.5px;background-color:#EEEEEE;">
                                                                                <small style="color: #58595B;">
                                                                                    이 메일은 블루무브 닥스를 통해 자동 발신되었습니다. 궁금하신 점이 있을 경우 이 주소로 회신해주시거나 사무국 연락처로 문의해주시기 바랍니다.<br>
                                                                                    ⓒ 파란물결 블루무브
                                                                                </small>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                                <!--[if mso]> </td> <![endif]-->

                                                                <!--[if mso]> </tr> </table> <![endif]-->
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    </td> </tr> </table>
                                    <!-- // END TEMPLATE -->
                                </td>
                            </tr>
                        </table>
                    </center>
                </body>
            </html>
            """
        message = MIMEText(message_text, 'html')
        message['from'] = sender
        message['to'] = to
        message['subject'] = subject
        message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')}
        # 10. 메일 발신
        message = (
            mail_service.users().messages().send(
                userId = user_id,
                body = message,
            ).execute()
        )
        # message_id = message['id']
        # 11. 슬랙 메시지 발신
        client = WebClient(token=slack_bot_token)
        try:
            client.conversations_join(
                channel = doc.box.channel_id
            )
        except:
            None
        slack = client.chat_postMessage(
            channel = doc.box.channel_id,
            link_names = True,
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🙆 " + doc.user.last_name + doc.user.first_name + "님의 문서가 반환되었습니다.",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<@" + doc.box.writer.email.replace('@bluemove.or.kr', '').lower() + ">님이 " + doc.user.last_name + doc.user.first_name + "님의 문서를 아래와 같이 반환했습니다.\n\n*<https://docs.google.com/document/d/" + doc.file_id + "|" + doc.name + ">*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*문서명:*\n" + doc.box.title + "\n\n*Google 계정:*\n" +  doc.user.email + "\n\n*생성일자:*\n" + doc.creation_date + "\n\n*제출일자:*\n" + doc.submission_date + "\n\n*반환일자:*\n" + doc.return_date
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": doc.avatar_src,
                        "alt_text": doc.user.last_name + doc.user.first_name + "님의 프로필 사진"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "문서함 열기"
                            },
                            "value": "open_box",
                            "url": "http://127.0.0.1:8000/box/" + str(doc.box.id) + "/#docPosition"
                        }
                    ]
                }
            ],
            text = f"🙆 " + doc.user.last_name + doc.user.first_name + "님의 문서가 반환되었습니다.",
        )
        doc.slack_ts = slack['ts']
        return redirect('box:read', id=doc.box.id)


@login_required
# @permission_required('auth.add_permission', raise_exception=True)
def return_doc_before_submit(request, doc_id):
    doc = get_object_or_404(Doc, pk=doc_id)
    file_id = doc.file_id
    permission_id = doc.permission_id
    outside_permission_id = doc.outside_permission_id
    # 01. 서비스 계정 Google Drive, Gmail API 호출
    SERVICE_ACCOUNT_SCOPES = ['https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name (
        'bluemove-docs-6a11a86cda0e.json',
        SERVICE_ACCOUNT_SCOPES,
    )
    drive_service = build('drive', 'v3', credentials=credentials)
    INSIDE_CLIENT = doc.box.writer.email
    user_id = doc.box.writer.email
    SERVICE_ACCOUNT_GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    gmail_credentials = service_account.Credentials.from_service_account_file(
        'bluemove-docs-6a11a86cda0e.json',
        scopes = SERVICE_ACCOUNT_GMAIL_SCOPES,
    )
    credentials_delegated = gmail_credentials.with_subject(INSIDE_CLIENT)
    mail_service = build('gmail', 'v1', credentials = credentials_delegated)
    # 02. 문서 잠금 해제
    drive_response = drive_service.files().update(
        fileId=file_id,
        body={
            "contentRestrictions": [
                {
                    "readOnly": "false",
                }
            ]
        }
    ).execute()
    # 03. OUTSIDE 클라이언트 권한 변경 writer 2 owner
    drive_response = drive_service.permissions().update(
        fileId = file_id,
        permissionId = outside_permission_id,
        transferOwnership = True,
        body = {
            'role': 'owner',
        },
    ).execute()
    # 04. 문서명 및 설명 변경
    drive_response = drive_service.files().update(
        fileId = file_id,
        body = {
            'name': '블루무브닥스_' +
                    doc.box.title.replace(" ","") + ##### 문서명 INPUT #####
                    doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                    '_' + datetime.date.today().strftime('%y%m%d'),
            'description': '블루무브 닥스에서 생성된 ' +
                           doc.user.last_name + doc.user.first_name + ##### OUTSIDE 클라이언트 성명 INPUT #####
                           '님의 ' +
                           doc.box.title ##### 문서명 INPUT #####
                           + '입니다.\n\n' +
                           '📧 생성일자: ' + doc.creation_date + '\n' + ##### 문서 생성일자 INPUT #####
                           '📩 반환일자: ' + datetime.date.today().strftime('%Y-%m-%d'), ##### 현재 일자 INPUT #####
        },
        fields = 'name'
    ).execute()
    name = drive_response.get('name') ##### 파일 최종 이름 OUTPUT #####
    # 05. 문서 잠금
    drive_response = drive_service.files().update(
        fileId=file_id,
        body={
            "contentRestrictions": [
                {
                    "readOnly": "true",
                    "reason": "문서가 반환되었습니다. 내용 수정 방지를 위해 잠금 설정되었습니다."
                }
            ]
        }
    ).execute()
    # 06. 서비스 계정 권한 삭제 writer 2 none
    drive_response = drive_service.permissions().delete(
        fileId = file_id,
        permissionId = permission_id,
    ).execute()
    # 07. 문서 데이터 DB 반영
    doc.reject_flag = False
    doc.return_flag = True
    doc.return_date = datetime.date.today().strftime('%Y-%m-%d')
    doc.inside_permission_id = None
    doc.outside_permission_id = None
    doc.permission_id = None
    doc.save()
    # 08. 메일 생성
    sender = doc.box.writer.email.replace('@bluemove.or.kr', '') + ' at Bluemove ' + '<' + doc.box.writer.email + '>' ##### INSIDE 클라이언트 이메일 주소 INPUT #####
    to = doc.user.email ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
    subject = doc.user.last_name + doc.user.first_name + '님의 문서가 반환되었습니다.' ##### 문서명 INPUT #####
    message_text = \
        """
        <!doctype html>
        <html
            xmlns="http://www.w3.org/1999/xhtml"
            xmlns:v="urn:schemas-microsoft-com:vml"
            xmlns:o="urn:schemas-microsoft-com:office:office">
            <head>
                <!-- NAME: 1 COLUMN -->
                <!--[if gte mso 15]> <xml> <o:OfficeDocumentSettings> <o:AllowPNG/>
                <o:PixelsPerInch>96</o:PixelsPerInch> </o:OfficeDocumentSettings> </xml>
                <![endif]-->
                <meta charset="UTF-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>블루무브 닥스 - """ + doc.user.last_name + doc.user.first_name + """님의 문서가 반환되었습니다.</title>
            </head>
            <body>
                <center>
                    <table
                        align="center"
                        border="0"
                        cellpadding="0"
                        cellspacing="0"
                        height="100%"
                        width="100%"
                        id="bodyTable">
                        <tr>
                            <td align="center" valign="top" id="bodyCell">
                                <!-- BEGIN TEMPLATE // -->
                                <table align="center" border="0" cellspacing="0"
                                cellpadding="0" width="600" style="width:600px;"> <tr> <td align="center"
                                valign="top" width="600" style="width:600px;">
                                <table
                                    border="0"
                                    cellpadding="0"
                                    cellspacing="0"
                                    width="100%"
                                    class="templateContainer">
                                    <tr>
                                        <td valign="top" id="templatePreheader"></td>
                                    </tr>
                                    <tr>
                                        <td valign="top" id="templateHeader">
                                            <table
                                                border="0"
                                                cellpadding="0"
                                                cellspacing="0"
                                                width="100%"
                                                class="mcnImageBlock"
                                                style="min-width:100%;">
                                                <tbody class="mcnImageBlockOuter">
                                                    <tr>
                                                        <td valign="top" style="padding:9px" class="mcnImageBlockInner">
                                                            <table
                                                                align="left"
                                                                width="100%"
                                                                border="0"
                                                                cellpadding="0"
                                                                cellspacing="0"
                                                                class="mcnImageContentContainer"
                                                                style="min-width:100%;">
                                                                <tbody>
                                                                    <tr>
                                                                        <td
                                                                            class="mcnImageContent"
                                                                            valign="top"
                                                                            style="padding-right: 9px; padding-left: 9px; padding-top: 0; padding-bottom: 0;">
                                                                            <img
                                                                                align="left"
                                                                                src="https://mcusercontent.com/8e85249d3fe980e2482c148b1/images/725d4688-6ae7-4f5d-8891-9c0796a9ebf4.png"
                                                                                width="110"
                                                                                style="max-width:1000px; padding-bottom: 0; display: inline !important; vertical-align: bottom;"
                                                                                class="mcnRetinaImage">
                                                                        </td>
                                                                    </tr>
                                                                </tbody>
                                                            </table>
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td valign="top" id="templateBody">
                                            <table
                                                border="0"
                                                cellpadding="0"
                                                cellspacing="0"
                                                width="100%"
                                                class="mcnTextBlock"
                                                style="min-width:100%;">
                                                <tbody class="mcnTextBlockOuter">
                                                    <tr>
                                                        <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                            <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                            width="100%" style="width:100%;"> <tr> <![endif]-->

                                                            <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                            <table
                                                                align="left"
                                                                border="0"
                                                                cellpadding="0"
                                                                cellspacing="0"
                                                                style="max-width:100%; min-width:100%;"
                                                                width="100%"
                                                                class="mcnTextContentContainer">
                                                                <tbody>
                                                                    <tr>
                                                                        <td
                                                                            valign="top"
                                                                            class="mcnTextContent"
                                                                            style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">
                                                                            <h1>""" + doc.user.last_name + doc.user.first_name + """님의 문서가 반환되었습니다.</h1>
                                                                            <p>안녕하세요, 블루무브 """ + doc.box.writer.last_name + doc.box.writer.first_name + """입니다.<br>
                                                                                """ + doc.user.last_name + doc.user.first_name + """님의 문서가 아래와 같이 반환되었습니다.</p>
                                                                        </td>
                                                                    </tr>
                                                                </tbody>
                                                            </table>
                                                            <!--[if mso]> </td> <![endif]-->

                                                            <!--[if mso]> </tr> </table> <![endif]-->
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>

                                            <table
                                                border="0"
                                                cellpadding="0"
                                                cellspacing="0"
                                                width="100%"
                                                class="mcnBoxedTextBlock"
                                                style="min-width:100%;">
                                                <!--[if gte mso 9]> <table align="center" border="0" cellspacing="0"
                                                cellpadding="0" width="100%"> <![endif]-->
                                                <tbody class="mcnBoxedTextBlockOuter">
                                                    <tr>
                                                        <td valign="top" class="mcnBoxedTextBlockInner">

                                                            <!--[if gte mso 9]> <td align="center" valign="top" "> <![endif]-->
                                                            <table
                                                                align="left"
                                                                border="0"
                                                                cellpadding="0"
                                                                cellspacing="0"
                                                                width="100%"
                                                                style="min-width:100%;"
                                                                class="mcnBoxedTextContentContainer">
                                                                <tbody>
                                                                    <tr>

                                                                        <td
                                                                            style="padding-top:9px; padding-left:18px; padding-bottom:9px; padding-right:18px;">

                                                                            <table
                                                                                border="0"
                                                                                cellspacing="0"
                                                                                class="mcnTextContentContainer"
                                                                                width="100%"
                                                                                style="min-width: 100% !important;background-color: #F7F7F7;">
                                                                                <tbody>
                                                                                    <tr>
                                                                                        <td
                                                                                            valign="top"
                                                                                            class="mcnTextContent"
                                                                                            style="padding: 18px;color: #58595B;font-family: Helvetica;font-size: 14px;font-weight: normal;">
                                                                                            <strong style="color:#222222;">문서명</strong>: """ + doc.box.title + """<br>
                                                                                            <strong style="color:#222222;">Google 계정</strong>: """ + doc.user.email + """<br>
                                                                                            <strong style="color:#222222;">생성일자</strong>: """ + doc.creation_date + """<br>
                                                                                            <strong style="color:#222222;">반환일자</strong>: """ + doc.return_date + """
                                                                                        </td>
                                                                                    </tr>
                                                                                </tbody>
                                                                            </table>
                                                                        </td>
                                                                    </tr>
                                                                </tbody>
                                                            </table>
                                                            <!--[if gte mso 9]> </td> <![endif]-->

                                                            <!--[if gte mso 9]> </tr> </table> <![endif]-->
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                            <table
                                                border="0"
                                                cellpadding="0"
                                                cellspacing="0"
                                                width="100%"
                                                class="mcnTextBlock"
                                                style="min-width:100%;">
                                                <tbody class="mcnTextBlockOuter">
                                                    <tr>
                                                        <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                            <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                            width="100%" style="width:100%;"> <tr> <![endif]-->

                                                            <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                            <table
                                                                align="left"
                                                                border="0"
                                                                cellpadding="0"
                                                                cellspacing="0"
                                                                style="max-width:100%; min-width:100%;"
                                                                width="100%"
                                                                class="mcnTextContentContainer">
                                                                <tbody>
                                                                    <tr>

                                                                        <td
                                                                            valign="top"
                                                                            class="mcnTextContent"
                                                                            style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px;">
                                                                            기한이 초과되어 문서가 제출되지 않고 반환되었습니다.<br>
                                                                            문서 소유 권한이 """ + doc.user.last_name + doc.user.first_name + """님에게 이전되어 더 이상 블루무브 닥스에서 이 문서에 액세스할 수 없습니다.<br>
                                                                            Google 드라이브에서 문서명을 검색하거나 '<a href="https://drive.google.com/drive/recent" style="color:#007DC5;">최근 문서함</a>'을 확인하시기 바랍니다.<br>
                                                                            감사합니다.<br><br>
                                                                        </td>
                                                                    </tr>
                                                                </tbody>
                                                            </table>
                                                            <!--[if mso]> </td> <![endif]-->

                                                            <!--[if mso]> </tr> </table> <![endif]-->
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                            <table
                                                border="0"
                                                cellpadding="0"
                                                cellspacing="0"
                                                width="100%"
                                                class="mcnButtonBlock"
                                                style="min-width:100%;">
                                                <tbody class="mcnButtonBlockOuter">
                                                    <tr>
                                                        <td
                                                            style="padding-top:0; padding-right:18px; padding-bottom:18px; padding-left:18px;"
                                                            valign="top"
                                                            align="center"
                                                            class="mcnButtonBlockInner">
                                                            <a
                                                                href="https://drive.google.com/drive/search?q=""" + doc.box.title.replace(' ', '') + doc.user.last_name + doc.user.first_name + """"
                                                                target="_blank"
                                                                style="text-decoration:none;">
                                                                <table
                                                                    border="0"
                                                                    cellpadding="0"
                                                                    cellspacing="0"
                                                                    width="100%"
                                                                    class="mcnButtonContentContainer"
                                                                    style="border-collapse: separate !important;border-radius: 4px;background-color: #007DC5;">
                                                                    <tbody>
                                                                        <tr>
                                                                            <td
                                                                                align="center"
                                                                                valign="middle"
                                                                                class="mcnButtonContent"
                                                                                style="font-family: Arial; font-size: 16px; padding-left: 12px; padding-top: 8px; padding-bottom: 8px; padding-right: 12px;">
                                                                                <a
                                                                                    class="mcnButton"
                                                                                    title="Google 드라이브에서 찾아보기"
                                                                                    href="https://drive.google.com/drive/search?q=""" + doc.box.title.replace(' ', '') + doc.user.last_name + doc.user.first_name + """"
                                                                                    target="_blank"
                                                                                    style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">Google 드라이브에서 찾아보기</a>
                                                                            </td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                            </a>
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td valign="top" id="templateFooter">
                                            <table
                                                border="0"
                                                cellpadding="0"
                                                cellspacing="0"
                                                width="100%"
                                                class="mcnTextBlock"
                                                style="min-width:100%;">
                                                <tbody class="mcnTextBlockOuter">
                                                    <tr>
                                                        <td valign="top" class="mcnTextBlockInner" style="padding-top:9px;">
                                                            <!--[if mso]> <table align="left" border="0" cellspacing="0" cellpadding="0"
                                                            width="100%" style="width:100%;"> <tr> <![endif]-->

                                                            <!--[if mso]> <td valign="top" width="600" style="width:600px;"> <![endif]-->
                                                            <table
                                                                align="left"
                                                                border="0"
                                                                cellpadding="0"
                                                                cellspacing="0"
                                                                style="max-width:100%; min-width:100%;"
                                                                width="100%"
                                                                class="mcnTextContentContainer">
                                                                <tbody>
                                                                    <tr>

                                                                        <td
                                                                            valign="top"
                                                                            class="mcnTextContent"
                                                                            style="padding: 0px 18px 9px; text-align: left;">
                                                                            <hr style="border:0;height:.5px;background-color:#EEEEEE;">
                                                                            <small style="color: #58595B;">
                                                                                이 메일은 블루무브 닥스를 통해 자동 발신되었습니다. 궁금하신 점이 있을 경우 이 주소로 회신해주시거나 사무국 연락처로 문의해주시기 바랍니다.<br>
                                                                                ⓒ 파란물결 블루무브
                                                                            </small>
                                                                        </td>
                                                                    </tr>
                                                                </tbody>
                                                            </table>
                                                            <!--[if mso]> </td> <![endif]-->

                                                            <!--[if mso]> </tr> </table> <![endif]-->
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                </td> </tr> </table>
                                <!-- // END TEMPLATE -->
                            </td>
                        </tr>
                    </table>
                </center>
            </body>
        </html>
        """
    message = MIMEText(message_text, 'html')
    message['from'] = sender
    message['to'] = to
    message['subject'] = subject
    message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')}
    # 09. 메일 발신
    message = (
        mail_service.users().messages().send(
            userId = user_id,
            body = message,
        ).execute()
    )
    # message_id = message['id']
    return redirect('box:read', id=doc.box.id)