from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Patient, Procedure, AdminStat, Notification
from django.utils import timezone
import re
import base64

# Serializer for the User model
class UserSerializer(serializers.ModelSerializer):
    # Custom field to accept role during user creation
    role = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']
        # Password should only be used for writing, not reading
        extra_kwargs = {
            'password': {'write_only': True}
        }

    # Custom validation for the User model fields
    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')

        # Validate username length and format
        if len(username) > 150:
            raise serializers.ValidationError({"username": "Username must be 150 characters or fewer."})
        if not re.match(r'^[\w.@+-]+$', username):
            raise serializers.ValidationError({"username": "Username can only contain letters, digits, and @/./+/-/_ characters."})
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "Username already taken."})

        # Validate email format and uniqueness
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise serializers.ValidationError({"email": "Enter a valid email address."})
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Email address already registered."})

        # Validate password strength (length, digits, cases, and special characters)
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

        # Validate the role field to ensure the specified role exists
        if not Group.objects.filter(name=role).exists():
            raise serializers.ValidationError({"role": "Role does not exist."})

        return data

    # Create a new user and assign them to a group based on the provided role
    def create(self, validated_data):
        role = validated_data.pop('role')
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()

        # Assign the user to the specified role (group)
        group = Group.objects.get(name=role)
        user.groups.add(group)

        return user

# Serializer for the Patient model
class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            'id', 'first_name', 'last_name', 'mobile_number', 'address',
            'gender', 'birthdate', 'email', 'city', 'state', 'pincode',
            'emergency_contact_name', 'emergency_contact_mobile_number', 'language', 'created_date'
        ]

        # `created_date` should be read-only as it's set automatically
        extra_kwargs = {
            'created_date': {'read_only': True}
        } 

    # Custom validation for the Patient model fields
    def validate(self, data):

        # Validate mobile number format (10 digits)
        mobile_number = data.get('mobile_number')
        emergency_contact_mobile_number = data.get('emergency_contact_mobile_number')

        if len(mobile_number) != 10 or not mobile_number.isdigit():
            raise serializers.ValidationError({"mobile_number": "Mobile number must be exactly 10 digits."})

        if len(emergency_contact_mobile_number) != 10 or not emergency_contact_mobile_number.isdigit():
            raise serializers.ValidationError({"emergency_contact_mobile_number": "Emergency contact mobile number must be exactly 10 digits."})
        
        # Validate pincode length (6 digits)
        if len(data.get('pincode', '')) != 6:
            raise serializers.ValidationError({"pincode": "Pincode must be 6 digits long."})

        # Validate email format
        email = data.get('email')
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise serializers.ValidationError({"email": "Enter a valid email address."})

        return data

# Serializer for the Procedure model
class ProcedureSerializer(serializers.ModelSerializer):
    # Include nested serializers for patient and created_by fields
    patient = PatientSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    report_base64 = serializers.SerializerMethodField()

    class Meta:
        model = Procedure
        fields = [
            'id', 'patient', 'status', 'procedure_datetime', 'category',
            'procedure_name', 'clinic_address', 'notes', 'report', 'report_base64', 'created_by', 'created_date', 'updated_date'
        ]

        # `created_date` and `updated_date` are read-only as they are set automatically
        extra_kwargs = {
            'created_date': {'read_only': True},
            'updated_date': {'read_only': True},
        } 

    # Custom validation for the Procedure model fields
    def validate(self, data):
        # Validate the procedure_datetime field to ensure it is not in the future
        if 'procedure_datetime' in data:
            procedure_datetime = data.get('procedure_datetime')
            if procedure_datetime > timezone.now():
                raise serializers.ValidationError({"procedure_datetime": "Procedure date cannot be in the future."})
            
        if 'report' in data:
            report = data.get('report')
            if report and not report.name.endswith('.pdf'):
                raise serializers.ValidationError({"report": "Only PDF files are accepted."})

        return data
    
    def get_report_base64(self, obj):
        if obj.report:
            with open(obj.report.path.replace('\\', '/'), 'rb') as file:
                file_content = file.read()
                return base64.b64encode(file_content).decode('utf-8')
        return None
    
# Serializer for the AdminStat model
class AdminStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminStat
        fields = [
            'total_patients', 'total_procedures', 'front_desk_users',
            'doctor_users', 'admin_users', 'last_updated'
        ]

# Serializer for the Notification model
class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'timestamp']
