from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/listings/', views.admin_listings, name='admin_listings'),
    path('dashboard/users/', views.admin_users, name='admin_users'),
    path('dashboard/users/<int:user_id>/toggle/', views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('dashboard/analytics/', views.admin_analytics, name='admin_analytics'),
    path('dashboard/advertisements/', views.admin_advertisements, name='admin_advertisements'),
]