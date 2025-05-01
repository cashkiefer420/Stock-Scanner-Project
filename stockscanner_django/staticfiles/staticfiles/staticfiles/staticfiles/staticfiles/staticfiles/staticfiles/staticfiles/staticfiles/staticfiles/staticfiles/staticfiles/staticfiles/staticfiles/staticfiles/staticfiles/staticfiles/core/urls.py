from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('news/', views.news_view, name='news_view'),
    path('search/', views.stock_search, name='stock_search'),
    path('filter/', views.filter_view, name='filter_view'),
    path('filter/download/', views.download_csv_view, name='download_csv'),
    #path('data-refresh/', views.data_refresh_view, name='data_refresh'),
    path('email-filter/', views.email_filter_view, name='email_filter'),
    path('subscribe/<slug:category>/', views.subscription_form, name='subscription_form'),
    path('subscribe-<slug:route_name>', views.generic_subscribe),
]
