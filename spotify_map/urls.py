from django.urls import path
from spotify_map import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('callback/', views.login_callback, name='login_callback'),
    path('loading/', views.loading_page, name='loading_page'),
    path('check_loading_status', views.check_loading_status, name='check_loading_status'),
    path('start-loading/', views.start_loading, name='start_loading'),
    path('top-artists/<str:time_range>/', views.top_artists, name='top_artists'),
    path('logout/', views.logout, name='logout'),
    path('logout_redirect/', views.logout_redirect, name='logout_redirect'),
]