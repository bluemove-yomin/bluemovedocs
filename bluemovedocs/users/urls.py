from django.urls import path
from .views import *

app_name="users"
urlpatterns = [
    path('<int:id>/myaccount/', myaccount, name="myaccount"),
    path('<int:id>/write_name/', write_name, name="write_name"),
    # path('<int:id>/update_name/', update_name, name="update_name"),
]