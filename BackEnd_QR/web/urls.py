from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('login-exitoso/', views.login_exitoso, name='login_exitoso'),
    path('user-edit/', views.user_edit, name='user_edit'),
]