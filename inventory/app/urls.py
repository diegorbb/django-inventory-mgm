from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create-item/', views.createItem, name='create-item'),
    path('edit-item/<str:pk>/', views.editItem, name='edit-item'),
    path('delete-item/<str:pk>/', views.deleteItem, name='delete-item'),
]
