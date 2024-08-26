from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
    ]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    mobile_number = models.CharField(max_length=10)
    address = models.TextField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    birthdate = models.DateField()
    email = models.EmailField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_mobile_number = models.CharField(max_length=10)
    language = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = _('Patient')
        verbose_name_plural = _('Patients')

class Procedure(models.Model):
    STATUS_CHOICES = [
        ('preparation', _('Preparation')),
        ('in-progress', _('In Progress')),
        ('not-done', _('Not Done')),
        ('on-hold', _('On Hold')),
        ('stopped', _('Stopped')),
        ('completed', _('Completed')),
        ('entered-in-error', _('Entered in Error')),
        ('unknown', _('Unknown')),
    ]

    CATEGORY_CHOICES = [
        ('psychiatry', _('Psychiatry procedure or service')),
        ('counseling', _('Counseling')),
        ('surgical', _('Surgical procedure')),
        ('diagnostic', _('Diagnostic procedure')),
        ('chiropractic', _('Chiropractic manipulation')),
        ('social-service', _('Social service procedure')),
    ]

    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='procedures')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    procedure_datetime = models.DateTimeField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    procedure_name = models.CharField(max_length=100)
    clinic_address = models.TextField()
    notes = models.TextField(blank=True, null=True)
    report = models.FileField(upload_to='reports/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.procedure_name} - {self.patient.first_name} {self.patient.last_name}"

    class Meta:
        ordering = ['-procedure_datetime']
        verbose_name = _('Procedure')
        verbose_name_plural = _('Procedures')

class AdminStat(models.Model):
    total_patients = models.IntegerField(default=0)
    total_procedures = models.IntegerField(default=0)
    front_desk_users = models.IntegerField(default=0)
    doctor_users = models.IntegerField(default=0)
    admin_users = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stats as of {self.last_updated}"

    class Meta:
        verbose_name = _('Admin Statistic')
        verbose_name_plural = _('Admin Statistics')

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} at {self.created_at}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')