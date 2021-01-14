from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload

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
    drive_response = drive_service.files().get(
        fileId=file_id).execute()
    if drive_response.get('id') == file_id:
        print('테스트. 유저 Google Drive에 지원서 파일이 존재합니다.')
    else:
        print('테스트. 유저 Google Drive에 지원서 파일이 존재하지 않습니다.')

    # # 02. 블루무브 폴더에 지원서 템플릿 업로드하기 ### 비활성하기 ###
    # # file_metadata = {
    # #     'name': '4기 블루무버 지원서', # 나중에 제출일시 및 이름 추가하기
    # #     'mimeType': 'application/vnd.google-apps.document',
    # #     'parents': [folder_id],
    # #     'writersCanShare': True,
    # # }
    # # media = MediaFileUpload('application.html',
    # #                         mimetype='text/html',
    # #                         resumable=True)
    # # file = drive_service.files().create(body=file_metadata,
    # #                                     media_body=media,
    # #                                     fields='id').execute()
    # # file_id = file.get('id') ### File ID ###
    # # print('File ID: %s' % file_id)
    # # print('블루무브 폴더에 지원서 템플릿을 업로드했습니다.')

    # # 03. 유저 Permission ID 불러오기
    # def callback_for_permissions_list(request_id, response, exception):
    #     if exception:
    #         print(exception)
    #         print('03. ERROR 지원서 권한 정보 또는 유저 권한 ID를 불러오지 못했습니다.')
    #     else:
    #         permissions_list = response.get('permissions') ### 유저 Permissions List ###
    #         print("03. User Permissions: %s" % permissions_list)
    #         print('03. 지원서 권한 정보를 불러왔습니다.')
    #         for permissions_data in permissions_list:
    #             user_permission_id = permissions_data['id'] ### 유저 Permission ID ###
    #             print('03. User Permission ID: %s' % user_permission_id)
    #             print('03. 유저 권한 ID를 불러왔습니다.')

    #     # 04. 지원서 소유권 블루무브로 이전하기
    #     # file_id = '1_4BCiUc0kAaQz4syK_rVmocdabi5-AfcF-JBH_9W5zY' ### 나중에 02와 연결하기 ###
    #     def callback_for_bluemove_ownership(request_id, response, exception):
    #         if exception:
    #             print(exception)
    #             print('04. ERROR 지원서 소유권을 블루무브로 이전하지 못했습니다.')
    #         else:
    #             bluemove_permission_id = response.get('id') ### 블루무브 Permission ID ###
    #             print("04. Bluemove Permission Id: %s" % bluemove_permission_id)
    #             print('04. 지원서 소유권을 블루무브로 이전했습니다.')
    #     batch = drive_service.new_batch_http_request(callback=callback_for_bluemove_ownership)
    #     bluemove_permission_owner = {
    #         'type': 'user',
    #         'role': 'owner',
    #         'emailAddress': 'bwbluemove@gmail.com', ### 블루무브 이메일 주소 ###
    #     }
    #     batch.add(drive_service.permissions().create(
    #             fileId=file_id,
    #             body=bluemove_permission_owner,
    #             transferOwnership=True,
    #             moveToNewOwnersRoot=True,
    #             fields='id',
    #     ))
    #     batch.execute()

    #     # 05. 유저 권한을 뷰어로 변경하기
    #     def callback_for_update_permission(request_id, response, exception):
    #         if exception:
    #             print(exception)
    #             print('05. ERROR 유저 권한을 뷰어로 변경하지 못했습니다.')
    #         else:
    #             updated_user_permission_id = response.get('id') ### 업데이트된 유저 Permission ID ###
    #             print("05. Updated User Permission ID: %s" % updated_user_permission_id)
    #             print('05. 유저 권한을 뷰어로 변경했습니다.')
    #             print('지원서 제출이 완료되었습니다.')
    #     batch = drive_service.new_batch_http_request(callback=callback_for_update_permission)
    #     user_permission_reader = {
    #         'role': 'reader',
    #     }
    #     batch.add(drive_service.permissions().update(
    #             fileId=file_id,
    #             permissionId=user_permission_id,
    #             body=user_permission_reader,
    #     ))
    #     batch.execute()

    # batch = drive_service.new_batch_http_request(callback=callback_for_permissions_list)
    # batch.add(drive_service.permissions().list(
    #         fileId=file_id,
    # ))
    # batch.execute()

if __name__ == '__main__':
    main()