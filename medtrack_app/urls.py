from django.urls import path
from . import views
urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='token_obtain_pair'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('user/', views.UserInfoView.as_view(), name='user_info'),
    path('notifications/', views.NotificationView.as_view(), name='list_notifications'),
    path('admin-stat/', views.AdminStatView.as_view(), name='admin-stats'),
    path('patients/', views.PatientView.as_view(), name='list_create_patient'),
    path('procedures/', views.ProcedureView.as_view(), name='list_create_procedure'),
    path('procedures/<int:pk>/', views.ProcedureView.as_view(), name='update_procedure'),
]
