from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from rest_framework import serializers

from .models import MyUser, Doctor, Appointment, Medicine, Prescription, PrescriptionDetail, Invoice

CLOUDINARY_DOMAIN = 'https://res.cloudinary.com/dyuafq1hx/'


class MyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
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
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data.get('password'))
        if validated_data.get('role') != instance.role:
            instance.groups.clear()
            instance.groups.add(Group.objects.get_or_create(name=validated_data.get('role')))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Check if avatar is present in data and not empty
        if 'avatar' in data and data['avatar']:
            # Append Cloudinary domain to avatar URL
            data['avatar'] = f"{CLOUDINARY_DOMAIN}{data['avatar']}"

        return data


class MyUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = [
            'id', 'fullname', 'gender'
        ]


class DoctorSerializer(serializers.ModelSerializer):
    user = MyUserSerializer()

    class Meta:
        model = Doctor
        fields = ('id', 'user', 'speciality', 'description')


class DoctorListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ('id', 'user', 'speciality')

    def get_user(self, obj):
        if obj.user.avatar:
            obj.user.avatar = f"{CLOUDINARY_DOMAIN}{obj.user.avatar}"
        user = {
            'id': obj.user.id,
            'fullname': obj.user.fullname,
            'avatar': obj.user.avatar
        }
        return user


class DoctorIntroduceSerializer(DoctorListSerializer):
    class Meta:
        model = Doctor
        fields = ('id', 'user', 'speciality', 'description')


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
        read_only_fields = ('id', 'status', 'created_date', 'updated_date')
        extra_kwargs = {
            'patient': {'required': False, 'allow_null': True},
        }

    def create(self, validated_data):
        validated_data['status'] = 'pending_confirmation'
        return super().create(validated_data)


class AppointmentDetailSerializer(serializers.ModelSerializer):
    patient = MyUserListSerializer(read_only=True)
    doctor = MyUserListSerializer(read_only=True)
    nurse = MyUserListSerializer(read_only=True)

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
        read_only_fields = ('id', 'status', 'created_date', 'updated_date')


class AppointmentListSerializer(serializers.ModelSerializer):
    patient = MyUserListSerializer(read_only=True)
    doctor = MyUserListSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'doctor',
            'date',
            'time',
            'status',
            'created_date',
            'updated_date'
        ]
        read_only_fields = ('id', 'status', 'created_date', 'updated_date')


class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = [
            'id',
            'name',
            'unit',
            'description'
        ]
        extra_kwargs = {
            'id': {
                'read_only': True
            }
        }


class PrescriptionDetailSerializer(serializers.ModelSerializer):
    medicine = MedicineSerializer(read_only=True)

    class Meta:
        model = PrescriptionDetail
        fields = [
            # 'id',
            # 'prescription',
            'medicine',
            'quantity',
            'morning_dose',
            'afternoon_dose',
            'evening_dose',
            'note'
        ]
        extra_kwargs = {
            'id': {
                'read_only': True
            }
        }


class PrescriptionSerializer(serializers.ModelSerializer):
    prescription_details = PrescriptionDetailSerializer(many=True, read_only=True)
    patient = MyUserListSerializer(read_only=True)
    doctor = MyUserListSerializer(read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id',
            'appointment',
            'patient',
            'doctor',
            'diagnosis',
            'prescription_details',
            'days_supply',
            'advice',
            'follow_up_date',
            'expiry_date'
        ]
        extra_kwargs = {
            'id': {
                'read_only': True
            },
            'appointment': {
                'required': True
            },
            'prescription_details': {
                'required': True
            },
        }


class PrescriptionListSerializer(serializers.ModelSerializer):
    patient = MyUserListSerializer(read_only=True)
    doctor = MyUserListSerializer(read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id',
            'appointment',
            'patient',
            'doctor',
            'created_date',
        ]
        extra_kwargs = {
            'id': {
                'read_only': True
            },
            'appointment': {
                'required': True
            },
        }


class InvoiceSerializer(serializers.ModelSerializer):
    patient = MyUserListSerializer(read_only=True)
    created_by = MyUserListSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'appointment',
            'patient',
            'prescription',
            'prescription_cost',
            'examination_cost',
            'total',
            'payment_method',
            'payment_date',
            'status',
            'created_by',
            'note'
        ]
        extra_kwargs = {
            'patient': {
                'required': False
            },
            'status': {
                'required': False
            },
            'total': {
                'required': False,
                'read_only': True
            },
            'payment_date': {
                'required': False
            },
        }

    def create(self, validated_data):
        validated_data['total'] = validated_data['prescription_cost'] + validated_data['examination_cost']
        validated_data['created_by'] = self.context['request'].user
        validated_data['status'] = 'pending'
        validated_data['patient'] = validated_data['appointment'].patient
        if Prescription.objects.filter(appointment=validated_data['appointment']).exists():
            validated_data['prescription'] = Prescription.objects.get(appointment=validated_data['appointment'])
        else:
            validated_data['prescription'] = None

        return super().create(validated_data)


class InvoiceListSerializer(serializers.ModelSerializer):
    patient = MyUserListSerializer(read_only=True)
    created_by = MyUserListSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'appointment',
            'patient',
            'total',
            'status',
            'created_by',
        ]
        extra_kwargs = {
            'id': {
                'read_only': True
            },
            'appointment': {
                'required': True
            },
            'patient': {
                'required': False
            },
            'status': {
                'required': False
            },
            'total': {
                'required': False,
                'read_only': True
            },
            'payment_date': {
                'required': False
            },
        }