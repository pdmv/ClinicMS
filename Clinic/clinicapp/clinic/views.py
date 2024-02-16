from rest_framework import viewsets, generics, permissions, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import Group

from . import models
from . import serializers
from .perms import IsAdmin, IsDoctor, IsNurse, IsPatient


# Create your views here.
class MyUserViewSet(viewsets.ModelViewSet):
    queryset = models.MyUser.objects.filter(is_active=True).all()
    serializer_class = serializers.MyUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = serializers.MyUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data.get('role')

        if role == 'patient':
            user = serializer.save()
            user.groups.add(Group.objects.get(name='patient'))
            return Response(serializers.MyUserSerializer(user).data, status=status.HTTP_201_CREATED)
        else:
            if request.user.is_authenticated and request.user.groups.filter(name='admin').exists():
                user = serializer.save()
                user.groups.add(Group.objects.get(name=role))
                return Response(serializers.MyUserSerializer(user).data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'You are not allowed to create this user'},
                                status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        serializer = serializers.MyUserSerializer(data=request.data, instance=self.get_object())
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data.get('role')

        if role == 'patient':
            user = serializer.save()
            return Response(serializers.MyUserSerializer(user).data, status=status.HTTP_200_OK)
        else:
            if request.user.is_authenticated and request.user.groups.filter(name='admin').exists():
                user = serializer.save()
                return Response(serializers.MyUserSerializer(user).data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'You are not allowed to update this user'},
                                status=status.HTTP_403_FORBIDDEN)

    # ??????????
    # def list(self, request, *args, **kwargs):
    #     if request.user.is_authenticated and request.user.groups.filter(name='admin').exists():
    #         return super().list(request, *args, **kwargs)
    #     else:
    #         return Response({'error': 'You are not allowed to view this list'},
    #                         status=status.HTTP_403_FORBIDDEN)
    #
    # def retrieve(self, request, *args, **kwargs):
    #     if request.user.is_authenticated and request.user.groups.filter(name='admin').exists():
    #         return super().retrieve(request, *args, **kwargs)
    #     else:
    #         return Response({'error': 'You are not allowed to view this user'},
    #                         status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.groups.filter(name='admin').exists():
            super().destroy(request, *args, **kwargs)
            return Response({'success': 'User deleted'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': 'You are not allowed to delete this user'},
                            status=status.HTTP_403_FORBIDDEN)

    @action(methods=['get'], url_path='current-user', url_name='current-user', detail=False)
    def current_user(self, request):
        return Response(serializers.MyUserSerializer(request.user).data)

    @action(methods=['get'], url_path='appointments', url_name='appointments', detail=False)
    def appointments(self, request):
        if request.user.is_authenticated:
            if request.user.groups.filter(name='patient').exists():
                queryset = models.Appointment.objects.filter(patient=request.user, active=True).all()
                serializer = models.serializers.AppointmentSerializer(queryset, many=True)
                return Response(serializer.data)
            elif request.user.groups.filter(name='doctor').exists():
                queryset = models.Appointment.objects.filter(doctor=request.user, active=True).all()
                serializer = serializers.AppointmentSerializer(queryset, many=True)
                return Response(serializer.data)
            elif request.user.groups.filter(name='nurse').exists():
                queryset = models.Appointment.objects.filter(nurse=request.user, active=True).all()
                serializer = serializers.AppointmentSerializer(queryset, many=True)
                return Response(serializer.data)
        else:
            return Response({'error': 'You are not allowed to view this list'},
                            status=status.HTTP_403_FORBIDDEN)


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = models.Appointment.objects.filter(active=True).all()
    serializer_class = serializers.AppointmentSerializer

    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.groups.filter(name='patient').exists():
            if request.data.get('patient') is None:
                request.data['patient'] = request.user.id
            serializer = serializers.AppointmentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            appointment = serializer.save()
            return Response(serializers.AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'You are not allowed to create this appointment'},
                            status=status.HTTP_403_FORBIDDEN)

    @action(methods=['post'], url_path='confirm', url_name='confirm', detail=True)
    def confirm(self, request, *args, **kwargs):
        appointment = self.get_object()
        if appointment.status == 'pending_confirmation':
            if request.user.is_authenticated and request.user.groups.filter(name='nurse').exists():
                if (request.data.get('doctor') is not None
                        and models.MyUser.objects.filter(pk=request.data.get('doctor')).exists()
                        and models.MyUser.objects.get(pk=request.data.get('doctor')).groups.filter(name='doctor').exists()):
                    appointment.doctor = models.MyUser.objects.get(pk=request.data.get('doctor'))
                else:
                    return Response({'error': 'Doctor does not exist'}, status=status.HTTP_400_BAD_REQUEST)

                appointment.status = 'confirmed'
                appointment.nurse = request.user
                appointment.save()
                return Response(serializers.AppointmentSerializer(appointment).data)
            else:
                return Response({'error': 'Only nurses can confirm appointments'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Appointment cannot be confirmed'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], url_path='cancel', url_name='cancel', detail=True)
    def cancel(self, request):
        appointment = self.get_object()
        if appointment.status in ['pending_confirmation', 'confirmed']:
            if request.user.is_authenticated and request.user.groups.filter(name='patient').exists():
                appointment.status = 'pending_cancellation_confirmation'
                appointment.cancellation_reason = request.data.get('cancellation_reason', '')
                appointment.save()
                return Response(serializers.AppointmentSerializer(appointment).data)
            else:
                return Response({'error': 'You are not authorized to cancel this appointment'},
                                status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Appointment cannot be cancelled'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], url_path='start-examination', url_name='start-examination', detail=True)
    def start_examination(self, request, *args, **kwargs):
        appointment = self.get_object()
        if appointment.status == 'confirmed':
            if request.user.is_authenticated and request.user.groups.filter(
                    name='doctor').exists():  # thieu kiem tra doctor co phai la doctor cua appointment khong --> has_permission
                appointment.status = 'examination_in_progress'
                appointment.save()
                return Response(serializers.AppointmentSerializer(appointment).data)
            else:
                return Response({'error': 'Only doctors can start examinations'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Appointment cannot be started'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], url_path='complete-examination', url_name='complete-examination', detail=True)
    def complete_examination(self, request, *args, **kwargs):
        appointment = self.get_object()
        if appointment.status == 'examination_in_progress':
            if request.user.is_authenticated and request.user.groups.filter(name='doctor').exists():
                if models.Appointment.objects.filter(pk=kwargs.get('pk'), doctor=request.user).exists():
                    appointment.status = 'exam_completed'
                    appointment.save()
                    return Response(serializers.AppointmentSerializer(appointment).data)
                else:
                    return Response({'error': 'You are not authorized to complete this appointment'},
                                    status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Only doctors can complete examinations'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Appointment cannot be completed'}, status=status.HTTP_400_BAD_REQUEST)

    # ??????????
    # @action(methods=['post'], url_path='confirm-cancel', url_name='confirm-cancel', detail=True)
    # def confirm_cancel(self, request, *args, **kwargs):
    #     appointment = self.get_object()
    #     if appointment.status == 'pending_cancellation_confirmation':
    #         if request.user.is_authenticated and request.user.groups.filter(name='nurse').exists():
    #             appointment.status = 'cancelled'
    #             appointment.save()
    #             return Response(serializers.AppointmentSerializer(appointment).data)
    #         else:
    #             return Response({'error': 'Only nurses can confirm cancellations'}, status=status.HTTP_403_FORBIDDEN)
    #     else:
    #         return Response({'error': 'Appointment cannot be confirmed'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], url_path='completed-appointments', url_name='completed-appointments', detail=False)
    def completed_appointments(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.groups.filter(name='nurse').exists():
            queryset = models.Appointment.objects.filter(status='exam_completed').all()
            serializer = serializers.AppointmentSerializer(queryset, many=True)
            return Response(serializer.data)
        else:
            return Response({'error': 'You are not allowed to view this list'},
                            status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        appointment = self.get_object()
        if appointment.patient == request.user:
            if appointment.status == 'pending_confirmation':
                serializer = serializers.AppointmentSerializer(appointment, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            else:
                return Response({'error': 'Appointment cannot be updated'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'You are not authorized to update this appointment'},
                            status=status.HTTP_403_FORBIDDEN)

    def retrieve(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if models.Appointment.objects.filter(pk=kwargs.get('pk')).exists():
                if (models.Appointment.objects.get(pk=kwargs.get('pk')).patient == request.user
                        or models.Appointment.objects.get(pk=kwargs.get('pk')).doctor == request.user):
                    return super().retrieve(request, *args, **kwargs)
                elif request.user.groups.filter(name='nurse').exists():
                    return super().retrieve(request, *args, **kwargs)
                else:
                    return Response({'error': 'You are not allowed to view this appointment'},
                                    status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Appointment does not exist'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'You are not allowed to view this appointment'},
                            status=status.HTTP_403_FORBIDDEN)

    def list(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.groups.filter(name='admin').exists():
            return super().list(request, *args, **kwargs)
        else:
            return Response({'error': 'You are not allowed to view this list'},
                            status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        appointment = self.get_object()
        if appointment.patient == request.user:
            if appointment.status == 'pending_confirmation':
                appointment.active = False
                appointment.save()
                return Response({'success': 'Appointment deleted'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'Appointment cannot be deleted'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'You are not authorized to delete this appointment'},
                            status=status.HTTP_403_FORBIDDEN)


# class PrescriptionViewSet(viewsets.ModelViewSet):
#     queryset = models.Prescription.objects.filter(active=True).all()
#     serializer_class = serializers.PrescriptionSerializer
#
#     def create(self, request, *args, **kwargs):
#         if request.user.is_authenticated and request.user.groups.filter(name='doctor').exists():
#             serializer = serializers.PrescriptionSerializer(data=request.data)
#             serializer.is_valid(raise_exception=True)
#
#             prescription = serializer.save()
#             return Response(serializers.PrescriptionSerializer(prescription).data, status=status.HTTP_201_CREATED)
#         else:
#             return Response({'error': 'You are not allowed to create this prescription'},
#                             status=status.HTTP_403_FORBIDDEN)
#
#     def update(self, request, *args, **kwargs):
#         prescription = self.get_object()
#         if prescription.doctor == request.user:
#             serializer = serializers.PrescriptionSerializer(prescription, data=request.data)
#             serializer.is_valid(raise_exception=True)
#             serializer.save()
#             return Response(serializer.data)
#         else:
#             return Response({'error': 'You are not authorized to update this prescription'},
#                             status=status.HTTP_403_FORBIDDEN)
#
#     def retrieve(self, request, *args, **kwargs):
#         if request.user.is_authenticated and models.Prescription.objects.filter(pk=kwargs.get('pk')).exists():
#             if models.Prescription.objects.get(pk=kwargs.get('pk')).doctor == request.user:
#                 return super().retrieve(request, *args, **kwargs)
#             elif request.user.groups.filter(name='nurse').exists():
#                 return super().retrieve(request, *args, **kwargs)
#             else:
#                 return Response({'error': 'You are not allowed to view this prescription'},
#                                 status=status.HTTP_403_FORBIDDEN)
#         else:
#             return Response({'error': 'Prescription does not exist'}, status=status.HTTP_404_NOT_FOUND)
#
#     def list(self, request, *args, **kwargs):
#         if request.user.is_authenticated and request.user.groups.filter(name='admin').exists():
#             return super().list(request, *args, **kwargs)
#         else:
#             return Response({'error': 'You are not allowed to view this list'},
#                             status=status.HTTP_403_FORBIDDEN)
#
#     def destroy(self, request, *args, **kwargs):
#         prescription = self.get_object()
#         if prescription.doctor == request.user:
#             prescription.active = False
#             prescription.save()
#             return Response({'success': 'Prescription deleted'}, status=status.HTTP_204_NO_CONTENT)

# class MyUserViewSet(viewsets.ModelViewSet):
#     queryset = MyUser.objects.filter(is_active=True).all()
#     serializer_class = serializers.MyUserSerializer
#
#     def get_queryset(self):
#         if IsAdmin().has_permission(self.request, self):
#             return MyUser.objects.all()
#         else:
#             return MyUser.objects.filter(pk=self.request.user.id)
#
#     def get_permissions(self):
#         if self.action in ['list', 'destroy']:
#             permission_classes = [IsAdmin, permissions.IsAuthenticated]
#         else:
#             permission_classes = [permissions.IsAuthenticated]
#         return [permission() for permission in permission_classes]
#
#     def create(self, request, *args, **kwargs):
#         serializer = serializers.MyUserSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         role = serializer.validated_data.get('role')
#
#         if role == 'patient':
#             user = serializer.save()
#             user.groups.add(Group.objects.get(name='patient'))
#             return Response(serializers.MyUserSerializer(user).data, status=status.HTTP_201_CREATED)
#         else:
#             if IsAdmin().has_permission(request, self):
#                 user = serializer.save()
#                 user.groups.add(Group.objects.get(name=role))
#                 return Response(serializers.MyUserSerializer(user).data, status=status.HTTP_201_CREATED)
#             else:
#                 return Response({'error': 'You are not allowed to create this user'},
#                                 status=status.HTTP_403_FORBIDDEN)
#
#     def update(self, request, *args, **kwargs):
#         serializer = serializers.MyUserSerializer(data=request.data, instance=self.get_object())
#         serializer.is_valid(raise_exception=True)
#
#         role = serializer.validated_data.get('role')
#
#         if role == 'patient':
#             user = serializer.save()
#             return Response(serializers.MyUserSerializer(user).data, status=status.HTTP_200_OK)
#         else:
#             if IsAdmin().has_permission(request, self):
#                 user = serializer.save()
#                 return Response(serializers.MyUserSerializer(user).data, status=status.HTTP_200_OK)
#             else:
#                 return Response({'error': 'You are not allowed to update this user'},
#                                 status=status.HTTP_403_FORBIDDEN)
#
#     @action(methods=['get'], url_path='current-user', url_name='current-user', detail=False)
#     def current_user(self, request):
#         return Response(serializers.MyUserSerializer(request.user).data)
#
#     @action(methods=['get'], url_path='appointments', url_name='appointments', detail=False)
#     def appointments(self, request):
#         if IsPatient().has_permission(request, self):
#             queryset = Appointment.objects.filter(patient=request.user, active=True).all()
#             serializer = serializers.AppointmentSerializer(queryset, many=True)
#             return Response(serializer.data)
#         elif IsDoctor().has_permission(request, self):
#             queryset = Appointment.objects.filter(doctor=request.user, active=True).all()
#             serializer = serializers.AppointmentSerializer(queryset, many=True)
#             return Response(serializer.data)
#         elif IsNurse().has_permission(request, self):
#             queryset = Appointment.objects.filter(nurse=request.user, active=True).all()
#             serializer = serializers.AppointmentSerializer(queryset, many=True)
#             return Response(serializer.data)
