from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Patient, Procedure, AdminStat, Notification
from django.utils import timezone
import re

class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')

        # Validate username
        if len(username) > 150:
            raise serializers.ValidationError({"username": "Username must be 150 characters or fewer."})
        if not re.match(r'^[\w.@+-]+$', username):
            raise serializers.ValidationError({"username": "Username can only contain letters, digits, and @/./+/-/_ characters."})
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "Username already taken."})

        # Validate email
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise serializers.ValidationError({"email": "Enter a valid email address."})
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Email address already registered."})

        # Validate password
        if len(password) < 8:
            raise serializers.ValidationError({"password": "Password must be at least 8 characters long."})
        if not re.search(r'\d', password):
            raise serializers.ValidationError({"password": "Password must contain at least one digit."})
        if not re.search(r'[A-Z]', password):
            raise serializers.ValidationError({"password": "Password must contain at least one uppercase letter."})
        if not re.search(r'[a-z]', password):
            raise serializers.ValidationError({"password": "Password must contain at least one lowercase letter."})
        if not re.search(r'[@$!%*?&#]', password):
            raise serializers.ValidationError({"password": "Password must contain at least one special character."})

        # Validate role
        if not Group.objects.filter(name=role).exists():
            raise serializers.ValidationError({"role": "Role does not exist."})

        return data

    def create(self, validated_data):
        role = validated_data.pop('role')
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()

        group = Group.objects.get(name=role)
        user.groups.add(group)

        return user

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            'id', 'first_name', 'last_name', 'mobile_number', 'address',
            'gender', 'birthdate', 'email', 'city', 'state', 'pincode',
            'emergency_contact_name', 'emergency_contact_mobile_number', 'language', 'created_date'
        ]

        extra_kwargs = {
            'created_date': {'read_only': True}
        } 

    def validate(self, data):
        gender_mapping = {
            'M': 'Male',
            'F': 'Female',
            'O': 'Other',
            'Male': 'Male',
            'Female': 'Female',
            'Other': 'Other'
        }

        # Validate mobile numbers
        mobile_number = data.get('mobile_number')
        emergency_contact_mobile_number = data.get('emergency_contact_mobile_number')

        if len(mobile_number) != 10 or not mobile_number.isdigit():
            raise serializers.ValidationError({"mobile_number": "Mobile number must be exactly 10 digits."})

        if len(emergency_contact_mobile_number) != 10 or not emergency_contact_mobile_number.isdigit():
            raise serializers.ValidationError({"emergency_contact_mobile_number": "Emergency contact mobile number must be exactly 10 digits."})
        
        # Validate pincode length
        if len(data.get('pincode', '')) != 6:
            raise serializers.ValidationError({"pincode": "Pincode must be 6 digits long."})

        # Validate gender
        gender = data.get('gender').capitalize()
        if gender not in gender_mapping:
            raise serializers.ValidationError({"gender": "Gender must be one of the following: Male, Female, Others or M, F, O"})
        data['gender'] = gender_mapping.get(gender, gender)

        # Validate email
        email = data.get('email')
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise serializers.ValidationError({"email": "Enter a valid email address."})

        return data

class ProcedureSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only = True)
    created_by = UserSerializer(read_only = True)

    class Meta:
        model = Procedure
        fields = [
            'id', 'patient', 'status', 'procedure_datetime', 'category',
            'procedure_name', 'clinic_address', 'notes', 'report', 'created_by', 'created_date', 'updated_date'
        ]

        extra_kwargs = {
            'created_date': {'read_only': True},
            'updated_date': {'read_only': True},
        } 

    def validate(self, data):
        # Validate status if provided
        if 'status' in data:
            status = data.get('status').lower()
            valid_statuses = ['preparation', 'in-progress', 'not-done', 'on-hold', 'stopped', 'completed', 'entered-in-error', 'unknown']
            if status not in valid_statuses:
                raise serializers.ValidationError({"status": f"Status must be one of the following: {', '.join(valid_statuses)}."})
            data['status'] = status

        # Validate category if provided
        if 'category' in data:
            category = data.get('category').lower()
            valid_categories = ['psychiatry', 'counseling', 'surgical', 'diagnostic', 'chiropractic', 'social-service']
            if category not in valid_categories:
                raise serializers.ValidationError({"category": f"Category must be one of the following: {', '.join(valid_categories)}."})
            data['category'] = category

        # Validate procedure_datetime if provided
        if 'procedure_datetime' in data:
            procedure_datetime = data.get('procedure_datetime')
            if procedure_datetime > timezone.now():
                raise serializers.ValidationError({"procedure_datetime": "Procedure date cannot be in the future."})

        return data
    
class AdminStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminStat
        fields = [
            'total_patients', 'total_procedures', 'front_desk_users',
            'doctor_users', 'admin_users', 'last_updated'
        ]

class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'timestamp']
