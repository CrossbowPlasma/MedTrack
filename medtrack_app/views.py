from django.contrib.auth import authenticate
from django.contrib.auth.models import User
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

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        user = request.user
        role = user.groups.first().name
        
        if role == "Admin":
            # If the user is an Admin, return a list of all users
            users = User.objects.all()
            users_data = []
            for usr in users:
                role_user = usr.groups.first()  # Ask about this again
                user_role = role_user.name
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
        user = request.user
        notifications = Notification.objects.filter(user=user)

        if not notifications.exists():
            return Response({"detail": "No notifications available."}, status=status.HTTP_404_NOT_FOUND)

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminStatView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        try:
            admin_stat = AdminStat.objects.get()#latest('last_updated')
        except AdminStat.DoesNotExist:
            return Response({"detail": "No admin stats available."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminStatSerializer(admin_stat)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class PatientView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin | IsFrontDesk]

    def get(self, request):
        # Handle GET requests to list patients
        name = request.query_params.get('name', None)
        patient_city = request.query_params.get('city', None)

        if name and patient_city:
            patients = Patient.objects.filter(first_name__icontains=name, city=patient_city)
        elif name:
            patients = Patient.objects.filter(first_name__icontains=name)
        elif patient_city:
            patients = Patient.objects.filter(city=patient_city)
        else:
            patients = Patient.objects.all()

        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Handle POST requests to create a new patient
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            patient = serializer.save()
            
            patient_created.send(sender=self.__class__, patient=patient, created_by=request.user)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProcedureView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin | IsDoctor]

    def get(self, request):
        # Handle GET requests to list procedure
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            try:
                procedures = Procedure.objects.filter(patient_id=patient_id)
            except Procedure.DoesNotExist:
                return Response({"error": "No procedures found for the given patient ID."}, status=status.HTTP_404_NOT_FOUND)
        else:
            procedures = Procedure.objects.all()

        serializer = ProcedureSerializer(procedures, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)    
    
    def post(self, request):
        # Handle POST requests to create a new procedure
        patient_id = request.data.get('patient')
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"patient": "Patient does not exist."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProcedureSerializer(data=request.data)
        if serializer.is_valid():
            procedure = serializer.save(patient=patient, created_by=request.user)
            return Response(ProcedureSerializer(procedure).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        # Handle PUT requests to update procedure
        try:
            procedure = Procedure.objects.get(pk=pk)
        except Procedure.DoesNotExist:
            return Response({"detail": "Procedure not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProcedureSerializer(procedure, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
