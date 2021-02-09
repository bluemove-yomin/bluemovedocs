from django.urls import path
from .views import *

app_name="users"
urlpatterns = [
    path('<int:id>/myaccount/', myaccount, name="myaccount"),
    path('<int:id>/write_info/', write_info, name="write_info"),
    path('login_cancelled/', login_cancelled, name="login_cancelled"),
    path('login_cancelled_no_scopes/', login_cancelled_no_scopes, name="login_cancelled_no_scopes"),
    path('login_cancelled_no_drive/', login_cancelled_no_drive, name="login_cancelled_no_drive"),
    path('login_cancelled_no_slack/', login_cancelled_no_slack, name="login_cancelled_no_slack"),
    path('<int:id>/login_cancelled_delete/', login_cancelled_delete, name="login_cancelled_delete"),
]