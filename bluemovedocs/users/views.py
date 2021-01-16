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
    name_verified = profile.name_update_flag
    if not name_verified == True:
        return redirect('users:write_name', request.user.id)
    else:
    # 회원가입 실명등록 끝
        user = get_object_or_404(User, pk=id)
        my_notices = Notice.objects.filter(writer=user)
        favorites = request.user.favorite_user_set.all()
        return render(request, 'users/myaccount.html', {'my_notices': my_notices, 'favorites': favorites})


@login_required
def write_name(request, id):
    user = get_object_or_404(User, pk=id)
    profile = Profile.objects.get(user=user)
    if request.method == "POST":
        user.last_name = request.POST.get("last_name")
        user.first_name = request.POST.get("first_name")
        if 'bluemove.or.kr' in user.email:
            profile.level = 'bluemover'
        elif 'gmail.com' in user.email:
            profile.level = 'guest'
        elif 'naver.com' in user.email:
            profile.level = 'guest'
        elif 'kakao.com' in user.email:
            profile.level = 'guest'
        elif 'daum.net' in user.email:
            profile.level = 'guest'
        elif 'hanmail.net' in user.email:
            profile.level = 'guest'
        elif 'nate.com' in user.email:
            profile.level = 'guest'
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
            return redirect('users:login_cancelled')
        profile.name_update_flag = True
        user.save(update_fields=['last_name', 'first_name'])
        profile.save(update_fields=['level', 'name_update_flag'])
        return redirect('users:myaccount', user.id)
    return render(request, 'users/write_name.html')


def login_cancelled(request):
    return render(request, 'users/login_cancelled.html')