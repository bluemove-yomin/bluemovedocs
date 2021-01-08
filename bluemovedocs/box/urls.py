from django.urls import path
from .views import *

app_name = 'box'
urlpatterns = [
    path('write/', write, name='write'),
    path('create/', create, name='create'),
    path('', main, name='main'),
    path('<int:id>/', read, name='read'),
    path('<int:id>/box_favorite/', box_favorite, name="box_favorite"),
    path('<int:id>/update/', update, name='update'),
    path('<int:id>/updateimage/', updateimage, name='updateimage'),
    path('<int:id>/delete/', delete, name="delete"),
]