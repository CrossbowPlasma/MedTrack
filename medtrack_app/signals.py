from django.db.models.signals import pre_save, post_save, post_delete, m2m_changed
from django.contrib.auth.models import User
from django.dispatch import receiver, Signal
from .models import Procedure, Notification, AdminStat
import os

# Custom signal to indicate when a patient is created
patient_created = Signal()

# Signal receiver to update role counts in AdminStat when users are added to groups
@receiver(m2m_changed, sender=User.groups.through)
def role_count_update(sender, instance, action, **kwargs):
    # Triggered when the 'groups' field of User model is changed
    if action == 'post_add':
        admin_stat, _ = AdminStat.objects.get_or_create(pk=1)
        group = instance.groups.first().name
        # Update counts based on the user's group
        if group == 'Front_Desk':
            admin_stat.front_desk_users += 1
        elif group == 'Doctor':
            admin_stat.doctor_users += 1
        elif group == 'Admin':
            admin_stat.admin_users += 1
        admin_stat.save()

# Signal receiver to handle actions when a patient is created
@receiver(patient_created)
def handle_patient_created(sender, patient, created_by, **kwargs):
    # Create a notification for the user who created the patient record
    Notification.objects.create(
        user=created_by,
        message=f"A new patient record for {patient.first_name} {patient.last_name} has been created."
    )

    # Update the total patient count in AdminStat
    admin_stat, _ = AdminStat.objects.get_or_create(pk=1)
    admin_stat.total_patients += 1
    admin_stat.save()

# Signal receiver to handle actions when a Procedure is created or updated
@receiver(post_save, sender=Procedure)
def procedure_created_or_updated(sender, instance, created, **kwargs):
    # Create a notification for the user who created or updated the procedure
    Notification.objects.create(
        user=User.objects.get(id=instance.created_by_id),
        message=f"A procedure {instance.procedure_name} for patient {instance.patient.first_name} {instance.patient.last_name} has been " + ('created.' if created else 'updated.')
    )

    # Update the total procedure count in AdminStat if the procedure was newly created
    if created:
        admin_stat, _ = AdminStat.objects.get_or_create(pk=1)
        admin_stat.total_procedures += 1
        admin_stat.save()

@receiver(pre_save, sender=Procedure)
def delete_old_file_on_update(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_file = Procedure.objects.get(pk=instance.pk).report
        except Procedure.DoesNotExist:
            return
        else:
            if old_file and old_file != instance.report:
                if os.path.isfile(old_file.path):
                    os.remove(old_file.path)

@receiver(post_delete, sender=Procedure)
def delete_file_on_delete(sender, instance, **kwargs):
    if instance.report:
        if os.path.isfile(instance.report.path):
            os.remove(instance.report.path)