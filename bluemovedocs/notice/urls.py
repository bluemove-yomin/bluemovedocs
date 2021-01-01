from django.urls import path
from .views import *

app_name = 'notice'
urlpatterns = [
    path('write/', write, name='write'),
    path('create/', create, name='create'),
    path('<int:id>/create_comment/', create_comment, name="create_comment"),
    path('', main, name='main'),
    path('<int:id>/', read, name='read'),
    path('<int:id>/update/', update, name='update'),
    path('updatecomment/<int:comment_id>/', updatecomment, name='updatecomment'),
    path('<int:id>/updateimage/', updateimage, name='updateimage'),
    path('<int:id>/delete/', delete, name="delete"),
    path('delete_comment/<int:comment_id>/', delete_comment, name="delete_comment"),
]