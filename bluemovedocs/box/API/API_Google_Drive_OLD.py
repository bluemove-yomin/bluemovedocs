from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

def main():

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8000)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    drive_service = build('drive', 'v3', credentials=creds)

    results = drive_service.files().list(
        corpora="drive",
        driveId="0ADF4LPECMczOUk9PVA",
        fields="files(id, name)",
        includeItemsFromAllDrives=True,
        q="mimeType='application/vnd.google-apps.folder' and '13o3t-Ig-OKzNpmXi-QCF7S88p2KXaHhQ' in parents",
        supportsAllDrives=True,
    ).execute()
    items = results.get('files', [])

    if not items:
        return print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
    return None

    # 01. 유저 My Drive에 블루무브 폴더 생성하기
    file_metadata = {
        'name': '블루무브',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    file = drive_service.files().create(body=file_metadata,
                                        fields='id').execute()
    folder_id = file.get('id')
    print('01. Folder ID: %s' % folder_id)
    print('01. 유저 My Drive에 블루무브 폴더를 생성했습니다.')
    
    # 02. 블루무브 폴더에 지원서 템플릿 복사하기
    application_id = '1mRPI5haxz1IrjDw5oXVIXYSd89HKB_8hOhGxC09sq58' ### 지원서 File ID ###
    body = {
        'name': '4기 블루무버 지원서', # 나중에 제출일시 및 이름 추가하기
        'parents': [folder_id],
        'writersCanShare': True,
    }
    drive_response = drive_service.files().copy(
        fileId=application_id, body=body).execute()
    file_id = drive_response.get('id') ### File ID ###
    print('02. File ID: %s' % file_id)
    print('02. 블루무브 폴더에 지원서 템플릿을 복사했습니다.')

    # 테스트. 지원서 찾기
    # drive_response = drive_service.files().get(
    #     fileId=file_id).execute()
    # if drive_response.get('id') == file_id:
    #     print('테스트. 유저 Google Drive에 지원서 파일이 존재합니다.')
    # else:
    #     print('테스트. 유저 Google Drive에 지원서 파일이 존재하지 않습니다.')

    # 02. 블루무브 폴더에 지원서 템플릿 업로드하기 ### 비활성하기 ###
    # file_metadata = {
    #     'name': '4기 블루무버 지원서', # 나중에 제출일시 및 이름 추가하기
    #     'mimeType': 'application/vnd.google-apps.document',
    #     'parents': [folder_id],
    #     'writersCanShare': True,
    # }
    # media = MediaFileUpload('application.html',
    #                         mimetype='text/html',
    #                         resumable=True)
    # file = drive_service.files().create(body=file_metadata,
    #                                     media_body=media,
    #                                     fields='id').execute()
    # file_id = file.get('id') ### File ID ###
    # print('File ID: %s' % file_id)
    # print('블루무브 폴더에 지원서 템플릿을 업로드했습니다.')

    # 03. 문서 잠그기
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
    print('03. 문서를 잠갔습니다.')

    # 04. 유저 Permission ID 불러오기
    drive_response = drive_service.permissions().list(
        fileId=file_id,
    ).execute()
    permissions_list = drive_response.get('permissions')
    for permissions_data in permissions_list:
        user_permission_id = permissions_data['id']
        if user_permission_id:
            print('04. 유저의 Permission ID를 불러왔습니다.')
        else:
            print('04. 유저의 Permission ID를 불러오지 못했습니다.')

    # 05. 문서 소유권 Service Account에게 이전하기
    bluemove_permission_owner = {
        'type': 'user',
        'role': 'owner',
        'emailAddress': 'bluemove-service@bluemove-docs.iam.gserviceaccount.com', ### 블루무브 이메일 주소 ###
    }
    drive_response = drive_service.permissions().create(
        fileId=file_id,
        body=bluemove_permission_owner,
        transferOwnership=True,
        # moveToNewOwnersRoot=True,
        fields='id',
    ).execute()
    bluemove_permission_id = drive_response.get('id')
    if bluemove_permission_id:
        print('05. 문서 소유권을 블루무브에 이전했습니다.')
    else:
        print('05. 문서 소유권을 블루무브에 이전하지 못했습니다.')

    # 06. 유저 권한을 뷰어로 변경하기
    user_permission_reader = {
        'role': 'reader',
    }
    drive_response = drive_service.permissions().update(
        fileId=file_id,
        permissionId=user_permission_id,
        body=user_permission_reader,
    ).execute()
    updated_user_permission_id = drive_response.get('id')
    if updated_user_permission_id:
        print('06. 유저 권한을 뷰어로 변경했습니다.')
    else:
        print('06. 유저 권한을 뷰어로 변경하지 못했습니다.')

    # 07. 서비스 계정으로 접수자 writer 퍼미션 추가
    SERVICE_ACCOUNT_SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'bluemove-docs-64c12e189ad5.json', SERVICE_ACCOUNT_SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    create_role_writer_boxwriter = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': 'tejava@bluemove.or.kr', ### 블루무브 이메일 주소 ###
    }
    drive_response = drive_service.permissions().create(
        fileId=file_id,
        body=create_role_writer_boxwriter,
        fields='id',
    ).execute()
    bluemove_permission_id = drive_response.get('id')
    if bluemove_permission_id:
        print('07. 접수자 writer 권한을 생성했습니다.')
    else:
        print('07. 접수자 writer 권한을 생성하지 못했습니다.')

if __name__ == '__main__':
    main()