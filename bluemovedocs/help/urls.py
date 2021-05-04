from django.urls import path
from .views import *

app_name = 'help'
urlpatterns = [
    path('', main, name='main'),
]