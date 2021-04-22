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
from googleapiclient.discovery import build
from slack_sdk import WebClient





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
    return render(request, 'users/myaccount.html', {'favorites': favorites, 'box_favorites': box_favorites})


@login_required
def write_info(request, id):
    user = get_object_or_404(User, pk=id)
    profile = Profile.objects.get(user=user)
    if 'bluemove.or.kr' in user.email:
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
            user.save(update_fields=['last_name', 'first_name'])
            profile.save(update_fields=['level', 'phone', 'slack_user_id', 'info_update_flag'])
            return redirect('users:myaccount', user.id)
    elif 'gmail.com' in user.email or 'naver.com' in user.email or 'kakao.com' in user.email or 'daum.net' in user.email or 'hanmail.net' in user.email or 'nate.com' in user.email:
        profile.level = 'guest'
        if request.method == "POST":
            user.last_name = request.POST.get("last_name")
            user.first_name = request.POST.get("first_name")
            profile.phone = request.POST.get("phone")
            profile.info_update_flag = True
            user.save(update_fields=['last_name', 'first_name'])
            profile.save(update_fields=['level', 'phone', 'info_update_flag'])
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
        user.delete()
        return render(request, 'users/login_deleted.html')
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