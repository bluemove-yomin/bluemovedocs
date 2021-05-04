from django.shortcuts import render, redirect
from .models import *
from users.models import Profile
from notice.models import Notice
from box.models import Box


def main(request):
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
    all_noticies = Notice.objects.all().order_by('-id')
    all_boxes = Box.objects.all().order_by('-id')
    return render(request, 'help/main.html', {'all_noticies': all_noticies, 'all_boxes': all_boxes})