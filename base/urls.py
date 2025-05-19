from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('verify-product/', views.verify_product, name='verify_product'),
    path('filter-products/', views.filter_products, name='filter_products'),
    path('login/', views.login_view, name='login_view'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout_view'),
    path('chat/api/', views.chat_api, name='chat_api'),
    path('webinars/', views.webinar_redirect, name='webinars'),
    path('quiz/', views.quiz, name='quiz'),

    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('api/products/<int:product_id>/verify/', views.verify_product, name='verify_product'),



]
