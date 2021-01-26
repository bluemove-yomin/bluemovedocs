from django.urls import path
from .views import *

app_name = 'box'
urlpatterns = [
    path('write/', write, name='write'),
    path('create/', create, name='create'),
    path('<int:id>/create_doc/', create_doc, name='create_doc'),
    path('', main, name='main'),
    path('<int:id>/', read, name='read'),
    path('<int:id>/box_favorite/', box_favorite, name="box_favorite"),
    path('<int:id>/update/', update, name='update'),
    path('<int:id>/updateimage/', updateimage, name='updateimage'),
    path('<int:id>/delete/', delete, name="delete"),
    path('delete_doc/<int:doc_id>/', delete_doc, name='delete_doc'),
    path('submit_doc/<int:doc_id>/', submit_doc, name='submit_doc'),
    path('reject_doc/<int:doc_id>/', reject_doc, name='reject_doc'),
    path('return_doc/<int:doc_id>/', return_doc, name='return_doc'),
    path('return_before_submit_doc/<int:doc_id>/', return_before_submit_doc, name='return_before_submit_doc'),
]