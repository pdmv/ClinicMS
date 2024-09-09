from datetime import datetime, timedelta

from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from django.db.models import Sum
# from .forms import TimeFilterForm

from datetime import datetime

from .dao import (
    send_book_appointment_success_email,
    send_confirm_appointment_success_email,
    send_cancel_appointment_success_email,
    is_max_appointment_per_day_reached
)
from .models import (
    MyUser, Doctor, WorkSchedule, Appointment, Medicine, Prescription, PrescriptionDetail, Invoice
)
from .perms import IsAdmin, IsDoctor, IsNurse, IsPatient
from .serializers import (
    MyUserSerializer, MyUserListSerializer,
    DoctorSerializer, DoctorListSerializer, DoctorIntroduceSerializer,
    AppointmentSerializer, AppointmentListSerializer, AppointmentDetailSerializer,
    MedicineSerializer, PrescriptionSerializer, PrescriptionListSerializer,
    InvoiceSerializer, InvoiceListSerializer
)


# Create your views here.
class MyUserViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = MyUser.objects.filter(is_active=True).all()
    serializer_class = MyUserSerializer
    pagination_class = PageNumberPagination

    def get_permissions(self):
        if self.action in ['register', ]:
            if self.request.data.get('role') == 'patient':
                permission_classes = [permissions.AllowAny]
            else:
                permission_classes = [IsAdmin]
        elif self.action in ['profile', 'update_profile', 'appointments', 'prescriptions', 'invoices']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['list', ]:
            permission_classes = [IsAdmin]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    @action(methods=['post'], url_path='register', url_name='register', detail=False)
    def register(self, request, *args, **kwargs):
        serializer = MyUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data.get('role')
        user = serializer.save()
        user.groups.add(Group.objects.get_or_create(name=role))
        return Response(MyUserSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(methods=['get'], url_path='profile', url_name='profile', detail=False)
    def profile(self, request):
        return Response(MyUserSerializer(request.user).data)

    @action(methods=['patch'], url_path='update-profile', url_name='update-profile', detail=False)
    def update_profile(self, request, *args, **kwargs):
        serializer = MyUserSerializer(data=request.data, instance=request.user, partial=True)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(request.user, field, value)

        role = request.data.get('role')
        if role and role != request.user.role:
            if IsAdmin().has_permission(request, self):
                request.user.groups.clear()
                request.user.groups.add(Group.objects.get_or_create(name=role))
            else:
                return Response({'error': 'You are not allowed to update role of this user'},
                                status=status.HTTP_403_FORBIDDEN)

        request.user.save()
        return Response(MyUserSerializer(request.user).data, status=status.HTTP_200_OK)

    @action(methods=['get'], url_path='appointments', url_name='appointments', detail=False)
    def appointments(self, request, *args, **kwargs):
        app_status = request.query_params.get('status', None)
        app_date = request.query_params.get('date', None)

        filters = {}
        if app_status:
            filters['status'] = app_status
            if app_date:
                filters['date'] = app_date

        user_roles = {
            'doctor': lambda: {'doctor': request.user},
            'nurse': lambda: {},  # Trả về tất cả lịch hẹn
            'patient': lambda: {'patient': request.user}
        }

        role_filter = user_roles.get(request.user.role)
        if role_filter:
            filters.update(role_filter())

        queryset = Appointment.objects.filter(**filters).all()
        serializer = AppointmentListSerializer(queryset, many=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AppointmentListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=['get'], url_path='prescriptions', url_name='prescriptions', detail=False)
    def prescriptions(self, request, *args, **kwargs):
        date = request.query_params.get('date', None)

        filters = {}
        if date:
            filters['created_date'] = date
        if request.user.role == 'patient':
            filters['patient'] = request.user
        if request.user.role == 'doctor':
            filters['doctor'] = request.user

        queryset = Prescription.objects.filter(**filters).all()
        serializer = PrescriptionListSerializer(queryset, many=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PrescriptionListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=['get'], url_path='invoices', url_name='invoices', detail=False)
    def invoices(self, request, *args, **kwargs):
        invoice_status = request.query_params.get('status', None)
        invoice_date = request.query_params.get('date', None)

        filters = {}
        if invoice_status:
            filters['status'] = invoice_status
        if invoice_date:
            filters['created_date__date'] = invoice_date

        if request.user.role == 'patient':
            filters['patient'] = request.user

        queryset = Invoice.objects.filter(**filters).all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = InvoiceListSerializer(page, many=True)
        else:
            serializer = InvoiceListSerializer(queryset, many=True)

        # Xử lý lỗi
        if not serializer.data:
            return Response({'error': 'No invoices found'}, status=status.HTTP_404_NOT_FOUND)

        return self.get_paginated_response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = MyUser.objects.filter(is_active=True).all()
        serializer = MyUserListSerializer(queryset, many=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MyUserListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class DoctorViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    pagination_class = PageNumberPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'time_slots', 'introduce']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        queryset = Doctor.objects.all()
        serializer = DoctorListSerializer(queryset, many=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = DoctorListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        doctor = Doctor.objects.get(pk=pk)
        serializer = DoctorSerializer(doctor)
        return Response(serializer.data)

    @action(methods=['get'], url_path='time-slots', url_name='time-slots', detail=True)
    def time_slots(self, request, pk=None):
        doctor = get_object_or_404(Doctor, pk=pk)

        # Lấy thời gian từ query parameters
        date_param = request.query_params.get('date', None)

        if not date_param:
            return Response({'error': 'Missing date parameter'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            date_obj = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

        if is_max_appointment_per_day_reached(date_obj):
            return Response({'error': 'Maximum appointment per day reached'}, status=status.HTTP_400_BAD_REQUEST)

        work_schedules = WorkSchedule.objects.filter(
            employee=doctor.user,
            from_date__lte=date_obj,
            to_date__gte=date_obj,
            is_available=True
        ).prefetch_related('shift')

        booked_appointments = Appointment.objects.filter(
            doctor=doctor.user,
            date=date_obj,
            status__in=['pending_confirmation', 'confirmed']
        ).values_list('time', flat=True)

        time_slots = []
        for schedule in work_schedules:
            for shift in schedule.shift.all():
                current_time = datetime.combine(date_obj, shift.start_time)
                end_time = datetime.combine(date_obj, shift.end_time)

                while current_time <= end_time and current_time + timedelta(minutes=30) <= end_time:
                    if current_time.time() not in booked_appointments:
                        time_slots.append(current_time.strftime('%H:%M'))
                    current_time += timedelta(minutes=30)

        return Response({'available_time_slots': time_slots})

    @action(methods=['get'], url_path='introduce', url_name='introduce', detail=True)
    def introduce(self, request, pk=None):
        doctor = get_object_or_404(Doctor, pk=pk)
        serializer = DoctorIntroduceSerializer(doctor)
        return Response(serializer.data)


def is_slot_available(date, time, doctor_id):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        time_obj = datetime.strptime(time, '%H:%M').time()
    except ValueError:
        return False

    if is_max_appointment_per_day_reached(date_obj):
        return False

    # Kiểm tra lịch làm việc và lịch hẹn đã đặt
    work_schedules = WorkSchedule.objects.filter(
        employee_id=doctor_id,
        from_date__lte=date_obj,
        to_date__gte=date_obj,
        is_available=True
    ).prefetch_related('shift')

    for schedule in work_schedules:
        for shift in schedule.shift.all():
            start_time = datetime.combine(date_obj, shift.start_time)
            end_time = datetime.combine(date_obj, shift.end_time)

            if start_time <= datetime.combine(date_obj, time_obj) <= end_time:
                if not Appointment.objects.filter(
                        doctor_id=doctor_id,
                        date=date_obj,
                        time=time_obj,
                        status__in=['pending_confirmation', 'confirmed']
                ).exists():
                    return True

    return False


class AppointmentViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    def get_permissions(self):
        if self.action in ['create', ]:
            permission_classes = [IsPatient]
        elif self.action in ['retrieve', 'cancel', 'confirm']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['examination', 'complete_examination']:
            permission_classes = [IsDoctor]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        data = request.data
        patient = data.get('patient')
        doctor = data.get('doctor')
        date = data.get('date')
        time = data.get('time')

        # Kiểm tra nếu time slot trống và hợp lệ cho bác sĩ
        if not self.is_slot_available(date, time, doctor):
            return Response({'error': 'Time slot is not available for the selected doctor'},
                            status=status.HTTP_400_BAD_REQUEST)

        if patient is None:
            data['patient'] = request.user.id
        if doctor is None:
            return Response({'error': 'Doctor is required'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AppointmentSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        appointment = serializer.save()
        send_book_appointment_success_email(appointment)
        return Response(AppointmentDetailSerializer(appointment).data, status=status.HTTP_201_CREATED)

    @action(methods=['post'], url_path='cancel', url_name='cancel', detail=True)
    def cancel(self, request, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=kwargs.get('pk'))
        if IsPatient().has_permission(request, self) and appointment.patient != request.user:
            return Response({'error': 'You are not allowed to cancel this appointment'},
                            status=status.HTTP_403_FORBIDDEN)
        if appointment.status in ['pending_confirmation', 'confirmed']:
            appointment.status = 'cancelled'
            appointment.cancellation_reason = request.data.get('cancellation_reason', '')
            appointment.save()

            send_cancel_appointment_success_email(appointment)
            return Response(AppointmentSerializer(appointment).data)
        else:
            return Response({'error': 'Appointment cannot be cancelled'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], url_path='confirm', url_name='confirm', detail=True)
    def confirm(self, request, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=kwargs.get('pk'))
        if appointment.status == 'pending_confirmation':
            if request.user.groups.filter(name='nurse').exists():
                appointment.status = 'confirmed'
                appointment.nurse = request.user
                appointment.save()

                send_confirm_appointment_success_email(appointment)
                return Response(AppointmentSerializer(appointment).data)
            else:
                return Response({'error': 'Only nurses can confirm appointments'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Appointment cannot be confirmed'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], url_path='examination', url_name='examination', detail=True)
    def examination(self, request, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=kwargs.get('pk'))
        if appointment.status == 'confirmed':
            if appointment.doctor == request.user:
                appointment.status = 'examination_in_progress'
                appointment.save()
                return Response(AppointmentSerializer(appointment).data)
            else:
                return Response({'error': 'Only doctor for this appointment can start examination'},
                                status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Appointment cannot be started'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], url_path='complete-examination', url_name='complete-examination', detail=True)
    def complete_examination(self, request, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=kwargs.get('pk'))
        if appointment.status == 'examination_in_progress':
            if appointment.doctor == request.user:
                appointment.status = 'exam_completed'
                appointment.save()
                return Response(AppointmentSerializer(appointment).data)
            else:
                return Response({'error': 'Only doctor for this appointment can complete examination'},
                                status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Appointment cannot be completed'}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=kwargs.get('pk'))

        if IsPatient().has_permission(request, self) and appointment.patient != request.user:
            return Response({'error': 'You are not allowed to view this appointment'}, status=status.HTTP_403_FORBIDDEN)
        serializer = AppointmentDetailSerializer(appointment)
        return Response(serializer.data)

    def is_slot_available(self, date, time, doctor_id):
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time, '%H:%M').time()
        except ValueError:
            return False

        # Kiểm tra lịch làm việc và lịch hẹn đã đặt
        work_schedules = WorkSchedule.objects.filter(
            employee_id=doctor_id,
            from_date__lte=date_obj,
            to_date__gte=date_obj,
            is_available=True
        ).prefetch_related('shift')

        for schedule in work_schedules:
            for shift in schedule.shift.all():
                start_time = datetime.combine(date_obj, shift.start_time)
                end_time = datetime.combine(date_obj, shift.end_time)

                if start_time <= datetime.combine(date_obj, time_obj) <= end_time:
                    if not Appointment.objects.filter(
                            doctor_id=doctor_id,
                            date=date_obj,
                            time=time_obj
                    ).exists():
                        return True

        return False


class MedicineViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Medicine.objects.filter(active=True).all()
    serializer_class = MedicineSerializer
    pagination_class = PageNumberPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'find']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    @action(methods=['get'], url_path='find', url_name='find', detail=False)
    def find(self, request, **kwargs):
        kw = request.query_params.get('kw', None)
        medicine = Medicine.objects.filter(name__icontains=kw)
        serializer = MedicineSerializer(medicine, many=True)
        page = self.paginate_queryset(medicine)
        if page is not None:
            serializer = MedicineSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class PrescriptionViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = Prescription.objects.filter(active=True).all()
    serializer_class = PrescriptionSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['create', ]:
            permission_classes = [IsDoctor]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        data = request.data

        if data.get('doctor') is None:
            data['doctor'] = request.user.id

        appointment = Appointment.objects.get(pk=data.get('appointment'))
        if appointment.status != 'exam_completed':
            return Response({'error': 'Appointment is not completed yet'}, status=status.HTTP_400_BAD_REQUEST)
        if Prescription.objects.filter(appointment=appointment).exists():
            return Response({'error': 'Prescription already created for this appointment'},
                            status=status.HTTP_400_BAD_REQUEST)
        if appointment.doctor != request.user:
            return Response({'error': 'You are not allowed to create prescription for this appointment'},
                            status=status.HTTP_403_FORBIDDEN)
        if data.get('patient') is None:
            data['patient'] = appointment.patient.id

        serializer = PrescriptionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        prescription = serializer.save()

        for medicine_data in data.get('prescription_details', []):
            medicine = Medicine.objects.get(pk=medicine_data['medicine'])
            detail = PrescriptionDetail.objects.create(
                prescription=prescription,
                medicine=medicine,
                quantity=medicine_data['quantity'],
                morning_dose=medicine_data.get('morning_dose', 0),
                afternoon_dose=medicine_data.get('afternoon_dose', 0),
                evening_dose=medicine_data.get('evening_dose', 0),
                note=medicine_data.get('note', None),
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InvoiceViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = Invoice.objects.filter(active=True).all()
    serializer_class = InvoiceSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', ]:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['create', 'cancel', 'pay']:
            permission_classes = [IsNurse]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = InvoiceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], url_path='pay', url_name='pay', detail=True)
    def pay(self, request, *args, **kwargs):
        try:
            invoice = Invoice.objects.get(pk=kwargs.get('pk'))  # Lock row for update
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

        payment_method = request.data.get('payment_method')
        if payment_method is None:
            return Response({'error': 'Payment method is required'}, status=status.HTTP_400_BAD_REQUEST)

        if invoice.status != 'pending':
            return Response({'error': 'Invoice cannot be paid'}, status=status.HTTP_400_BAD_REQUEST)

        invoice.status = 'paid'
        invoice.payment_method = payment_method
        invoice.payment_date = datetime.now()
        invoice.save()

        return Response(InvoiceSerializer(invoice).data)

    @action(methods=['post'], url_path='cancel', url_name='cancel', detail=True)
    def cancel(self, request, *args, **kwargs):
        invoice = Invoice.objects.get(pk=kwargs.get('pk'))
        if invoice.status in ['pending', 'paid']:
            invoice.status = 'cancelled'
            invoice.save()
            return Response(InvoiceSerializer(invoice).data)
        else:
            return Response({'error': 'Invoice cannot be cancelled'}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=kwargs.get('pk'))
        if request.user.role == 'patient' and invoice.patient != request.user:
            return Response({'error': 'You are not allowed to view this invoice'}, status=status.HTTP_403_FORBIDDEN)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data)

    def get_appointment(self, pk):
        try:
            return Appointment.objects.get(pk=pk)
        except Appointment.DoesNotExist:
            raise Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)

    def check_appointment_status(self, appointment):
        if appointment.status != 'exam_completed':
            raise Response({'error': 'Appointment is not completed yet'}, status=status.HTTP_400_BAD_REQUEST)

    def check_existing_invoice(self, appointment):
        if Invoice.objects.filter(appointment=appointment, status__in=('pending', 'paid')).exists():
            raise Response({'error': 'Invoice already created for this appointment and cancelled'},
                           status=status.HTTP_400_BAD_REQUEST)


# Clinic Statistics
#
# def report_view(request):
#     # if not request.user.is_superuser:
#     #     return HttpResponseForbidden("Only admins can access this page.")
#     return render(request, 'clinic/activity-stats.html')

