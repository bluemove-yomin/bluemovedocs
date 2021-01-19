from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

def main():
    ##### 00. OUTSIDE 클라이언트 Google Drive API 호출
    # SCOPES = ['https://www.googleapis.com/auth/drive']
    # creds = None
    # if os.path.exists('token.pickle'):
    #     with open('token.pickle', 'rb') as token:
    #         creds = pickle.load(token)
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file(
    #             'credentials.json', SCOPES)
    #         creds = flow.run_local_server(port=8000)
    #     with open('token.pickle', 'wb') as token:
    #         pickle.dump(creds, token)
    # drive_service = build('drive', 'v3', credentials=creds)
    # if drive_service:
    #     print('01. OUTSIDE 클라이언트 Google Drive API 호출에 성공했습니다.')
    # else:
    #     print('01. OUTSIDE 클라이언트 Google Drive API 호출에 실패했습니다.')

    ##### 00. 서비스 계정 My Drive 내 블루무브 닥스 폴더 생성
    # file = drive_service.files().create(
    #     body = {
    #         'name': '블루무브 닥스', ##### 폴더 이름 INPUT #####
    #         'mimeType': 'application/vnd.google-apps.folder'
    #     },
    #     fields = 'id'
    # ).execute()
    # folder_id = file.get('id') ##### 폴더 ID OUTPUT #####
    # if folder_id:
    #     print('02. 서비스 계정 My Drive 내 블루무브 닥스 폴더 생성에 성공했습니다. 폴더 ID: %s' % folder_id)
    # else:
    #     print('02. 서비스 계정 My Drive 내 블루무브 닥스 폴더 생성에 실패했습니다!!!')

    # 01. 서비스 계정 Google Drive, Google Docs API 호출
    SERVICE_ACCOUNT_SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
    creds = ServiceAccountCredentials.from_json_keyfile_name (
        'bluemove-docs-64c12e189ad5.json',
        SERVICE_ACCOUNT_SCOPES,
    )
    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)
    if drive_service:
        print('01-A. 서비스 계정 Google Drive API 호출에 성공했습니다.')
    else:
        print('01-A. 서비스 계정 Google Drive API 호출에 실패했습니다!!!')
    if docs_service:
        print('01-B. 서비스 계정 Google Docs API 호출에 성공했습니다.')
    else:
        print('01-B. 서비스 계정 Google Docs API 호출에 실패했습니다!!!')

    ##### 00. 테스트 파일 또는 폴더 삭제
    # drive_response = drive_service.files().delete(
    #     fileId = '19UJqme6cNd-vtfy-Oxn-5PQ8dx4ammGE',
    # ).execute()
    # return print('00. 테스트 파일 또는 폴더 삭제에 성공했습니다.')

    # 02. 서비스 계정 My Drive 내 템플릿 문서 생성(복사)
    application_id = '1mRPI5haxz1IrjDw5oXVIXYSd89HKB_8hOhGxC09sq58' ##### 템플릿 문서 ID INPUT #####
    drive_response = drive_service.files().copy(
        fileId = application_id,
        body = {
            'name': '4기 블루무버 지원서 - ' + ##### 문서 이름 INPUT #####
                    '성' + '이름', ##### OUTSIDE 클라이언트 성명 INPUT #####
            'description': '블루무브 닥스에서 생성된 ' +
                           '성' + '이름' + ##### OUTSIDE 클라이언트 성명 INPUT #####
                           '님의 ' +
                           '4기 블루무버 지원서' ##### 문서 이름 INPUT #####
                           + '입니다.\n\n' + ##### OUTSIDE 클라이언트 성명 INPUT #####
                           '📧 생성일자: ' + '2021-01-20', ##### 현재 일자 INPUT #####
        },
        fields = 'id, name'
    ).execute()
    file_id = drive_response.get('id') ##### 문서 ID OUTPUT #####
    name = drive_response.get('name') ##### 문서 이름 + OUTSIDE 클라이언트 성명 OUTPUT #####
    if file_id:
        print('02-A. 서비스 계정 My Drive 내 템플릿 문서 생성에 성공했습니다. 파일 ID: %s' % file_id)
    else:
        print('02-A. 서비스 계정 My Drive 내 템플릿 문서 생성에 실패했습니다!!!')
    if name:
        print('02-B. 서비스 계정 My Drive 내 템플릿 문서 생성에 성공했습니다. 문서 이름: %s' % name)
    else:
        print('02-B. 서비스 계정 My Drive 내 템플릿 문서 생성에 실패했습니다!!!')

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
                        'replaceText': '성' + '이름', ##### OUTSIDE 클라이언트 성명 INPUT #####
                    }
                },
                {
                    'replaceAllText': {
                        'containsText': {
                            'text': '{{user-phone}}',
                            'matchCase':  'true'
                        },
                        'replaceText': '010-1234-5678', ##### OUTSIDE 클라이언트 휴대전화 번호 INPUT #####
                    }
                },
                {
                    'replaceAllText': {
                        'containsText': {
                            'text': '{{user-email}}',
                            'matchCase':  'true'
                        },
                        'replaceText': 'example@example.com', ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
                    }
                }
            ]
        }
    ).execute()
    if docs_response:
        print('03. 문서 내 템플릿 태그 적용에 성공했습니다.')
    else:
        print('03. 문서 내 템플릿 태그 적용에 실패했습니다!!!')

    # 04. 서비스 계정 권한 ID 조회
    drive_response = drive_service.permissions().list(
        fileId=file_id,
    ).execute()
    permissions_list = drive_response.get('permissions')
    for permissions_data in permissions_list:
        permission_id = permissions_data['id']
        if permission_id:
            print('04. 서비스 계정 권한 ID 조회에 성공했습니다. 서비스 계정 권한 ID: %s' % permission_id)
        else:
            print('04. 서비스 계정 권한 ID 조회에 실패했습니다!!!')

    # 05. OUTSIDE 클라이언트 권한 추가 writer
    drive_response = drive_service.permissions().create(
        fileId = file_id,
        body = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': 'ssongyo@gmail.com', ##### OUTSIDE 클라이언트 이메일 주소 INPUT #####
        },
    ).execute()
    outside_permission_id = drive_response.get('id') ##### OUTSIDE 클라이언트 권한 ID OUTPUT #####
    if outside_permission_id:
        print('05. OUTSIDE 클라이언트 권한 추가 writer에 성공했습니다. OUTSIDE 클라이언트 권한 ID: %s' % outside_permission_id)
    else:
        print('05. OUTSIDE 클라이언트 권한 추가 writer에 실패했습니다!!!')

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
    if drive_response:
        print('06. 문서 잠그기에 성공했습니다.')
    else:
        print('06. 문서 잠그기에 실패했습니다!!!')

    # 07. OUTSIDE 클라이언트 권한 변경 writer 2 reader
    drive_response = drive_service.permissions().update(
        fileId = file_id,
        permissionId = outside_permission_id,
        body = {
            'role': 'reader',
        },
    ).execute()
    if drive_response:
        print('07. OUTSIDE 클라이언트 권한 변경 writer 2 reader에 성공했습니다.')
    else:
        print('07. OUTSIDE 클라이언트 권한 변경 writer 2 reader에 실패했습니다!!!')

    # 08. 문서 이름 및 설명 변경
    drive_response = drive_service.files().update(
        fileId = file_id,
        body = {
            'name': '4기 블루무버 지원서 - ' + ##### 문서 이름 INPUT #####
                    '성' + '이름', ##### OUTSIDE 클라이언트 성명 INPUT #####
            'description': '블루무브 닥스에서 생성된 ' +
                           '성' + '이름' + ##### OUTSIDE 클라이언트 성명 INPUT #####
                           '님의 ' +
                           '4기 블루무버 지원서' ##### 문서 이름 INPUT #####
                           + '입니다.\n\n' + ##### OUTSIDE 클라이언트 성명 INPUT #####
                           '📧 생성일자: ' + '2021-01-20\n' + ##### 현재 일자 INPUT #####
                           '📨 제출일자: ' + '2021-01-20\n', ##### 08 일자 INPUT #####
        },
        fields = 'name'
    ).execute()
    name = drive_response.get('name') ##### 문서 이름 + OUTSIDE 클라이언트 성명 OUTPUT #####
    if name:
        print('08. 문서 이름 및 설명 변경에 성공했습니다.')
    else:
        print('08. 문서 이름 및 설명 변경에 실패했습니다!!!')

    # 09. INSIDE 클라이언트 권한 추가 writer
    drive_response = drive_service.permissions().create(
        fileId = file_id,
        body = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': 'tejava@bluemove.or.kr', ##### INSIDE 클라이언트 이메일 주소 INPUT #####
        },
    ).execute()
    inside_permission_id = drive_response.get('id') ##### INSIDE 클라이언트 권한 ID OUTPUT #####
    if inside_permission_id:
        print('09. INSIDE 클라이언트 권한 추가 writer에 성공했습니다. INSIDE 클라이언트 권한 ID: %s' % inside_permission_id)
    else:
        print('09. INSIDE 클라이언트 권한 추가 writer에 실패했습니다!!!')

    # 10. INSIDE 클라이언트 권한 삭제 writer 2 none
    drive_response = drive_service.permissions().delete(
        fileId = file_id,
        permissionId = inside_permission_id,
    ).execute()
    print('10. INSIDE 클라이언트 권한 삭제 writer 2 none에 성공했습니다.')

    # 11. OUTSIDE 클라이언트 권한 변경 reader 2 owner
    drive_response = drive_service.permissions().update(
        fileId = file_id,
        permissionId = outside_permission_id,
        transferOwnership = True,
        body = {
            'role': 'owner',
        },
    ).execute()
    if drive_response:
        print('11. OUTSIDE 클라이언트 권한 변경 reader 2 owner에 성공했습니다.')
    else:
        print('11. OUTSIDE 클라이언트 권한 변경 reader 2 owner에 실패했습니다!!!')

    # 12. 문서 이름 및 설명 변경
    drive_response = drive_service.files().update(
        fileId = file_id,
        body = {
            'name': '4기 블루무버 지원서 - ' + ##### 문서 이름 INPUT #####
                    '성' + '이름', ##### OUTSIDE 클라이언트 성명 INPUT #####
            'description': '블루무브 닥스에서 생성된 ' +
                           '성' + '이름' + ##### OUTSIDE 클라이언트 성명 INPUT #####
                           '님의 ' +
                           '4기 블루무버 지원서' ##### 문서 이름 INPUT #####
                           + '입니다.\n\n' + ##### OUTSIDE 클라이언트 성명 INPUT #####
                           '📧 생성일자: ' + '2021-01-20\n' + ##### 현재 일자 INPUT #####
                           '📨 제출일자: ' + '2021-01-20\n' + ##### 08 일자 INPUT #####
                           '📩 반환일자: ' + '2021-01-20\n', ##### 10 일자 INPUT #####
        },
        fields = 'name'
    ).execute()
    name = drive_response.get('name') ##### 문서 이름 + OUTSIDE 클라이언트 성명 OUTPUT #####
    if name:
        print('12. 문서 이름 및 설명 변경에 성공했습니다.')
    else:
        print('12. 문서 이름 및 설명 변경에 실패했습니다!!!')

    # 13. 서비스 계정 권한 삭제 writer 2 none
    drive_response = drive_service.permissions().delete(
        fileId = file_id,
        permissionId = permission_id,
    ).execute()
    print('13. 서비스 계정 권한 삭제 writer 2 none에 성공했습니다.')

if __name__ == '__main__':
    main()