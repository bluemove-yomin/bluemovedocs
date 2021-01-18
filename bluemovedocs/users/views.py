from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *
from notice.models import Notice
from box.models import Box
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount


@login_required
def myaccount(request, id):
    # 회원가입 실명등록 시작
    profile = Profile.objects.get(user=request.user)
    name_verified = profile.info_update_flag
    if not name_verified == True:
        return redirect('users:write_info', request.user.id)
    else:
    # 회원가입 실명등록 끝
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
            user.save(update_fields=['last_name', 'first_name'])
            profile.save(update_fields=['level', 'phone', 'info_update_flag'])
            return redirect('users:myaccount', user.id)
    elif 'gmail.com' in user.email:
        profile.level = 'guest'
        if request.method == "POST":
            user.last_name = request.POST.get("last_name")
            user.first_name = request.POST.get("first_name")
            profile.phone = request.POST.get("phone")
            profile.info_update_flag = True
            user.save(update_fields=['last_name', 'first_name'])
            profile.save(update_fields=['level', 'phone', 'info_update_flag'])
            return redirect('users:myaccount', user.id)
    elif 'naver.com' in user.email:
        profile.level = 'guest'
        if request.method == "POST":
            user.last_name = request.POST.get("last_name")
            user.first_name = request.POST.get("first_name")
            profile.phone = request.POST.get("phone")
            profile.info_update_flag = True
            user.save(update_fields=['last_name', 'first_name'])
            profile.save(update_fields=['level', 'phone', 'info_update_flag'])
            return redirect('users:myaccount', user.id)
    elif 'kakao.com' in user.email:
        profile.level = 'guest'
        if request.method == "POST":
            user.last_name = request.POST.get("last_name")
            user.first_name = request.POST.get("first_name")
            profile.phone = request.POST.get("phone")
            profile.info_update_flag = True
            user.save(update_fields=['last_name', 'first_name'])
            profile.save(update_fields=['level', 'phone', 'info_update_flag'])
            return redirect('users:myaccount', user.id)
    elif 'daum.net' in user.email:
        profile.level = 'guest'
        if request.method == "POST":
            user.last_name = request.POST.get("last_name")
            user.first_name = request.POST.get("first_name")
            profile.phone = request.POST.get("phone")
            profile.info_update_flag = True
            user.save(update_fields=['last_name', 'first_name'])
            profile.save(update_fields=['level', 'phone', 'info_update_flag'])
            return redirect('users:myaccount', user.id)
    elif 'hanmail.net' in user.email:
        profile.level = 'guest'
        if request.method == "POST":
            user.last_name = request.POST.get("last_name")
            user.first_name = request.POST.get("first_name")
            profile.phone = request.POST.get("phone")
            profile.info_update_flag = True
            user.save(update_fields=['last_name', 'first_name'])
            profile.save(update_fields=['level', 'phone', 'info_update_flag'])
            return redirect('users:myaccount', user.id)
    elif 'nate.com' in user.email:
        profile.level = 'guest'
        if request.method == "POST":
            user.last_name = request.POST.get("last_name")
            user.first_name = request.POST.get("first_name")
            profile.phone = request.POST.get("phone")
            profile.info_update_flag = True
            user.save(update_fields=['last_name', 'first_name'])
            profile.save(update_fields=['level', 'info_update_flag'])
            return redirect('users:myaccount', user.id)
    elif '.edu' in user.email:
        user.delete()
        return redirect('users:login_cancelled')
    elif '.ac.kr' in user.email:
        user.delete()
        return redirect('users:login_cancelled')
    elif '.hs.kr' in user.email:
        user.delete()
        return redirect('users:login_cancelled')
    elif '.ms.kr' in user.email:
        user.delete()
        return redirect('users:login_cancelled')
    elif '.go.kr' in user.email:
        user.delete()
        return redirect('users:login_cancelled')
    elif '.co.kr' in user.email:
        user.delete()
        return redirect('users:login_cancelled')
    elif '.or.kr' in user.email:
        user.delete()
        return redirect('users:login_cancelled')
    elif '.org' in user.email:
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