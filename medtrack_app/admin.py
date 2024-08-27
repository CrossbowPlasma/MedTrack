from django.contrib import admin
from .models import Patient, Procedure, AdminStat, Notification

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'mobile_number', 'gender', 'birthdate', 'created_date')
    readonly_fields = ('created_date',)
    search_fields = ('first_name', 'last_name', 'email', 'mobile_number')
    list_filter = ('gender', 'city', 'state', 'created_date')
    ordering = ('first_name', 'last_name')

@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ('procedure_name', 'patient', 'status', 'created_by', 'created_date', 'updated_date')
    readonly_fields = ('patient', 'created_by', 'created_date', 'updated_date')
    list_filter = ('status', 'created_date', 'updated_date')
    search_fields = ('procedure_name', 'patient__first_name', 'patient__last_name')
    ordering = ('-created_date',)

@admin.register(AdminStat)
class AdminStatAdmin(admin.ModelAdmin):
    list_display = ('total_patients', 'total_procedures', 'front_desk_users', 'doctor_users', 'admin_users', 'last_updated')
    readonly_fields = ('total_patients', 'total_procedures', 'front_desk_users', 'doctor_users', 'admin_users', 'last_updated')
    # ordering = ('-last_updated',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'timestamp')
    search_fields = ('user__username', 'message')
    ordering = ('-timestamp',)
