
from django.urls import path
from . import views

urlpatterns = [
    path('', views.workspace, name='workspace'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/hint/', views.get_hint, name='get_hint'),
    path('api/score/update/', views.record_success, name='record_success'),
    path('api/score/', views.get_score, name='get_score'),
    path('stackframe.js', views.empty_js, name='empty_js'),
]
