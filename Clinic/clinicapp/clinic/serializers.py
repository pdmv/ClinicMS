from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from rest_framework import serializers

from . import models


class MyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MyUser
        fields = [
            'id', 'fullname', 'date_of_birth', 'gender', 'phone_number', 'email', 'avatar', 'role',
            'username', 'password'
        ]
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'id': {
                'read_only': True
            }
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        if validated_data.get('role') == 'admin':
            validated_data['is_superuser'] = True
            validated_data['is_staff'] = True
        elif validated_data.get('role') == 'doctor':
            validated_data['is_staff'] = True
        elif validated_data.get('role') == 'nurse':
            validated_data['is_staff'] = True

        user = super().create(validated_data)
        return user

    def update(self, instance, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        if validated_data.get('role') != instance.role:
            instance.groups.clear()
            instance.groups.add(Group.objects.get(name=validated_data.get('role')))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Check if avatar is present in data and not empty
        if 'avatar' in data and data['avatar']:
            # Append Cloudinary domain to avatar URL
            data['avatar'] = f"https://res.cloudinary.com/dyuafq1hx/{data['avatar']}"

        return data


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Doctor
        fields = [
            'id',
            'user',
            'speciality',
            'description'
        ]
        extra_kwargs = {
            'id': {
                'read_only': True
            }
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Check if user is present in data and not empty
        if 'user' in data and data['user']:
            # Append Cloudinary domain to avatar URL
            data['user'] = MyUserSerializer(data['user']).data

        return data


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Appointment
        fields = [
            'id',
            'patient',
            'doctor',
            'nurse',
            'date',
            'time',
            'description',
            'cancellation_reason',
            'status',
            'created_date',
            'updated_date'
        ]
        extra_kwargs = {
            'id': {
                'read_only': True
            },
            'created_date': {
                'read_only': True
            },
            'updated_date': {
                'read_only': True
            }
        }

    def create(self, validated_data):
        validated_data['status'] = 'pending_confirmation'
        return super().create(validated_data)

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #
    #     # Check if patient is present in data and not empty
    #     if 'patient' in data and data['patient']:
    #         # Append Cloudinary domain to avatar URL
    #         data['patient'] = MyUserSerializer(data['patient']).data
    #
    #     # Check if doctor is present in data and not empty
    #     if 'doctor' in data and data['doctor']:
    #         # Append Cloudinary domain to avatar URL
    #         data['doctor'] = MyUserSerializer(data['doctor']).data
    #
    #     # Check if nurse is present in data and not empty
    #     if 'nurse' in data and data['nurse']:
    #         # Append Cloudinary domain to avatar URL
    #         data['nurse'] = MyUserSerializer(data['nurse']).data
    #
    #     # Check if shift is present in data and not empty
    #     if 'shift' in data and data['shift']:
    #         # Append Cloudinary domain to avatar URL
    #         data['shift'] = ShiftSerializer(data['shift']).data
    #
    #     return data


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Shift
        fields = [
            'id',
            'start_time',
            'end_time',
            'created_date',
            'updated_date',
            'active'
        ]
        extra_kwargs = {
            'id': {
                'read_only': True
            }
        }


# class WorkScheduleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.WorkSchedule
#         fields = [
#             'id',
#             'employee',
#             'shift',
#             'date',
#             'is_available',
#             'created_date',
#             'updated_date',
#             'active'
#         ]
#         extra_kwargs = {
#             'id': {
#                 'read_only': True
#             }
#         }
#
#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#
#         # Check if employee is present in data and not empty
#         if 'employee' in data and data['employee']:
#             # Append Cloudinary domain to avatar URL
#             data['employee'] = MyUserSerializer(data['employee']).data
#
#         # Check if shift is present in data and not empty
#         if 'shift' in data and data['shift']:
#             # Append Cloudinary domain to avatar URL
#             data['shift'] = ShiftSerializer(data['shift']).data
#
#         return data
#
#
# class MedicineSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Medicine
#         fields = [
#             'id',
#             'name',
#             'description',
#             'created_date',
#             'updated_date',
#             'active'
#         ]
#         extra_kwargs = {
#             'id': {
#                 'read_only': True
#             }
#         }
#
#
# class PrescriptionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Prescription
#         fields = [
#             'id',
#             'appointment',
#             'medicine',
#             'dosage',
#             'created_date',
#             'updated_date',
#             'active'
#         ]
#         extra_kwargs = {
#             'id': {
#                 'read_only': True
#             }
#         }
#
#     def create(self, validated_data):
#         appointment = validated_data.get('appointment')
#         appointment.status = 'examination_in_progress'
#         appointment.save()
#         return super().create(validated_data)
#
#
#
# class PrescriptionDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Prescription
#         fields = [
#             'id',
#             'appointment',
#             'medicine',
#             'dosage',
#             'created_date',
#             'updated_date',
#             'active'
#         ]
#         extra_kwargs = {
#             'id': {
#                 'read_only': True
#             }
#         }
#
#
# class InvoiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Invoice
#         fields = [
#             'id',
#             'appointment',
#             'total',
#             'created_date',
#             'updated_date',
#             'active'
#         ]
#         extra_kwargs = {
#             'id': {
#                 'read_only': True
#             }
#         }


