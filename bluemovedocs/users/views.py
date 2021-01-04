from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *
from notice.models import Notice
from box.models import Box


@login_required
def myaccount(request, id):
    user = get_object_or_404(User, pk=id)
    my_notices = Notice.objects.filter(writer=user)
    favorites = request.user.favorite_user_set.all()
    return render(request, 'users/myaccount.html', {'my_notices': my_notices, 'favorites': favorites})