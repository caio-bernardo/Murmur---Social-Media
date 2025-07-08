from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('about/', views.about, name='about'),
    path('login/', views.login_redirect, name='login'),
    path('signup/', views.signup_redirect, name='signup'),
]