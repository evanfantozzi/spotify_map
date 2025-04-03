from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),  # Pre-login landing page
    path('home/', views.home, name='home'),  # Post-login home page
    path('login/', views.login, name='login'),
    path('login/callback/', views.login_callback, name='login_callback'),
    path('top-artists/<str:time_range>/', views.top_artists, name='top_artists'),
    path('logout/', views.logout, name='logout'),
]
