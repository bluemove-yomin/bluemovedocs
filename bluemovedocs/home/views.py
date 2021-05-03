from django.shortcuts import render, redirect
from .models import *
from users.models import Profile
from notice.models import Notice
from box.models import Box


def home(request):
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
    return render(request, 'home/home.html', {'all_noticies': all_noticies, 'all_boxes': all_boxes})


def handler500(request):
    return render(request, 'errors/500.html')


def handler404(request, exception, template_name="404.html"): 
    response = render(request, "errors/404.html") 
    response.status_code = 404
    return response


def handler403(request, exception, template_name="403.html"): 
    response = render(request, "errors/403.html") 
    response.status_code = 403
    return response


def handler400(request, exception, template_name="400.html"): 
    response = render(request, "errors/400.html") 
    response.status_code = 400
    return response