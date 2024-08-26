from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Patient, Procedure, AdminStat, Notification
from django.utils import timezone
import re

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            'id', 'first_name', 'last_name', 'mobile_number', 'address',
            'gender', 'birthdate', 'email', 'city', 'state', 'pincode',
            'emergency_contact_name', 'emergency_contact_mobile_number', 'language'
        ]

    def validate(self, data):
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
        gender = data.get('gender')
        if gender not in ['M', 'F', 'O']:
            raise serializers.ValidationError({"gender": "Gender must be one of the following: M, F, O."})

        # Validate email
        email = data.get('email')
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise serializers.ValidationError({"email": "Enter a valid email address."})

        return data

class ProcedureSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only = True)

    class Meta:
        model = Procedure
        fields = [
            'id', 'patient', 'status', 'procedure_datetime', 'category',
            'procedure_name', 'clinic_address', 'notes', 'report', 'created_by'
        ]

def validate(self, data):
        # Validate status if provided
        if 'status' in data:
            status = data.get('status')
            valid_statuses = ['preparation', 'in-progress', 'not-done', 'on-hold', 'stopped', 'completed', 'entered-in-error', 'unknown']
            if status not in valid_statuses:
                raise serializers.ValidationError({"status": f"Status must be one of the following: {', '.join(valid_statuses)}."})

        # Validate category if provided
        if 'category' in data:
            category = data.get('category')
            valid_categories = ['psychiatry', 'counseling', 'surgical', 'diagnostic', 'chiropractic', 'social-service']
            if category not in valid_categories:
                raise serializers.ValidationError({"category": f"Category must be one of the following: {', '.join(valid_categories)}."})

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
        fields = ['id', 'user', 'message', 'created_at']
