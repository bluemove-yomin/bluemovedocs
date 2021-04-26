from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from allauth.socialaccount.models import SocialAccount
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
from .forms import NoticeContentForm
from users.models import Profile
from slack_sdk import WebClient
import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
from email.mime.text import MIMEText
import base64
from django.conf import settings


slack_bot_token = getattr(settings, 'SLACK_BOT_TOKEN', 'SLACK_BOT_TOKEN')
service_account_creds = "bluemove-docs-9f4ec6cf5006.json"


# @permission_required('auth.add_permission', raise_exception=True)
@login_required
def write(request):
    form = NoticeContentForm()
    # Slack 채널 불러오기 시작
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
    # Slack 채널 불러오기 끝
    return render(request, 'notice/write.html', {'form': form, 'channels_list': channels_list})


# @permission_required('auth.add_permission', raise_exception=True)
@login_required
def create(request):
    if request.method == "POST" and request.user.profile.level == 'bluemover':
        form = NoticeContentForm(request.POST, request.FILES)
        if form.is_valid():
            notice_category = request.POST.get('category')
            notice_title = request.POST.get('title')
            notice_channel_id = request.POST.get('channel_id').split('#')[0]
            notice_channel_name = request.POST.get('channel_id').split('#')[1]
            notice_writer = request.user
            notice_image = request.FILES.get('image')
            form.save(category=notice_category, title=notice_title, channel_id = notice_channel_id, channel_name = notice_channel_name, writer = notice_writer, image=notice_image)
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
        mentioned_users = request.POST.get('mention_name')[0:-1]
        # 댓글에 멘션된 유저에게 알림 발신
        if not request.POST.get('mention') == '':
            mentioned_users_id_list = request.POST.get('mention').split('@')
            for i in range(1, len(mentioned_users_id_list)):
                mentioned_users_id = mentioned_users_id_list[i]
                user = User.objects.get(pk=mentioned_users_id)
                if comment_writer.profile.level == 'bluemover':
                    comment_writer_level = '블루무버'
                elif comment_writer.profile.level == 'guest':
                    comment_writer_level = '게스트'
                else:
                    comment_writer_level = '알 수 없음'
                if user.profile.level == 'bluemover':
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
                                    "text": "💬 " + user.last_name + user.first_name + "님이 " + comment_writer.last_name + comment_writer.first_name + "님의 댓글에 멘션됨",
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "<@" + user.email.replace('@bluemove.or.kr', '').lower() + ">님, '" + notice.title + "'에서 " + comment_writer.last_name + comment_writer.first_name + "님의 댓글에 멘션되셨습니다."
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "```" + mentioned_users + " " + comment_content + "```"
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*이메일 주소:*\n" +  comment_writer.email + "\n*작성일자:* " + datetime.date.today().strftime('%Y-%m-%d')
                                },
                                "accessory": {
                                    "type": "image",
                                    "image_url": comment_avatar_src,
                                    "alt_text": comment_writer.last_name + comment_writer.first_name + "님의 프로필 사진"
                                }
                            },
                            {
                                "type": "actions",
                                "elements": [
                                    {
                                        "type": "button",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "공지사항 열기"
                                        },
                                        "value": "open_notice",
                                        "url": "http://127.0.0.1:8000/notice/" + str(notice.id) + "/#commentBoxPosition"
                                    }
                                ]
                            }
                        ],
                        text = f"💬 " + user.last_name + user.first_name + "님이 " + comment_writer.last_name + comment_writer.first_name + "님의 댓글에 멘션됨",
                    )
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
                    to = user.email ##### 멘션된 유저 이메일 주소 INPUT #####
                    subject = user.last_name + user.first_name + "님께서 댓글에 멘션되셨습니다."
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
                                <title>블루무브 닥스 - """ + user.last_name + user.first_name + """님께서 댓글에 멘션되셨습니다.</title>
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
                                                                                            <h1>""" + user.last_name + user.first_name + """님께서 댓글에 멘션되셨습니다.</h1>
                                                                                            <p>안녕하세요, 파란물결 블루무브입니다.<br>
                                                                                                """ + user.last_name + user.first_name + """님께서 """ + comment_writer.last_name + comment_writer.first_name + """님의 댓글에 멘션되셨습니다.</p>
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
                                                                                                            <strong style="color:#222222;">작성자</strong>: """ + comment_writer.last_name + comment_writer.first_name + """<br>
                                                                                                            <strong style="color:#222222;">회원 구분</strong>: """ + comment_writer_level + """<br>
                                                                                                            <strong style="color:#222222;">작성일자</strong>: """ + datetime.date.today().strftime('%Y-%m-%d') + """<br>
                                                                                                            <strong style="color:#222222;">내용</strong>: """ + comment_content + """
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

                                                                                            댓글의 수정 및 삭제 내역에 대해서는 별도의 알림이 발신되지 않습니다.<br>
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
                                                                                href="http://127.0.0.1:8000/notice/""" + str(notice.id) + """/#commentBoxPosition"
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
                                                                                                    title="블루무브 닥스 공지사항 열기"
                                                                                                    href="http://127.0.0.1:8000/notice/""" + str(notice.id) + """/#commentBoxPosition"
                                                                                                    target="_blank"
                                                                                                    style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">블루무브 닥스 공지사항 열기</a>
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
                                                                                                이 메일은 블루무브 닥스를 통해 자동 발신되었습니다. 궁금하신 점이 있을 경우 사무국 연락처로 문의해주시기 바랍니다.<br>
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
        # 연동 Slack 채널에 메시지 발신
        client = WebClient(token=slack_bot_token)
        if mentioned_users != '':
            client.chat_postMessage(
                channel = notice.channel_id,
                link_names = True,
                as_user = True,
                blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "💬 " + comment_writer.last_name + comment_writer.first_name + "님이 '" + notice.title + "'에 댓글 남김",
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "<@" + notice.writer.email.replace('@bluemove.or.kr', '').lower() + ">님, " + comment_writer.last_name + comment_writer.first_name + "님이 남긴 댓글을 확인하세요."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "```" + mentioned_users + " " + comment_content + "```"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*이메일 주소:*\n" +  comment_writer.email + "\n*작성일자:* " + datetime.date.today().strftime('%Y-%m-%d')
                        },
                        "accessory": {
                            "type": "image",
                            "image_url": comment_avatar_src,
                            "alt_text": comment_writer.last_name + comment_writer.first_name + "님의 프로필 사진"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "공지사항 열기"
                                },
                                "value": "open_notice",
                                "url": "http://127.0.0.1:8000/notice/" + str(notice.id) + "/#commentBoxPosition"
                            }
                        ]
                    }
                ],
                text = f"💬 " + comment_writer.last_name + comment_writer.first_name + "님이 '" + notice.title + "'에 댓글 남김",
            )
        else:
            client.chat_postMessage(
                channel = notice.channel_id,
                link_names = True,
                as_user = True,
                blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "💬 " + comment_writer.last_name + comment_writer.first_name + "님이 '" + notice.title + "'에 댓글 남김",
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "<@" + notice.writer.email.replace('@bluemove.or.kr', '').lower() + ">님, " + comment_writer.last_name + comment_writer.first_name + "님이 남긴 댓글을 확인하세요."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "```" + comment_content + "```"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*이메일 주소:*\n" +  comment_writer.email + "\n*작성일자:* " + datetime.date.today().strftime('%Y-%m-%d')
                        },
                        "accessory": {
                            "type": "image",
                            "image_url": comment_avatar_src,
                            "alt_text": comment_writer.last_name + comment_writer.first_name + "님의 프로필 사진"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "공지사항 열기"
                                },
                                "value": "open_notice",
                                "url": "http://127.0.0.1:8000/notice/" + str(notice.id) + "/#commentBoxPosition"
                            }
                        ]
                    }
                ],
                text = f"💬 " + comment_writer.last_name + comment_writer.first_name + "님이 '" + notice.title + "'에 댓글 남김",
            )
        Comment.objects.create(avatar_src=comment_avatar_src, writer=comment_writer, content=comment_content, notice=notice, mentioned_users=mentioned_users)
    return redirect('notice:read', notice.id)


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


# @permission_required('auth.add_permission', raise_exception=True)
@login_required
def update(request, id):
    notice = get_object_or_404(Notice, pk=id)
    form = NoticeContentForm(instance=notice)
    # Slack 채널 불러오기 시작
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
    # Slack 채널 불러오기 끝
    if request.method == "POST":
        form = NoticeContentForm(request.POST, instance=notice)
        if form.is_valid():
            notice_category = request.POST.get('category')
            notice_title = request.POST.get('title')
            notice_channel_id = request.POST.get('channel_id').split('#')[0]
            notice_channel_name = request.POST.get('channel_id').split('#')[1]
            form.update(category=notice_category, title=notice_title, channel_id=notice_channel_id, channel_name=notice_channel_name)
        return redirect('notice:read', notice.id)
    return render(request, 'notice/update.html', {'notice': notice, 'form': form, 'channels_list': channels_list})


# @permission_required('auth.add_permission', raise_exception=True)
@login_required
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
    page = request.GET.get('page', 1)
    paginator = Paginator(all_notices, 10)
    try:
        all_notices = paginator.page(page)
    except PageNotAnInteger:
        all_notices = paginator.page(1)
    except EmptyPage:
        all_notices = paginator.page(paginator.num_pages)
    if request.method == "POST":
        comment.content = request.POST['content']
        comment.save()
        return redirect('notice:read', id=comment.notice.id)
    return render(request, 'notice/updatecomment.html', {'comment': comment, 'notice': notice, 'all_notices': all_notices, 'all_comments': all_comments})


# @permission_required('auth.add_permission', raise_exception=True)
@login_required
def delete(request, id):
    notice = get_object_or_404(Notice, pk=id)
    notice.delete()
    return redirect('notice:main')


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.delete()
    return redirect('notice:read', id=comment.notice.id)