from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('dashboard/listings/', views.admin_listings, name='admin_listings'),
    path('dashboard/listings/<int:listing_id>/', views.admin_listing_detail, name='admin_listing_detail'),
    path('dashboard/listings/<int:listing_id>/approve/', views.admin_approve_listing, name='admin_approve_listing'),
    path('dashboard/listings/<int:listing_id>/reject/', views.admin_reject_listing, name='admin_reject_listing'),
    path('dashboard/listings/<int:listing_id>/remove/', views.admin_remove_listing, name='admin_remove_listing'),

    path('dashboard/users/', views.admin_users, name='admin_users'),
    path('dashboard/users/<int:user_id>/toggle/', views.admin_toggle_user_status, name='admin_toggle_user_status'),

    path('dashboard/analytics/', views.admin_analytics, name='admin_analytics'),

    path('dashboard/advertisements/', views.admin_advertisements, name='admin_advertisements'),
    path('dashboard/advertisements/<int:ad_id>/configure/', views.admin_ad_configure, name='admin_ad_configure'),
    path('dashboard/advertisements/<int:ad_id>/report/', views.admin_ad_report, name='admin_ad_report'),
]