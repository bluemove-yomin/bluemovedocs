from django.urls import path
from .views import *

app_name="users"
urlpatterns = [
    path('<int:id>/myaccount/', myaccount, name="myaccount"),
    path('<int:id>/write_info/', write_info, name="write_info"),
    path('login/', login_cancelled, name="login_cancelled"),
    path('<int:id>/delete/', login_cancelled_after_delete, name="login_cancelled_after_delete"),
]