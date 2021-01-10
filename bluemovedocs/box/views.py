from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
import datetime


@permission_required('auth.add_permission', raise_exception=True)
def write(request):
    return render(request, 'box/write.html')


@permission_required('auth.add_permission', raise_exception=True)
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
    opened_boxes = Box.objects.filter(deadline__gte=datetime.date.today()).order_by('deadline')
    closed_boxes = Box.objects.filter(deadline__lt=datetime.date.today()).order_by('deadline')
    # opened_page = request.GET.get('opened_page', 1)
    # closed_page = request.GET.get('closed_page', 1)
    page = request.GET.get('page', 1)
    opened_paginator = Paginator(opened_boxes, 9)
    closed_paginator = Paginator(closed_boxes, 9)
    try:
        # opened_boxes = opened_paginator.page(opened_page)
        # closed_boxes = closed_paginator.page(closed_page)
        opened_boxes = opened_paginator.page(page)
        closed_boxes = closed_paginator.page(page)
    except PageNotAnInteger:
        opened_boxes = opened_paginator.page(1)
        closed_boxes = closed_paginator.page(1)
    except EmptyPage:
        opened_boxes = opened_paginator.page(opened_paginator.num_pages)
        closed_boxes = closed_paginator.page(closed_paginator.num_pages)
    return render(request, 'box/main.html', {'opened_boxes': opened_boxes, 'closed_boxes': closed_boxes})


def read(request, id):
    box = Box.objects.get(pk=id)
    opened_boxes = Box.objects.filter(deadline__gte=datetime.date.today()).order_by('deadline')
    closed_boxes = Box.objects.filter(deadline__lt=datetime.date.today()).order_by('deadline')
    # opened_page = request.GET.get('opened_page', 1)
    # closed_page = request.GET.get('closed_page', 1)
    page = request.GET.get('page', 1)
    opened_paginator = Paginator(opened_boxes, 9)
    closed_paginator = Paginator(closed_boxes, 9)
    try:
        # opened_boxes = opened_paginator.page(opened_page)
        # closed_boxes = closed_paginator.page(closed_page)
        opened_boxes = opened_paginator.page(page)
        closed_boxes = closed_paginator.page(page)
    except PageNotAnInteger:
        opened_boxes = opened_paginator.page(1)
        closed_boxes = closed_paginator.page(1)
    except EmptyPage:
        opened_boxes = opened_paginator.page(opened_paginator.num_pages)
        closed_boxes = closed_paginator.page(closed_paginator.num_pages)
    return render(request, 'box/read.html', {'box': box, 'opened_boxes': opened_boxes, 'closed_boxes': closed_boxes})


@login_required
def box_favorite(request, id):
    box = get_object_or_404(Box, pk=id)
    
    if request.user in box.box_favorite_user_set.all():
        box.box_favorite_user_set.remove(request.user)
    else:
        box.box_favorite_user_set.add(request.user)

    if 'next' in request.GET:
        return redirect(request.GET['next'])
    else:
        return redirect('box:main')


@permission_required('auth.add_permission', raise_exception=True)
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


@permission_required('auth.add_permission', raise_exception=True)
def updateimage(request, id):
    box = get_object_or_404(Box, pk=id)
    if request.method == "POST":
        box.image = request.FILES.get('image')
        box.save(update_fields=['image'])
        return redirect('box:read', box.id)
    return render(request, 'box/updateimage.html', {'box': box})


@permission_required('auth.add_permission', raise_exception=True)
def delete(request, id):
    box = get_object_or_404(Box, pk=id)
    box.delete()
    return redirect('box:main')