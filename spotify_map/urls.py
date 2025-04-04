from django.urls import path
from spotify_map import views
from django.contrib import admin 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('callback/', views.login_callback, name='login_callback'),
    path('top-artists/<str:time_range>/', views.top_artists, name='top_artists'),
    path('logout/', views.logout, name='logout'),
    path('logout_redirect/', views.logout_redirect, name='logout_redirect'),
]