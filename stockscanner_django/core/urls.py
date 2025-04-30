from django.urls import path
from . import views

urlpatterns = [
    path('subscribe/<slug:category>/', views.subscription_form, name='subscription_form'),
]