from django.shortcuts import render
from notice.models import *
from .models import *


def home(request):
    all_noticies = Notice.objects.all().order_by('-id')
    return render(request, 'home/home.html', {'all_noticies': all_noticies})


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

    # 아 뭐가 문제일까