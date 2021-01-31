from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *
from notice.models import Notice
from box.models import Box
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
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
    my_notices = Notice.objects.filter(writer=user)
    favorites = request.user.favorite_user_set.all()
    return render(request, 'users/myaccount.html', {'my_notices': my_notices, 'favorites': favorites})


@login_required
def write_info(request, id):
    user = get_object_or_404(User, pk=id)
    profile = Profile.objects.get(user=user)
    if 'bluemove.or.kr' in user.email:
        profile.level = 'bluemover'
        if request.method == "POST":
            user.last_name = request.POST.get("last_name")
            user.first_name = request.POST.get("first_name")
            profile.phone = request.POST.get("phone")
            profile.info_update_flag = True
            client = WebClient(token=slack_bot_token)
            slack_response = client.users_lookupByEmail(
                email = request.user.email
            )
            slack_user_data = slack_response.get('user')
            profile.slack_user_id = slack_user_data.get('id')
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


def login_cancelled(request):
    return render(request, 'users/login_cancelled.html')


def login_cancelled_after_delete(request, id):
    user = get_object_or_404(User, pk=id)
    user.delete()
    return render(request, 'users/login_cancelled_after_delete.html')