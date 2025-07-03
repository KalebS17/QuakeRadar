from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('login-exitoso/', views.login_exitoso, name='login_exitoso'),
    path('user/edit/', views.user_edit, name='user_edit'),
    path('logout/', views.logout_view, name='logout'),
    path('mapa/', views.mapa, name='mapa'),
    path('auth/', include('social_django.urls', namespace='social')),
]