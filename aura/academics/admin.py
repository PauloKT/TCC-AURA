from django.contrib import admin

from .models import ClassGroup, Enrollment, Schedule, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "professor")
    search_fields = ("code", "name", "professor__username", "professor__first_name", "professor__last_name")
    list_select_related = ("professor",)


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "professor")
    search_fields = ("subject__code", "subject__name", "name", "professor__username")
    list_select_related = ("subject", "professor")


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("class_group", "weekday", "start_time", "end_time")
    list_filter = ("weekday",)
    list_select_related = ("class_group",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("class_group", "student", "created_at")
    search_fields = ("class_group__subject__code", "class_group__name", "student__username")
    list_select_related = ("class_group", "student")
from django.contrib import admin

# Register your models here.
