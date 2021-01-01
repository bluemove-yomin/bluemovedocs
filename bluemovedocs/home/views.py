from django.shortcuts import render
from notice.models import *
from .models import *


def home(request):
    all_noticies = Notice.objects.all().order_by('-id')
    return render(request, 'home/home.html', {'all_noticies': all_noticies})