import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medtrack.settings')
django.setup()

from django.contrib.auth.models import User, Group

def create_initial_data():
    # Create groups
    groups = ['Front_Desk', 'Doctor', 'Admin']
    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f'Created group: {group_name}')
        else:
            print(f'Group already exists: {group_name}')

    # Create a superuser
    username = 'admin'
    email = 'admin@example.com'
    password = 'admin'
    
    superuser, created = User.objects.get_or_create(username=username, defaults={
        'email': email,
        'is_superuser': True,
        'is_staff': True,
        'is_active': True
    })
    
    if created:
        superuser.set_password(password)
        superuser.save()
        print(f'Superuser created with username: {username}')
    else:
        print(f'Superuser already exists with username: {username}')

    # Assign the "Admin" group to the superuser
    admin_group = Group.objects.get(name='Admin')
    if not superuser.groups.filter(name='Admin').exists():
        superuser.groups.add(admin_group)
        print(f'Assigned superuser to "Admin" group')
    else:
        print(f'Superuser already in "Admin" group')

if __name__ == "__main__":
    create_initial_data()
