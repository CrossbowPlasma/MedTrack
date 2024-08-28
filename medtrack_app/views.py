from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import base64
from .models import Notification, AdminStat, Patient, Procedure
from .serializers import NotificationSerializer, AdminStatSerializer, PatientSerializer, ProcedureSerializer, UserSerializer
from .signals import patient_created
from .permissions import IsAdmin, IsDoctor, IsFrontDesk


class CustomLoginView(APIView):
    def post(self, request, *args, **kwargs):
        # Retrieve the Authorization header from the request
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return Response({"error": "Authorization header missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Decode the base64 encoded credentials
            decoded_credentials = base64.b64decode(auth_header).decode('utf-8')
            username, password = decoded_credentials.split(':')
        except (TypeError, ValueError) as e:
            return Response({"error": "Invalid authorization token format"}, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate the user with the provided credentials
        user = authenticate(username=username, password=password)
        if user is None:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Get the user's role from their group
        role = user.groups.first().name

        # Return user details along with the generated tokens
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': role,
            'access': access_token,
            'refresh': refresh_token
        }, status=status.HTTP_200_OK)


class RegisterView(APIView):
    def post(self, request, *args, **kwargs):
        # Use the UserSerializer to validate and create a new user
        serializer = UserSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Invalidate the refresh token
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Blacklist the token to log the user out
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Retrieve the current user and their role
        user = request.user
        role = user.groups.first().name
        
        if role == "Admin":
            # If the user is an Admin, return a list of all users
            users = User.objects.all()
            users_data = []
            for usr in users:
                user_group = usr.groups.first()
                user_role = user_group.name
                users_data.append({
                    'id': usr.id,
                    'username': usr.username,
                    'email': usr.email,
                    'role': user_role,
                })
            return Response(users_data, status=status.HTTP_200_OK)
        else:
            # If the user is not an Admin, return only their own info
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': role,
            }, status=status.HTTP_200_OK)

        
class NotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Retrieve notifications for the authenticated user
        user = request.user
        notifications = Notification.objects.filter(user=user)

        if not notifications:
            return Response({"detail": "No notifications available."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize and return the notifications
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminStatView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        try:
            # Retrieve the AdminStat object
            admin_stat = AdminStat.objects.get()
        except AdminStat.DoesNotExist:
            return Response({"detail": "No admin stats available."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize and return the AdminStat data
        serializer = AdminStatSerializer(admin_stat)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class PatientView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin | IsFrontDesk]

    def get(self, request):
        # Handle GET requests to list patients
        name = request.query_params.get('name', None)
        patient_city = request.query_params.get('city', None)

        # Filter patients by name and city if provided
        if name and patient_city:
            patients = Patient.objects.filter(first_name__icontains=name, city=patient_city)
        elif name:
            patients = Patient.objects.filter(first_name__icontains=name)
        elif patient_city:
            patients = Patient.objects.filter(city=patient_city)
        else:
            patients = Patient.objects.all()

        # Serialize and return the list of patients
        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Handle POST requests to create a new patient
        data = request.data.copy()
        data['gender'] = data['gender'].capitalize()

        serializer = PatientSerializer(data=data)
        if serializer.is_valid():
            patient = serializer.save()
            
            # Trigger the patient_created signal
            patient_created.send(sender=self.__class__, patient=patient, created_by=request.user)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProcedureView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin | IsDoctor]

    def get(self, request):
        # Handle GET requests to list procedures
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            try:
                # Filter procedures by patient ID
                procedures = Procedure.objects.filter(patient_id=patient_id)
            except Procedure.DoesNotExist:
                return Response({"error": "No procedures found for the given patient ID."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Retrieve all procedures if no patient ID is provided
            procedures = Procedure.objects.all()

        # Serialize and return the list of procedures
        serializer = ProcedureSerializer(procedures, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)    
    
    def post(self, request):
        # Handle POST requests to create a new procedure
        patient_id = request.data.get('patient')
        try:
            # Ensure the patient exists
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"patient": "Patient does not exist."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        data['status'] = data['status'].lower()
        data['category'] = data['category'].lower()

        # Serialize and validate the procedure data
        serializer = ProcedureSerializer(data=data)
        if serializer.is_valid():
            # Save the procedure and associate it with the patient and user
            procedure = serializer.save(patient=patient, created_by=request.user)
            return Response(ProcedureSerializer(procedure).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        # Handle PUT requests to update a procedure
        try:
            # Retrieve the procedure by its primary key
            procedure = Procedure.objects.get(pk=pk)
        except Procedure.DoesNotExist:
            return Response({"detail": "Procedure not found."}, status=status.HTTP_404_NOT_FOUND)
        
        data = request.data.copy()
        if data.get('status'):
            data['status'] = data['status'].lower()
        if data.get('category'):
            data['category'] = data['category'].lower()

        # Serialize and validate the update data
        serializer = ProcedureSerializer(procedure, data=data, partial=True)
        if serializer.is_valid():
            # Save the updated procedure data
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
