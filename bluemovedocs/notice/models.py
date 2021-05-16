from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from ckeditor.fields import RichTextField
from allauth.socialaccount.models import SocialAccount
from slack_sdk import WebClient
import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
from email.mime.text import MIMEText
import base64
import textwrap
import re
from django.conf import settings


slack_bot_token = getattr(settings, 'SLACK_BOT_TOKEN', 'SLACK_BOT_TOKEN')
service_account_creds = "bluemove-docs-9f4ec6cf5006.json"


class Notice(models.Model):

    CATEGORY_CHOICES = {
        ('bluemover', '블루무버'),
        ('guest', '게스트'),
    }

    title = models.CharField(max_length = 50)
    old_title = models.CharField(max_length = 50, null=True, blank=True)
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length = 50, choices = CATEGORY_CHOICES)
    channel_id = models.CharField(max_length = 50)
    channel_name = models.CharField(max_length = 50)
    content = RichTextField()
    # content = models.TextField()
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    created_at = models.DateField(auto_now_add = True)
    updated_at = models.DateField(auto_now = True)
    favorite_user_set = models.ManyToManyField(User, blank=True, related_name="favorite_user_set", through="Favorite")

    @property
    def favorite_count(self):
        return self.favorite_user_set.count()


@receiver(pre_save, sender=Notice)
def send_noti(sender, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass # Object is new, so field hasn't technically changed, but you may want to do something else here.
    else:
        if obj.category != instance.category or obj.title != instance.title or obj.content != instance.content: # obj가 원본, ins가 수정본
            if instance.category == 'bluemover':
                instance_category = '블루무버'
            else:
                instance_category = '게스트'
            for i in range(obj.favorite_count):
                favorite_user_id = obj.favorite_user_set.values()[i].get('id')
                user = User.objects.get(pk=favorite_user_id)
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
                                    "text": "📑 북마크에 있는 '" + obj.title + "' 업데이트됨",
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "<@" + user.email.replace('@bluemove.or.kr', '').lower() + ">님, 공지사항 '" + obj.title + "'의 업데이트를 확인하세요."
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "```대상: " + instance_category + "\n제목: " + instance.title + "\n작성자: " + obj.writer.last_name + obj.writer.first_name + "\n내용: " + textwrap.shorten(re.sub(pattern='<[^>]*>', repl='', string=instance.content).replace('&nbsp;', ' '), width=100) + "```"
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*이메일 주소:*\n" +  obj.writer.email + "\n*수정일:* " + datetime.date.today().strftime('%Y-%m-%d')
                                },
                                "accessory": {
                                    "type": "image",
                                    "image_url": SocialAccount.objects.filter(user=obj.writer)[0].extra_data['picture'],
                                    "alt_text": obj.writer.last_name + obj.writer.first_name + "님의 프로필 사진"
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
                                        "url": "http://docs.bluemove.or.kr/notice/" + str(obj.id)
                                    }
                                ]
                            }
                        ],
                        text = f"📑 북마크에 있는 '" + obj.title + "' 업데이트됨",
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
                    subject = user.last_name + user.first_name + "님, " + obj.title + "의 업데이트를 확인하세요."
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
                                <title>블루무브 닥스 - """ + user.last_name + user.first_name + """님, 공지사항 업데이트를 확인하세요.</title>
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
                                                                                            <h1>""" + user.last_name + user.first_name + """님, 공지사항 업데이트를 확인하세요.</h1>
                                                                                            <p>안녕하세요, 파란물결 블루무브입니다.<br>
                                                                                                """ + user.last_name + user.first_name + """님의 북마크에 있는 공지사항이 아래와 같이 업데이트 되었습니다.</p>
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
                                                                                                            <strong style="color:#222222;">대상</strong>: """ + instance_category + """<br>
                                                                                                            <strong style="color:#222222;">제목</strong>: """ + instance.title + """<br>
                                                                                                            <strong style="color:#222222;">작성자</strong>: """ + obj.writer.last_name + obj.writer.first_name + """<br>
                                                                                                            <strong style="color:#222222;">내용</strong>: """ + textwrap.shorten(re.sub(pattern='<[^>]*>', repl='', string=instance.content).replace('&nbsp;', ' '), width=100) + """<br>
                                                                                                            <strong style="color:#222222;">수정일</strong>: """ + datetime.date.today().strftime('%Y-%m-%d') + """
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

                                                                                            더 이상 알림을 원치 않으실 경우 북마크에서 제거해주시기 바랍니다.<br>
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
                                                                                href="http://docs.bluemove.or.kr/notice/""" + str(obj.id) + """"
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
                                                                                                    href="http://docs.bluemove.or.kr/notice/""" + str(obj.id) + """"
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
                                                                                                이 메일은 블루무브 닥스에서 자동 발신되었습니다. 궁금한 점이 있으실 경우 <a href="mailto:management@bluemove.or.kr">management@bluemove.or.kr</a>로 문의해주시기 바랍니다.<br>
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


class Comment(models.Model):
    content = models.TextField(null = False)
    avatar_src = models.TextField(null = True)
    writer = models.ForeignKey(User, on_delete = models.CASCADE)
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='comments')
    mentioned_users = models.TextField(null=True, blank=True)
    created_at = models.DateField(auto_now_add = True)
    updated_at = models.DateField(auto_now = True)


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    class Meta:
        unique_together = (('user','notice'))