from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from rest_framework import serializers

from .models import MyUser, Appointment, Shift


class MyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'fullname', 'date_of_birth', 'gender', 'phone_number', 'email', 'avatar', 'role', 'username', 'password']
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


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
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
