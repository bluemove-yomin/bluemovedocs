from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *
from notice.models import Notice
from box.models import Box
from django.contrib.auth.models import User


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
        user.save(update_fields=['last_name', 'first_name'])
        profile.name_update_flag = True
        profile.save(update_fields=['name_update_flag'])
        return redirect(request.GET['next'])
    return render(request, 'users/write_name.html')


# @login_required
# def update_name(request, id):
#     user = get_object_or_404(User, pk=id)
#     profile = Profile.objects.get(user=user)
#     if request.method == "POST":
#         user.last_name = request.POST.get("last_name")
#         user.first_name = request.POST.get("first_name")
#         user.save(update_fields=['last_name', 'first_name'])
#         profile.name_update_flag = True
#         profile.save(update_fields=['name_update_flag'])
#         return redirect(request.GET['next'])
#     return redirect('users:myaccount', user.id)