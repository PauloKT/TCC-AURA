from django.urls import path

from . import views

urlpatterns = [
    path("professor/", views.professor_overview, name="professor_overview"),
    path("aluno/", views.aluno_overview, name="aluno_overview"),
    path("subjects/new/", views.subject_create, name="subject_create"),
    path("classes/new/", views.classgroup_create, name="classgroup_create"),
    path("schedules/new/", views.schedule_create, name="schedule_create"),
    path("enrollments/new/", views.enrollment_create, name="enrollment_create"),
]

