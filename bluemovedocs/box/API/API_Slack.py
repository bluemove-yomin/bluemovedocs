# import requests

# def main():
#     webhook_url = "VALUE"
#     payload = {
#         "blocks": [
#             {
#                 "type": "header",
#                 "text": {
#                     "type": "plain_text",
#                     "text": "📩 새 문서가 접수되었습니다."
#                 }
#             },
#             {
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": "*<https://docs.google.com|블루무브닥스_4기블루무버지원서이상준_210128>*"
#                 }
#             },
#             {
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": "*문서명:*\n4기 블루무버 지원서\n\n*제출자:*\n이상준 (sangjun@gmail.com)\n\n*제출일자:*\n2021-01-28"
#                 },
#                 "accessory": {
#                     "type": "image",
#                     "image_url": "https://api.slack.com/img/blocks/bkb_template_images/approvalsNewDevice.png",
#                     "alt_text": "computer thumbnail"
#                 }
#             },
#             {
#                 "type": "actions",
#                 "elements": [
#                     {
#                         "type": "button",
#                         "text": {
#                             "type": "plain_text",
#                             "text": "문서함 열기"
#                         },
#                         "value": "click_me_123",
#                         "url": "http://127.0.0.1:8000/box/7/#boxListPosition"
#                     }
#                 ]
#             }
#         ]
#     }
#     requests.post(webhook_url, json = payload)

################################################

# import os
# from slack_bolt import App


# API_Slack = App(
#     token='VALUE',
#     signing_secret='VALUE'
# )


# @API_Slack.message("안녕!")
# def message_hello(message, say):
#     say(f"안녕하세요, <@{message['user']}>님!")


# @API_Slack.message("버튼")
# def message_button(message, say):
#     say(
#         channel="VALUE",
#         blocks=[
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"안녕하세요, <@{message['user']}>님!"},
#                 "accessory": {
#                     "type": "button",
#                     "text": {"type": "plain_text", "text": "이것은 버튼입니다."},
#                     "action_id": "button_click"
#                 }
#             }
#         ],
#         text=f"안녕하세요, <@{message['user']}>님!",
#     )


# @API_Slack.action("button_click")
# def action_button_click(body, ack, say):
#     ack()
#     say(f"<@{body['user']['id']}>님께서 버튼을 누르셨습니다.")


# if __name__ == "__main__":
#     API_Slack.start(port=int(os.environ.get("PORT", 8000)))

###############################################################

from slack_sdk import WebClient


def main():
    slack_bot_token = "VALUE"

    client = WebClient(token=slack_bot_token)
    slack_response = client.conversations_list(
        team_id = 'T2EH6PN00',
        types = "public_channel, im"
    )
    all_channels = slack_response.get('channels')
    # return print(all_channels)
    for channels_info in all_channels:
        channels_name = channels_info.get('name')
        print(channels_name)


if __name__ == "__main__":
    main()