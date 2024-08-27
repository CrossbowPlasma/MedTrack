from django.db.models.signals import post_save, m2m_changed
from django.contrib.auth.models import User
from django.dispatch import receiver, Signal
from .models import Procedure, Notification, AdminStat

patient_created = Signal()

@ receiver(m2m_changed, sender=User.groups.through)
def role_count_update(sender, instance, action, **kwargs):
    if action == 'post_add':
        admin_stat, _ = AdminStat.objects.get_or_create(pk=1)
        group = instance.groups.first().name
        if group == 'Front_Desk':
            admin_stat.front_desk_users += 1
        elif group == 'Doctor':
            admin_stat.doctor_users += 1
        elif group == 'Admin':
            admin_stat.admin_users += 1
        admin_stat.save()

@receiver(patient_created)
def handle_patient_created(sender, patient, created_by, **kwargs):
    Notification.objects.create(
        user=created_by,
        message=f"A new patient record for {patient.first_name} {patient.last_name} has been created."
    )

    admin_stat, _ = AdminStat.objects.get_or_create(pk=1)
    admin_stat.total_patients += 1
    admin_stat.save()

@receiver(post_save, sender=Procedure)
def procedure_created_or_updated(sender, instance, created, **kwargs):
    Notification.objects.create(
        user=User.objects.get(id=instance.created_by_id),
        message=f"A procedure {instance.procedure_name} for patient {instance.patient.first_name} {instance.patient.last_name} has been " + ('created.' if created else 'updated.')
    )

    if created:
        admin_stat, _ = AdminStat.objects.get_or_create(pk=1)
        admin_stat.total_procedures += 1
        admin_stat.save()    