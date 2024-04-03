from django.urls import path
from .views import LoginView, ProfileView, register_user, LogoutView



urlpatterns = [
    path('login/',LoginView.as_view(), name='loginUrl'),
    path('profile/',ProfileView.as_view(), name='profileUrl'),
    path('register/',register_user, name='registerUrl'),
    path('logout/',LogoutView.as_view(), name='LogoutUrl'),
    
]
