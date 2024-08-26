from django.contrib import admin
from .models import Patient, Procedure, AdminStat, Notification

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'mobile_number', 'email', 'city', 'state')
    search_fields = ('first_name', 'last_name', 'mobile_number', 'email')
    list_filter = ('city', 'state', 'gender')
    ordering = ('first_name', 'last_name')

@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ('procedure_name', 'patient', 'status', 'procedure_datetime', 'category', 'clinic_address', 'created_by')
    search_fields = ('procedure_name', 'patient__first_name', 'patient__last_name', 'clinic_address')
    list_filter = ('status', 'category', 'procedure_datetime')
    ordering = ('-procedure_datetime',)

@admin.register(AdminStat)
class AdminStatAdmin(admin.ModelAdmin):
    list_display = ('total_patients', 'total_procedures', 'front_desk_users', 'doctor_users', 'admin_users', 'last_updated')
    readonly_fields = ('total_patients', 'total_procedures', 'front_desk_users', 'doctor_users', 'admin_users', 'last_updated')
    ordering = ('-last_updated',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at')
    search_fields = ('user__username', 'message')
    ordering = ('-created_at',)
