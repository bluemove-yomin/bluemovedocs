from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import datetime
from .models import *


@login_required
def write(request):
    return render(request, 'box/write.html')


@login_required
def create(request):
    if request.method == "POST":
        box_category = request.POST.get('category')
        box_title = request.POST.get('title')
        box_writer = request.user
        box_deadline = request.POST.get('deadline')
        box_content = request.POST.get('content')
        box_image = request.FILES.get('image')
        Box.objects.create(category=box_category, title=box_title, writer=box_writer, deadline=box_deadline, content=box_content, image=box_image)
    return redirect('box:main')


def main(request):
    all_boxes = Box.objects.order_by('deadline')
    return render(request, 'box/main.html', {'all_boxes': all_boxes})


def read(request, id):
    box = Box.objects.get(pk=id)
    all_boxes = Box.objects.all().order_by('deadline')
    return render(request, 'box/read.html', {'box': box, 'all_boxes': all_boxes})


@login_required
def update(request, id):
    box = get_object_or_404(Box, pk=id)
    if request.method == "POST":
        box.category = request.POST['category']
        box.title = request.POST['title']
        box.deadline = request.POST['deadline']
        box.content = request.POST['content']
        box.save()
        return redirect('box:read', box.id)
    return render(request, 'box/update.html', {'box': box})


@login_required
def updateimage(request, id):
    box = get_object_or_404(Box, pk=id)
    if request.method == "POST":
        box.category = request.POST.get('category')
        box.title = request.POST.get('title')
        box.deadline = request.POST.get('deadline')
        box.content = request.POST.get('content')
        box.image = request.FILES.get('image')
        box.save(update_fields=['image'])
        return redirect('box:read', box.id)
    return render(request, 'box/updateimage.html', {'box': box})


@login_required
def delete(request, id):
    box = get_object_or_404(Box, pk=id)
    box.delete()
    return redirect('box:main')