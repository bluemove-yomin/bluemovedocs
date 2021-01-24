import base64
import jwt
import time
import json
import requests
from email.mime.text import MIMEText
from googleapiclient.discovery import build
# from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account


# def gmailTestJWT():
#     # 01. 서비스 계정 JWT 생성
#     PRIVATE_KEY_ID_FROM_JSON ="6a11a86cda0e6fe100bfa8fb36482d572883580e"
#     PRIVATE_KEY_FROM_JSON= "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDUi2qvbOIk81kt\n5vu+I3njYqf+b0qYMqrvC1PcDJb6fsxBFxW2g5UNweW2lUdFirM+dZqINEAqwQMP\nls6efPlnTaPvU6CVrSToxnpQpBQDOmAAdvzWfAM9M6/yZu4nJOG5BebUW6xEV+Bv\n6EzwR1a/AOyOoxmF/WIjfxgqZsD7K0sGQnxVkCRXLj0P6K7xC43cCF56H1UnGgZ9\n2lG9Nz3uOCSpD5gdmig/uSxPPBL7NLKK8yQLT23tIP71dt5Ym2MJn7/5uzLiRHN1\n7xka3Ul51cRR5izHbbEvmqUYr2dQMISnPIXbkMOCRH9aO8eBGRN2Lx9IXb1MV//z\nLukvJg7/AgMBAAECggEADivl89POnkhL3WrykeJuqZhPe2aZpcOj49owmYVZxoXD\nm645qEvMsx6gpBRlX9mLV8vimL59h5XX9oDUWC5QBZdgXPNv/rRzng7bYyevHlBh\nmOMi7fzvZsDDNGZKVPmfqhHR94qab77solMhJViavy1SGIHMEJC5xVEfk0NhQaRD\nT/JDa9wnB9aEWAPbhw3nMvkrHM7JdFDliDUlbVxHYoBTeZzetqrFxBML/NRrpwV9\nFNAVVMuuj9KbyxWGiPkZQwCEfXF2cLKlTdBh5x6DLq23okN7wot+0fZYZ3jnfxfr\nsNJyYAZecpu1Pv8wnrYMhUDDxDnzRApsWueLDZE71QKBgQDwsFn5MxONPbm8+Cxi\nOlQn2LlJfCuS+smpX44rxOVFqX2/S5tFDwxx5cMec/Jh3H5AszblD6i1Ug6Z7urb\nmUGwlq93s5y3ID4+u/f8aUiI3pUm/Akfg8TKxiUR+3kAZthUvG3cihGhvUBnxdRz\n0UTk0IiuxaCUKM1Bfzhf4Il8MwKBgQDiELtxyse887GwGHlAj/1gHWGaBF+HPfTx\nyjeYNfsXUF/NFQXWQyD4ZE56pRoUp2PB3r6EPOWaaR+xStOxzOAwb8C2KKFJpvnr\np8f9sLUOYoA5ydf9GVWkBo7DLqoglf0GCbhzr2l8e/33fgWeD42Yyq7JaJLhU1ei\naZZygszWBQKBgAPrKxvWjAvxpFOCSt6yimo3qhSbM+5prNzYFG18ACuZLdXuejGu\npAo6rmmRg7G6MEgHYu5pydph4qD49dPrc9lXKrYtM3D70medEdWHNUodLZp74f4k\nXBDdFv9q87Zg9kay5qr/iHf0p9bIrsPP9WowRvlpeErROz5Evvs4oaRnAoGAMjhj\nW8kfjDNa8vLM5PHX6OU+DHgSPLof0yMILLE5QZmiXq3f6RRqm6O053wMCjCRcb0o\n97mLjDz0RG+KDcKkvz3kQtNN2U3V0Wspe4so/bQWJkBX0isxokmup1+Tfb+0QQYh\nytlaBsSIy9VcLBvqadoE8Eth7dqU6kiomnHCTX0CgYBjmbR2U20tymxdeNGWpLNF\nvQcqBxxyUW4q5MGc5qRRo8T6sSizbBKzrGt6nPDhLmFQ4krn5lh1Mh/J2mKSq04b\nrfENyBbWpHvnmyGy42DEpK+UCun047ltrp3kXkCmkeXO/3Kf4W0qKrRuEACH0xqb\nq8e8VGhBru0JwFqaHpBRPw==\n-----END PRIVATE KEY-----\n"
#     iat = time.time()
#     exp = iat + 3600
#     payload = {
#         'iss': 'bluemove-service@bluemove-docs.iam.gserviceaccount.com',
#         'scope': 'https://www.googleapis.com/auth/gmail.send',
#         'aud':'https://oauth2.googleapis.com/token',
#         'iat': iat,
#         'exp': exp,
#     }
#     additional_headers = {'kid': PRIVATE_KEY_ID_FROM_JSON}
#     signed_jwt = jwt.encode(payload, PRIVATE_KEY_FROM_JSON, headers = additional_headers, algorithm = 'RS256')
#     URL = 'https://oauth2.googleapis.com/token'
#     data = {
#         'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
#         'assertion': signed_jwt,
#     }
#     response = requests.post(URL, data = data)
#     access_token = response.json()['access_token']
#     # 02. 메일 생성
#     sender = 'bluemove-docs@bluemove.or.kr'
#     to = 'ssongyo@gmail.com' ##### 나중에 doc.user.email로 바꾸기 #####
#     subject = '[Bluemove Docs] OOO님의 OOO가 정상적으로 제출되었습니다.' ##### 나중에 이름이랑 문서명 채워넣기 #####
#     message_text = r"<h1>테스트</h1><p>테스트</p><strong>감사합니다</strong>"
#     message = MIMEText(message_text, 'html')
#     message['from'] = sender
#     message['to'] = to
#     message['subject'] = subject
#     message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')}
#     # 03. Gmail API 호출 및 메일 전송
#     user_id = 'ssongyo@gmail.com' ##### 나중에 doc.user.email로 바꾸기 #####
#     URL = 'https://www.googleapis.com/gmail/v1/users/' + user_id + '/messages/send'
#     request_header = {
#         "Authorization": "Bearer " + access_token,
#         "Content-Type": "application/json",
#         "X-GFE-SSL": "yes",
#     }
#     payload = message
#     response = requests.post(URL, headers = request_header, data=json.dumps(payload))
#     return print(response.text)


def gmailTest():
    # 01. 서비스 계정 Gmail API 호출
    INSIDE_CLIENT = 'Sangjun@bluemove.or.kr' ##### 나중에 doc.box.writer.email로 바꾸기 #####
    user_id = 'Sangjun@bluemove.or.kr' ##### 나중에 doc.box.writer.email로 바꾸기 #####
    SERVICE_ACCOUNT_SCOPES = ['https://mail.google.com/']
    credentials = service_account.Credentials.from_service_account_file(
        'bluemove-docs-6a11a86cda0e.json',
        scopes = SERVICE_ACCOUNT_SCOPES,
    )
    credentials_delegated = credentials.with_subject(INSIDE_CLIENT)
    mail_service = build('gmail', 'v1', credentials = credentials_delegated)

    # 02. 메일 생성
    sender = 'Sangjun at Bluemove <' + 'Sangjun@bluemove.or.kr' + '>' ##### 나중에 doc.box.writer.email'로 바꾸기 #####
    to = 'ssongyo@gmail.com' ##### 나중에 doc.user.email로 바꾸기 #####
    subject = 'OOO가 정상적으로 제출되었습니다.' ##### 나중에 문서명 채워넣기 #####
    message_text = "<h1>테스트</h1><p>테스트</p><strong>감사합니다</strong>" ##### 나중에 템플릿 만들어 넣기 #####
    message = MIMEText(message_text, 'html')
    message['from'] = sender
    message['to'] = to
    message['subject'] = subject
    message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')}
    print('메일이 생성되었습니다.')

    # 03. 메일 전송
    message = (
        mail_service.users().messages().send(
            userId = user_id,
            body = message,
        ).execute()
    )
    message_id = message['id']
    print('메일이 전송되었습니다.\nMessage Id: %s' % message['id'])

print(gmailTest())