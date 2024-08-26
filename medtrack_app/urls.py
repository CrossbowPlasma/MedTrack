from django.urls import path
from . import views
urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='token_obtain_pair'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('user/', views.UserInfoView.as_view(), name='user_info'),
    path('notifications/', views.NotificationView.as_view(), name='list_notifications'),
    path('admin-stat/', views.AdminStatView.as_view(), name='admin-stats'),
    path('patients/create/', views.CreatePatientView.as_view(), name='create_patient'),
    path('patients/', views.ListPatientView.as_view(), name='list_patient'),
    path('procedures/create/', views.CreateProcedureView.as_view(), name='create_procedure'),
    path('procedures/', views.ListProcedureView.as_view(), name='list_procedure'),
    path('procedures/edit/<int:pk>/', views.UpdateProcedureView.as_view(), name='update_procedure'),
]
