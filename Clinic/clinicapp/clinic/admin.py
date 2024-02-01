from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group

from .models import MyUser


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
            'password'
        ]
        widgets = {
            'password': forms.PasswordInput(),
        }


class MyUserAdmin(admin.ModelAdmin):
    form = MyUserForm

    list_display = ('id', 'fullname', 'email', 'role', 'is_superuser', 'is_staff', 'is_active')
    list_filter = ('role',)
    search_fields = ('fullname', 'id')
    ordering = ('-id',)

    def save_model(self, request, obj, form, change):
        obj.password = make_password(obj.password)
        obj.groups.clear()
        obj.groups.add(Group.objects.get(name=obj.role))
        super().save_model(request, obj, form, change)

    class Meta:
        model = MyUser


# Register your models here.
admin.site.register(MyUser, MyUserAdmin)
