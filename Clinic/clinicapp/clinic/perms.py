from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='admin').exists()

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.groups.filter(name='admin').exists()


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='doctor').exists()


class IsNurse(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='nurse').exists()


class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='patient').exists()


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.patient == request.user or obj.doctor == request.user or obj.nurse == request.user