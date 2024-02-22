from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.utils.html import mark_safe

from .models import MyUser, Shift, WorkSchedule, Appointment, Doctor, Medicine


admin.site.site_header = 'Clinic Administration'
admin.site.site_title = 'Clinic Administration'


class MyUserForm(forms.ModelForm):
    class Meta:
        model = MyUser
        fields = [
            'fullname',
            'date_of_birth',
            'gender',
            'phone_number',
            'email',
            'avatar',
            'role',
            'username',
            'password',
        ]
        widgets = {
            'password': forms.PasswordInput(),
        }


class MyUserAdmin(admin.ModelAdmin):
    form = MyUserForm

    list_display = ('id', 'fullname', 'email', 'role', 'is_active')
    list_filter = ('role',)
    search_fields = ('fullname', 'id')
    ordering = ('-id',)
    readonly_fields = ('current_avatar',)

    @staticmethod
    def current_avatar(obj):
        if obj.avatar:
            return mark_safe(f'<img src="{obj.avatar.url}" alt={obj.fullname} width="100" height="100">')

    def save_model(self, request, obj, form, change):
        obj.password = make_password(obj.password)
        obj.groups.clear()
        obj.groups.add(Group.objects.get(name=obj.role))
        super().save_model(request, obj, form, change)

    class Meta:
        model = MyUser


class ShiftAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_time', 'end_time')
    list_filter = ('start_time', 'end_time')
    search_fields = ('start_time', 'id')
    ordering = ('-id',)

    class Meta:
        model = Shift


class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'from_date', 'to_date')
    list_filter = ('employee', 'from_date')
    search_fields = ('doctor', 'id')
    ordering = ('-id',)

    class Meta:
        model = WorkSchedule


class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'nurse', 'time', 'status')
    list_filter = ('patient', 'doctor', 'nurse', 'time', 'status')
    search_fields = ('patient', 'id')
    ordering = ('-id',)

    class Meta:
        model = Appointment


class DoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'speciality', 'description')
    list_filter = ('speciality',)
    search_fields = ('user__fullname', 'id')
    ordering = ('-id',)

    user = MyUserForm

    class Meta:
        model = Doctor


class MedicineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unit')
    list_filter = ('name', 'unit')
    search_fields = ('name', 'id')
    ordering = ('-id',)

    class Meta:
        model = Medicine


# Register your models here.
admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(WorkSchedule, WorkScheduleAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Medicine, MedicineAdmin)

