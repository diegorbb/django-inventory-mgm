from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),

    path('create-item/', views.createItem, name='create-item'),
    path('edit-item/<str:pk>/', views.editItem, name='edit-item'),
    path('delete-item/<str:pk>/', views.deleteItem, name='delete-item'),

    path('incidents/', views.incidentPage, name='incidents'),
    path('incident/<str:pk>/', views.incident, name='incident'),
    path('create-incident/', views.createIncident, name='create-incident'),
]
