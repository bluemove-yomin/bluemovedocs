from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *
from django.db.models import Q
from notice.models import Notice, Comment
from box.models import Box, Doc
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from google.oauth2.credentials import Credentials
from django.contrib.auth import logout
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialToken, SocialAccount
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from email.mime.text import MIMEText
import base64
from slack_sdk import WebClient
import string
import random
from django.conf import settings


client_id = getattr(settings, 'CLIENT_ID', 'CLIENT_ID')
client_secret = getattr(settings, 'CLIENT_SECRET', 'CLIENT_SECRET')
slack_bot_token = getattr(settings, 'SLACK_BOT_TOKEN', 'SLACK_BOT_TOKEN')
service_account_creds = "bluemove-docs-9f4ec6cf5006.json"


@login_required
def myaccount(request, id):
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
    user = get_object_or_404(User, pk=id)
    favorites = request.user.favorite_user_set.all().order_by('-id')
    box_favorites = request.user.box_favorite_user_set.all().order_by('-id')
    page = request.GET.get('page', 1)
    paginator = Paginator(favorites, 5)
    try:
        favorites = paginator.page(page)
    except PageNotAnInteger:
        favorites = paginator.page(1)
    except EmptyPage:
        favorites = paginator.page(paginator.num_pages)
    box_page = request.GET.get('box_page', 1)
    box_paginator = Paginator(box_favorites, 5)
    try:
        box_favorites = box_paginator.page(box_page)
    except PageNotAnInteger:
        box_favorites = box_paginator.page(1)
    except EmptyPage:
        box_favorites = box_paginator.page(box_paginator.num_pages)
    return render(request, 'users/myaccount.html', {'user': user, 'favorites': favorites, 'box_favorites': box_favorites})


@login_required
def write_info(request, id):
    user = get_object_or_404(User, pk=id)
    profile = Profile.objects.get(user=user)
    string_pool = string.ascii_letters + string.digits
    random_sub_id = ''
    for i in range(9):
        random_sub_id += random.choice(string_pool)
    if user.is_superuser:
        profile.level = 'admin'
        user.last_name = '사'
        user.first_name = '무국'
        profile.phone = '02-3296-0613'
        profile.info_update_flag = True
        profile.sub_id = 'B' + random_sub_id
        user.save(update_fields=['last_name', 'first_name'])
        profile.save(update_fields=['level', 'phone', 'info_update_flag', 'sub_id'])
        return redirect('users:myaccount', user.id)
    elif 'bluemove.or.kr' in user.email:
        token = SocialToken.objects.get(account__user=request.user, account__provider='google')
        credentials = Credentials(
            client_id=client_id,
            client_secret=client_secret,
            token_uri='https://oauth2.googleapis.com/token',
            token=token.token,
            refresh_token=token.token_secret,
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        try:
            drive_response = drive_service.drives().list().execute()
        except:
            logout(request)
            return redirect('users:login_cancelled_no_scopes')
        all_drives = drive_response.get('drives')
        for drive in all_drives:
            drive_id = drive['id']
            drive_name = drive['name']
            if 'A' in drive_name:
                Adrive = drive_id
            if 'B' in drive_name:
                Bdrive = drive_id
            if 'C' in drive_name:
                Cdrive = drive_id
            if 'D' in drive_name:
                Ddrive = drive_id
            if 'F' in drive_name:
                Fdrive = drive_id
            if 'G' in drive_name:
                Gdrive = drive_id
            if 'H' in drive_name:
                Hdrive = drive_id
        try:
            drive_response = drive_service.files().list(
                corpora='allDrives',
                fields="files(id, name)",
                includeItemsFromAllDrives=True,
                orderBy="name",
                q="mimeType='application/vnd.google-apps.folder' and trashed = false and ('" + Adrive + "' in parents or '" + Bdrive + "' in parents or '" + Cdrive + "' in parents or '" + Ddrive + "' in parents or '" + Fdrive + "' in parents or '" + Gdrive + "' in parents or '" + Hdrive + "' in parents)",
                supportsAllDrives=True,
            ).execute()
        except:
            user.delete()
            return redirect('users:login_cancelled_no_drive')
        try:
            client = WebClient(token=slack_bot_token)
            slack_response = client.users_lookupByEmail(
                email = request.user.email
            )
            slack_user_data = slack_response.get('user')
            profile.slack_user_id = slack_user_data.get('id')
        except:
            user.delete()
            return redirect('users:login_cancelled_no_slack')
        profile.level = 'bluemover'
        if request.method == "POST":
            user.last_name = request.POST.get("last_name")
            user.first_name = request.POST.get("first_name")
            profile.phone = request.POST.get("phone")
            profile.info_update_flag = True
            profile.sub_id = 'B' + random_sub_id
            user.save(update_fields=['last_name', 'first_name'])
            profile.save(update_fields=['level', 'phone', 'slack_user_id', 'info_update_flag', 'sub_id'])
            # 슬랙 메시지 발신
            client = WebClient(token=slack_bot_token)
            client.chat_postMessage(
                channel = user.profile.slack_user_id,
                link_names = True,
                as_user = True,
                blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "💙 " + user.last_name + user.first_name + "님의 회원 정보 등록됨",
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "<@" + user.email.replace('@bluemove.or.kr', '').lower() + ">님의 회원 정보가 아래와 같이 등록되었습니다."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*실명:* " + user.last_name + user.first_name + "\n*회원 구분:* 블루무버\n*이메일 주소:* " + user.email + "\n*휴대전화 번호:* " + user.profile.phone[0:5] + "***" + user.profile.phone[8:10] + "***\n\n이제 블루무브 닥스에서 공지사항 및 댓글을 작성하시거나, 문서함 및 새 문서를 생성하실 수 있습니다."
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "블루무브 닥스 열기"
                                },
                                "value": "open_bluemove_docs",
                                "url": "http://docs.bluemove.or.kr/"
                            }
                        ]
                    }
                ],
                text = f"💙 " + user.last_name + user.first_name + "님의 회원 정보 등록됨",
            )
            return redirect('users:myaccount', user.id)
    elif 'gmail.com' in user.email or 'naver.com' in user.email or 'kakao.com' in user.email or 'daum.net' in user.email or 'hanmail.net' in user.email or 'nate.com' in user.email:
        profile.level = 'guest'
        if request.method == "POST":
            user.last_name = request.POST.get("last_name")
            user.first_name = request.POST.get("first_name")
            profile.phone = request.POST.get("phone")
            profile.info_update_flag = True
            profile.sub_id = 'B' + random_sub_id
            user.save(update_fields=['last_name', 'first_name'])
            profile.save(update_fields=['level', 'phone', 'info_update_flag', 'sub_id'])
            # 01. 서비스 계정 Gmail API 호출
            INSIDE_CLIENT = 'docs@bluemove.or.kr'
            user_id = 'docs@bluemove.or.kr'
            SERVICE_ACCOUNT_GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
            gmail_credentials = service_account.Credentials.from_service_account_file(
                service_account_creds,
                scopes = SERVICE_ACCOUNT_GMAIL_SCOPES,
            )
            credentials_delegated = gmail_credentials.with_subject(INSIDE_CLIENT)
            mail_service = build('gmail', 'v1', credentials = credentials_delegated)
            # 02. 메일 생성
            sender = 'Bluemove Docs ' + '<' + INSIDE_CLIENT + '>' ##### INSIDE 클라이언트 이메일 주소 INPUT #####
            to = user.email ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
            subject = user.last_name + user.first_name + "님의 회원 정보가 등록되었습니다."
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
                        <title>블루무브 닥스 - """ + user.last_name + user.first_name + """님의 회원 정보가 등록되었습니다.</title>
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
                                                                                    <h1>""" + user.last_name + user.first_name + """님의 회원 정보가 등록되었습니다.</h1>
                                                                                    <p>안녕하세요, 파란물결 블루무브입니다.<br>
                                                                                        """ + user.last_name + user.first_name + """님의 회원 정보가 아래와 같이 등록되었습니다.</p>
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
                                                                                                    <strong style="color:#222222;">실명</strong>: """ + user.last_name + user.first_name + """<br>
                                                                                                    <strong style="color:#222222;">회원 구분</strong>: 게스트<br>
                                                                                                    <strong style="color:#222222;">이메일 주소</strong>: """ + user.email + """<br>
                                                                                                    <strong style="color:#222222;">휴대전화 번호</strong>: """ + user.profile.phone[0:5] + """***""" + user.profile.phone[8:10] + """***
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

                                                                                    이제 블루무브 닥스에서 댓글을 작성하시거나 새 문서를 생성하실 수 있습니다.<br>
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
                                                                        href="http://docs.bluemove.or.kr/"
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
                                                                                            href="http://docs.bluemove.or.kr/"
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
                                                                                        이 메일은 블루무브 닥스에서 자동 발신되었습니다. 궁금하신 점이 있을 경우 사무국 연락처로 문의해주시기 바랍니다.<br>
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
            # 03. 메일 발신
            message = (
                mail_service.users().messages().send(
                    userId = user_id,
                    body = message,
                ).execute()
            )
            return redirect('users:myaccount', user.id)
    elif '.edu' in user.email or '.ac.kr' in user.email or '.hs.kr' in user.email or '.ms.kr' in user.email or '.go.kr' in user.email or '.co.kr' in user.email or '.or.kr' in user.email or '.org' in user.email:
        user.delete()
        return redirect('users:login_cancelled')
    else:
        user.delete()
        return redirect('users:login_cancelled')
    return render(request, 'users/write_info.html')


@login_required
def edit_info(request, id):
    user = get_object_or_404(User, pk=id)
    profile = Profile.objects.get(user=user)
    if request.method == "POST":
        user.last_name = request.POST.get("last_name")
        user.first_name = request.POST.get("first_name")
        profile.phone = request.POST.get("phone")
        user.save(update_fields=['last_name', 'first_name'])
        profile.save(update_fields=['phone'])
        return redirect('users:myaccount', id=user.id)
    return render(request, 'users/edit_info.html')


@login_required
def delete(request, id):
    user = get_object_or_404(User, pk=id)
    my_notices = Notice.objects.filter(writer=user)
    my_comments = Comment.objects.filter(writer=user)
    my_boxes = Box.objects.filter(writer=user)
    my_docs = Doc.objects.filter(user=user)
    my_docs_create = Doc.objects.filter(user=user, submit_flag=False, reject_flag=False, return_flag=False)
    my_docs_submit = Doc.objects.filter(user=user, submit_flag=True)
    my_docs_reject = Doc.objects.filter(user=user, reject_flag=True)
    my_docs_return = Doc.objects.filter(user=user, return_flag=True)
    my_docs_delete = Doc.objects.filter(user=user, delete_flag=True)
    if request.method == "POST":
        ###########################
        ##### bluemover일 경우 #####
        ###########################
        if user.profile.level == 'bluemover':
            # 슬랙 메시지 발신
            client = WebClient(token=slack_bot_token)
            client.chat_postMessage(
                channel = user.profile.slack_user_id,
                link_names = True,
                as_user = True,
                blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🗑 " + user.last_name + user.first_name + "님의 회원 정보 삭제됨",
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "<@" + user.email.replace('@bluemove.or.kr', '').lower() + ">님의 회원 정보가 영구적으로 삭제되었습니다."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "블루무브 닥스를 이용하시려면 회원 정보를 다시 등록하시기 바랍니다."
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "블루무브 닥스 열기"
                                },
                                "value": "open_bluemove_docs",
                                "url": "http://docs.bluemove.or.kr/"
                            }
                        ]
                    }
                ],
                text = f"🗑 " + user.last_name + user.first_name + "님의 회원 정보 삭제됨",
            )
        ########################
        ##### guest일 경우 #####
        ########################
        else:
            # 01. 서비스 계정 Gmail API 호출
            INSIDE_CLIENT = 'docs@bluemove.or.kr'
            user_id = 'docs@bluemove.or.kr'
            SERVICE_ACCOUNT_GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
            gmail_credentials = service_account.Credentials.from_service_account_file(
                service_account_creds,
                scopes = SERVICE_ACCOUNT_GMAIL_SCOPES,
            )
            credentials_delegated = gmail_credentials.with_subject(INSIDE_CLIENT)
            mail_service = build('gmail', 'v1', credentials = credentials_delegated)
            # 02. 메일 생성
            sender = 'Bluemove Docs ' + '<' + INSIDE_CLIENT + '>' ##### INSIDE 클라이언트 이메일 주소 INPUT #####
            to = user.email ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
            subject = user.last_name + user.first_name + "님의 회원 정보가 삭제되었습니다."
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
                        <title>블루무브 닥스 - """ + user.last_name + user.first_name + """님의 회원 정보가 삭제되었습니다.</title>
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
                                                                                    <h1>""" + user.last_name + user.first_name + """님의 회원 정보가 삭제되었습니다.</h1>
                                                                                    <p style="margin-bottom:0;">안녕하세요, 파란물결 블루무브입니다.<br>
                                                                                        """ + user.last_name + user.first_name + """님의 회원 정보가 영구적으로 삭제되었습니다.<br>
                                                                                        그동안 블루무브 닥스를 이용해주셔서 감사합니다.</p><br>
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
                                                                        href="http://docs.bluemove.or.kr/"
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
                                                                                            href="http://docs.bluemove.or.kr/"
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
                                                                                        이 메일은 블루무브 닥스에서 자동 발신되었습니다. 궁금하신 점이 있을 경우 사무국 연락처로 문의해주시기 바랍니다.<br>
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
            # 03. 메일 발신
            message = (
                mail_service.users().messages().send(
                    userId = user_id,
                    body = message,
                ).execute()
            )
        user.delete()
        return redirect('users:login_deleted')
    return render(request, 'users/delete.html', {
        'my_notices': my_notices,
        'my_comments': my_comments,
        'my_boxes': my_boxes,
        'my_docs': my_docs,
        'my_docs_create': my_docs_create,
        'my_docs_submit': my_docs_submit,
        'my_docs_reject': my_docs_reject,
        'my_docs_return': my_docs_return,
        'my_docs_delete': my_docs_delete
        })

def login_cancelled(request):
    return render(request, 'users/login_cancelled.html')


def login_cancelled_no_scopes(request):
    return render(request, 'users/login_cancelled_no_scopes.html')


def login_cancelled_no_token(request):
    return render(request, 'users/login_cancelled_no_token.html')


def login_cancelled_no_drive(request):
    return render(request, 'users/login_cancelled_no_drive.html')


def login_cancelled_no_slack(request):
    return render(request, 'users/login_cancelled_no_slack.html')


def login_cancelled_delete(request, id):
    try:
        user = get_object_or_404(User, pk=id)
        user.delete()
    except:
        None
    return render(request, 'users/login_cancelled_delete.html')


def login_deleted(request):
    return render(request, 'users/login_deleted.html')