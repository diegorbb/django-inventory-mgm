from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('inventory/', views.inventory, name='inventory'),  # Update URL pattern

    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),

    path('create-item/', views.createItem, name='create-item'),
    path('edit-item/<str:pk>/', views.editItem, name='edit-item'),
    path('delete-item/<str:pk>/', views.deleteItem, name='delete-item'),

    path('incidents/', views.incidentPage, name='incidents'),
    path('incident/<str:pk>/', views.incident, name='incident'),
    path('create-incident/', views.createIncident, name='create-incident'),
    path('edit-incident/<str:pk>/', views.editIncident, name='edit-incident'),

    path('incident/<str:pk>/add-comment/', views.add_comment, name='add-comment'),
    path('incident/<str:pk>/delete-comment/<str:comment_id>/', views.delete_comment, name='delete-comment'),

    path('profile/', views.profile, name='profile'),
    path('users/', views.users_list, name='users'),
    path('users/create/', views.create_user, name='create-user'),
]
