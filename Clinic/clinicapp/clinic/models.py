from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField


# Create your models here.
class MyUser(AbstractUser):
    gender_choices = [
        ('male', 'Nam'),
        ('female', 'Nữ')
    ]

    role_choices = [
        ('patient', 'Bệnh nhân'),
        ('doctor', 'Bác sĩ'),
        ('nurse', 'Y tá'),
        ('admin', 'Admin')
    ]

    fullname = models.CharField(max_length=200, null=False)
    date_of_birth = models.DateField(null=True)
    gender = models.CharField(max_length=10, choices=gender_choices, default='male')
    phone_number = models.CharField(max_length=15, null=True)
    email = models.EmailField(max_length=255, null=True, unique=True)
    avatar = CloudinaryField('avatar', null=True)
    role = models.CharField(
        max_length=10,
        choices=role_choices,
        default='patient',
        null=False
    )

    def __str__(self):
        return self.fullname


class Doctor(models.Model):
    speciality_choices = [
        ('Nội khoa', 'Nội khoa'),
        ('Ngoại khoa', 'Ngoại khoa'),
        ('Nhi khoa', 'Nhi khoa'),
        ('Sản khoa', 'Sản khoa'),
        ('Răng hàm mặt', 'Răng hàm mặt'),
        ('Da liễu', 'Da liễu'),
        ('Tim mạch', 'Tim mạch'),
        ('Thần kinh', 'Thần kinh'),
        ('Tai mũi họng', 'Tai mũi họng'),
        ('Mắt', 'Mắt'),
        ('Nội tiết', 'Nội tiết'),
        ('Chấn thương chỉnh hình', 'Chấn thương chỉnh hình'),
        ('Chẩn đoán hình ảnh', 'Chẩn đoán hình ảnh'),
        ('Y học cổ truyền', 'Y học cổ truyền'),
    ]

    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, related_name='doctor', null=False)
    speciality = models.CharField(max_length=50, choices=speciality_choices, null=False)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.fullname


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Shift(BaseModel):
    start_time = models.TimeField(null=False)
    end_time = models.TimeField(null=False)

    def __str__(self):
        return f'{self.start_time} - {self.end_time}'


class WorkSchedule(BaseModel):
    employee = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='work_schedules',
        null=False
    )
    shift = models.ManyToManyField(
        Shift,
        related_name='work_schedules',
    )
    from_date = models.DateField(null=True)  # null!
    to_date = models.DateField(null=True)  # null!

    def __str__(self):
        return f'{self.employee} - {self.from_date} - {self.to_date}'


class Appointment(BaseModel):
    status_choices = [
        ('pending_confirmation', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('cancelled', 'Đã huỷ'),
        ('examination_in_progress', 'Đang khám'),
        ('exam_completed', 'Đã khám'),
    ]

    patient = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='patient_appointments', null=False)
    doctor = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='doctor_appointments', null=True)
    nurse = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='nurse_appointments', null=True)
    date = models.DateField(null=False)  # ngày khám
    time = models.TimeField(null=False)  # giờ khám
    description = models.TextField(null=True)  # triệu chứng ban đầu
    cancellation_reason = models.CharField(max_length=150, null=True, blank=True)  # lý do huỷ
    status = models.CharField(max_length=40, choices=status_choices, default='Chờ xác nhận')

    def __str__(self):
        return f'{self.patient} - {self.doctor} - {self.date} - {self.time}'


class Medicine(BaseModel):
    unit_choices = [
        ('Viên', 'Viên'),
        ('Chai', 'Chai'),
        ('Ống', 'Ống'),
        ('Tuýp', 'Tuýp'),
        ('Gói', 'Gói'),
    ]

    name = models.CharField(max_length=50, null=False)
    unit = models.CharField(max_length=20, choices=unit_choices, null=False)  # đơn vị tính
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Prescription(BaseModel):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescription', null=False)
    patient = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='patient_prescriptions', null=False)
    doctor = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='doctor_prescriptions', null=False)
    diagnosis = models.TextField(null=False)  # chẩn đoán
    # medicines = models.ManyToManyField(Medicine, through='PrescriptionDetail')  # thuốc
    days_supply = models.IntegerField(null=False)  # cấp toa trong bao nhiêu ngày
    advice = models.TextField(null=False)  # lời dặn
    follow_up_date = models.DateField(null=True)  # ngày tái khám
    expiry_date = models.DateField(null=True, blank=True)  # ngày hết hạn

    def __str__(self):
        return f'{self.patient} - {self.doctor} - {self.created_date}'


class PrescriptionDetail(models.Model):
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='prescription_details',
        null=False
    )
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name='prescription_details',
    )
    quantity = models.IntegerField(null=False)  # số lượng
    morning_dose = models.IntegerField(default=0)  # liều sáng
    afternoon_dose = models.IntegerField(default=0)  # liều trưa
    evening_dose = models.IntegerField(default=0)  # liều tối
    note = models.TextField(null=True)  # ghi chú

    def __str__(self):
        return f'{self.prescription} - {self.medicine} - {self.quantity}'


class Invoice(BaseModel):
    payment_method_choices = [
        ('Tiền mặt', 'Tiền mặt'),
        ('e-Wallet', 'e-Wallet'),
    ]
    status_choices = [
        ('pending', 'Chờ thanh toán'),
        ('paid', 'Đã thanh toán'),
        ('cancelled', 'Đã huỷ'),
    ]

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='invoice', null=False)
    patient = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='patient_invoices',
        null=False
    )
    created_by = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='nurse_invoices',
        null=False
    )
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='invoice', null=True)
    prescription_cost = models.DecimalField(max_digits=10, decimal_places=2, null=False)  # chi phí ra toa
    examination_cost = models.DecimalField(max_digits=10, decimal_places=2, null=False)  # chi phí khám bệnh
    total = models.DecimalField(max_digits=10, decimal_places=2, null=False)  # tổng tiền
    payment_method = models.CharField(max_length=20, choices=payment_method_choices, null=True)  # hình thức thanh toán
    payment_date = models.DateTimeField(null=True)  # ngày thanh toán
    status = models.CharField(max_length=20, choices=status_choices, default='Chờ thanh toán')
    note = models.CharField(max_length=150, null=True, blank=True)  # ghi chú

# class Notification(BaseModel):
#     appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='notifications', null=False)
#     content = models.TextField(null=False)
#     is_read = models.BooleanField(default=False)
#     read_date = models.DateTimeField(null=True)
