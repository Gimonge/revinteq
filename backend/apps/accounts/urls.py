from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from .views import LoginView, RegisterView, AccountDetailView, ChangePasswordView, OnboardingCompleteView

urlpatterns = [
    path('login/',               LoginView.as_view(),            name='auth-login'),
    path('register/',            RegisterView.as_view(),          name='auth-register'),
    path('token/refresh/',       TokenRefreshView.as_view(),      name='auth-token-refresh'),
    path('token/blacklist/',     TokenBlacklistView.as_view(),    name='auth-token-blacklist'),
    path('account/',             AccountDetailView.as_view(),     name='auth-account'),
    path('change-password/',     ChangePasswordView.as_view(),    name='auth-change-password'),
    path('onboarding-complete/', OnboardingCompleteView.as_view(),name='auth-onboarding'),
]
