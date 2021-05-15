import requests
import json


notion_token = "secret_oNT9GBQZuS4etJBUvZYcKDki8LXwsMsSEkBMYA6wALf"
notion_projects_db_id = "d17acacd-fb64-4e0d-9f75-462424c7cb81"
notion_tasks_db_id = "45e43f3f-dfb3-4d34-8b02-1c95a745719d"


def main():
    notion_headers = {
        'Authorization': f"Bearer " + notion_token,
        'Content-Type': 'application/json',
        'Notion-Version': '2021-05-13',
    }

    ##### List users #####
    notion_response = requests.get('https://api.notion.com/v1/users', headers=notion_headers)
    notion_response = json.loads(notion_response.text)
    notion_response = notion_response['results']
    notion_users_list = []
    for i in range(len(notion_response)):
        notion_user_type = notion_response[i]['type']
        if notion_user_type == "person":
            notion_user_email = notion_response[i]['person']['email']
            notion_user_id = notion_response[i]['id']
            notion_users_list.append(tuple((notion_user_email, notion_user_id)))
    print(notion_users_list)
    notion_user_id = dict(notion_users_list)["sangjun@bluemove.or.kr".lower()]
    print(notion_user_id)

    ##### List databases #####
    # notion_response = requests.post('https://api.notion.com/v1/search', headers=notion_headers)
    # notion_response = json.loads(notion_response.text)
    # notion_response = notion_response['results']
    # notion_projects_list = []
    # for i in range(len(notion_response)):
    #     notion_object = notion_response[i]['object']
    #     if notion_object == "page":
    #         if notion_response[i]['parent']['database_id'].replace('-', '') == notion_projects_db_id:
    #             notion_project_name = notion_response[i]['properties']['프로젝트']['title'][0]['text']['content']
    #             notion_project_id = notion_response[i]['id'].replace('-', '')
    #             notion_projects_list.append(tuple((notion_project_name, notion_project_id)))
    # notion_projects_list = sorted(notion_projects_list, key=lambda tup: (tup[0]))
    # print(notion_projects_list)

    ##### Retrieve a page #####
    # url = "https://api.notion.com/v1/pages/3875f954-86e2-4f21-b7de-052f63f3acff"
    # notion_response = requests.request("GET", url, headers=notion_headers)
    # notion_response = json.loads(notion_response.text)
    # print(notion_response['archived'])

    ##### Create a page #####
    # payload = json.dumps({
    #     "parent": {
    #         "database_id": notion_tasks_db_id
    #     },
    #     "properties": {
    #         "태스크": {
    #             "title": [
    #                 {
    #                     "text": {
    #                         "content": "인티그레이션 테스트"
    #                     }
    #                 }
    #             ]
    #         }
    #     }
    # })
    # notion_response = requests.request("POST", 'https://api.notion.com/v1/pages/', headers=notion_headers, data=payload.encode('utf-8'))
    # print(json.loads(notion_response.text)['id'])

    ##### Update page properties #####
    # payload = json.dumps({
    #     "properties": {
    #         "완료": {
    #             "checkbox": True
    #         }
    #     }
    # })
    # response = requests.request("PATCH", 'https://api.notion.com/v1/pages/e8c4e211-3f4b-429c-bfd0-fd5c5f542172', headers=notion_headers, data=payload)
    # print(response.text)


if __name__ == '__main__':
    main()