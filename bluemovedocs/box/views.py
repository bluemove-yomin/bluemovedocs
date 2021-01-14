from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
import datetime
from .forms import BoxContentForm


@permission_required('auth.add_permission', raise_exception=True)
def write(request):
    form = BoxContentForm()
    return render(request, 'box/write.html', {'form': form})


@permission_required('auth.add_permission', raise_exception=True)
def create(request):
    if request.method == "POST":
        form = NoticeContentForm(request.POST, request.FILES)
        if form.is_valid():
            box_category = request.POST.get('category')
            box_title = request.POST.get('title')
            box_writer = request.user
            box_document_id = request.POST.get('document_id')
            box_deadline = request.POST.get('deadline')
            box_image = request.FILES.get('image')
            form.save(category=box_category, title=box_title, writer=box_writer, document_id=box_document_id, deadline=box_deadline, image=box_image)
    return redirect('box:main') # POST와 GET 모두 notice:main으로 redirect


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
    form = BoxContentForm(instance=box)
    if request.method == "POST":
        form = BoxContentForm(request.POST, instance=box)
        if form.is_valid():
            box_category = request.POST.get('category')
            box_title = request.POST.get('title')
            box_document_id = request.POST.get('document_id')
            box_deadline = request.POST.get('deadline')
            form.update(category=box_category, title=box_title, document_id=box_document_id, deadline=box_deadline)
        return redirect('box:read', box.id)
    return render(request, 'box/update.html', {'box': box, 'form': form})


@permission_required('auth.add_permission', raise_exception=True)
def updateimage(request, id):
    box = get_object_or_404(Box, pk=id)
    form = BoxContentForm(instance=box)
    if request.method == "POST":
        box.image = request.FILES.get('image')
        box.save(update_fields=['image'])
        return redirect('box:read', box.id)
    return render(request, 'box/updateimage.html', {'box': box, 'form': form})


@permission_required('auth.add_permission', raise_exception=True)
def delete(request, id):
    box = get_object_or_404(Box, pk=id)
    box.delete()
    return redirect('box:main')