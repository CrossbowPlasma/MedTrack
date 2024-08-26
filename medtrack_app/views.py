from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import base64
from .models import Notification, AdminStat, Patient, Procedure
from .serializers import NotificationSerializer, AdminStatSerializer, PatientSerializer, ProcedureSerializer
from .signals import patient_created


class CustomLoginView(APIView):
    def post(self, request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return Response({"error": "Authorization header missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded_credentials = base64.b64decode(auth_header).decode('utf-8')
            username, password = decoded_credentials.split(':')
        except (TypeError, ValueError) as e:
            return Response({"error": "Invalid authorization token format"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if user is None:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        role = user.groups.first().name

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
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        role = request.data.get('role')

        if not username or not email or not password or not role:
            return Response({"error": "Username, email, and password and role are required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        group = Group.objects.filter(name=role).first()
        if group:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.groups.add(group)
        else:
            return Response({"error": "Role does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Invalidate the refresh token
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            role = user.groups.first().name
            
            if role == "Admin":
                # If the user is an Admin, return a list of all users
                users = User.objects.all()
                users_data = []
                for usr in users:
                    user_role = usr.groups.first().name if usr.groups.exists() else None
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

        except TokenError:
            return Response({"error": "Invalid token or token has expired."}, status=status.HTTP_401_UNAUTHORIZED)

        
class NotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        notifications = Notification.objects.filter(user=user)

        if not notifications.exists():
            return Response({"detail": "No notifications available."}, status=status.HTTP_404_NOT_FOUND)

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminStatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Check if the user is in the Admin group
        if not request.user.groups.filter(name='Admin').exists():
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        try:
            admin_stat = AdminStat.objects.latest('last_updated')
        except AdminStat.DoesNotExist:
            return Response({"detail": "No admin stats available."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminStatSerializer(admin_stat)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class CreatePatientView(APIView):
    def post(self, request):
        # Check if the user is in the Front_Desk or Admin group
        user_groups = request.user.groups.values_list('name', flat=True)
        if not ('Front_Desk' in user_groups or 'Admin' in user_groups):
            return Response({"detail": "You do not have permission to create patients."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            patient = serializer.save()
            
            patient_created.send(sender=self.__class__, patient=patient, created_by=request.user)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListPatientView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Check if the user is in the Front_Desk or Admin group
        user_groups = request.user.groups.values_list('name', flat=True)
        if 'Front_Desk' not in user_groups and 'Admin' not in user_groups:
            return Response({"detail": "You do not have permission to view patients."}, status=status.HTTP_403_FORBIDDEN)

        name = request.query_params.get('name', None)
        patient_id = request.query_params.get('id', None)

        if name:
            patients = Patient.objects.filter(first_name__icontains=name)
        elif patient_id:
            patients = Patient.objects.filter(id=patient_id)
        else:
            patients = Patient.objects.all()

        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateProcedureView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Check if the user is in the Doctor or Admin group
        user_groups = request.user.groups.values_list('name', flat=True)
        if 'Doctor' not in user_groups and 'Admin' not in user_groups:
            return Response({"detail": "You do not have permission to create procedures."}, status=status.HTTP_403_FORBIDDEN)

        patient_id = request.data.get('patient')
        if not Patient.objects.filter(id=patient_id).exists():
            return Response({"patient": "Patient does not exist."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProcedureSerializer(data=request.data)
        if serializer.is_valid():
            procedure = serializer.save(created_by=request.user)
            return Response(ProcedureSerializer(procedure).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListProcedureView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Check if the user is in the Doctor or Admin group
        user_groups = request.user.groups.values_list('name', flat=True)
        if 'Doctor' not in user_groups and 'Admin' not in user_groups:
            return Response({"detail": "You do not have permission to view procedures."}, status=status.HTTP_403_FORBIDDEN)

        procedures = Procedure.objects.all()
        serializer = ProcedureSerializer(procedures, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
 
    
class UpdateProcedureView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        # Check if the user is in the Doctor or Admin group
        user_groups = request.user.groups.values_list('name', flat=True)
        if 'Doctor' not in user_groups and 'Admin' not in user_groups:
            return Response({"detail": "You do not have permission to edit procedures."}, status=status.HTTP_403_FORBIDDEN)

        try:
            procedure = Procedure.objects.get(pk=pk)
        except Procedure.DoesNotExist:
            return Response({"detail": "Procedure not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProcedureSerializer(procedure, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)