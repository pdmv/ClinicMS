from django.core.mail import send_mail
from .models import Appointment


def is_max_appointment_per_day_reached(date):
    return Appointment.objects.filter(date=date).count() == 100


def send_book_appointment_success_email(appointment):
    patient_name = appointment.patient.fullname
    doctor_name = appointment.doctor.fullname
    date = appointment.date.strftime('%d/%m/%Y')
    time = appointment.time.strftime('%H:%M')
    subject = f'Xác nhận đặt lịch hẹn thành công - ID lịch hẹn: {appointment.id}'
    message = f"""
    Chào {patient_name},

    Cảm ơn bạn đã đặt lịch hẹn với bác sĩ {doctor_name} vào {date} lúc {time}.

    Thông tin lịch hẹn của bạn:
    - Bác sĩ: {doctor_name}
    - Ngày: {date}
    - Giờ: {time}
    - Triệu chứng ban đầu: {appointment.description}
    - Trạng thái: {appointment.get_status_display()}

    Vui lòng chờ xác nhận lịch hẹn.

    Trân trọng,

    Phòng khám Global Health
    """
    recipient_list = [appointment.patient.email]
    send_mail(subject, message, None, recipient_list)


def send_confirm_appointment_success_email(appointment):
    patient_name = appointment.patient.fullname
    doctor_name = appointment.doctor.fullname
    nurse_name = appointment.nurse.fullname
    date = appointment.date.strftime('%d/%m/%Y')
    time = appointment.time.strftime('%H:%M')
    subject = f'Đã xác nhận lịch hẹn - ID lịch hẹn: {appointment.id}'
    message = f"""
    Chào {patient_name},
    
    Lịch hẹn của bạn với bác sĩ {doctor_name} vào {date} lúc {time} đã được xác nhận.

    Thông tin lịch hẹn của bạn:
    - Bác sĩ: {doctor_name}
    - Ngày: {date}
    - Giờ: {time}
    - Triệu chứng ban đầu: {appointment.description}
    - Y tá xác nhận: {nurse_name}
    - Trạng thái: {appointment.get_status_display()}

    Vui lòng đến phòng khám trước 15 phút để làm thủ tục.

    Trân trọng,

    Phòng khám Global Health
    """
    recipient_list = [appointment.patient.email]
    send_mail(subject, message, None, recipient_list)


def send_cancel_appointment_success_email(appointment):
    patient_name = appointment.patient.fullname
    doctor_name = appointment.doctor.fullname
    date = appointment.date.strftime('%d/%m/%Y')
    time = appointment.time.strftime('%H:%M')
    subject = f'Đã huỷ lịch hẹn - ID lịch hẹn: {appointment.id}'
    message = f"""
    Chào {patient_name},
    
    Lịch hẹn của bạn với bác sĩ {doctor_name} vào {date} lúc {time} đã được huỷ.

    Thông tin lịch hẹn của bạn:
    - Bác sĩ: {doctor_name}
    - Ngày: {date}
    - Giờ: {time}
    - Triệu chứng ban đầu: {appointment.description}
    - Lý do: {appointment.cancellation_reason}
    - Trạng thái: {appointment.get_status_display()}

    Cảm ơn bạn đã sử dụng dịch vụ và mong rằng chúng tôi sẽ tiếp tục được phục vụ bạn trong tương lai.

    Trân trọng,

    Phòng khám Global Health
    """
    recipient_list = [appointment.patient.email]
    send_mail(subject, message, None, recipient_list)