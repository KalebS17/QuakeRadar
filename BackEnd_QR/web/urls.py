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
    path('fetch_earthquake_data/', views.fetch_earthquake_data, name='fetch_earthquake_data'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('guardar_terremotos/', views.save_earthquake_data, name='save_earthquake_data'),
    path('news-generator/', views.news_generator, name='news_generator'),
    path('user/editar/', views.editar_usuario, name='editar_usuario'),
    path('dashboard/admin/eliminar_usuario/<int:user_id>/<str:fuente>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('dashboard/admin/editar_usuario/<int:user_id>/<str:fuente>/', views.editar_usuario_admin, name='editar_usuario_admin')
]