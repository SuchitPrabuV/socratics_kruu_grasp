from django.urls import path
from . import views

urlpatterns = [
    path('', views.workspace, name='workspace'),
    path('api/hint/', views.get_hint, name='get_hint'),
    path('api/success/', views.record_success, name='record_success'),
    path('api/progress/', views.get_progress, name='get_progress'),
    path('stackframe.js', views.empty_js, name='empty_js'),
]
