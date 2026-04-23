from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from .forms import ClassGroupForm, EnrollmentForm, ScheduleForm, SubjectForm
from .models import ClassGroup, Enrollment, Subject


def _professor_required(request):
    if not getattr(request.user, "is_professor", None) or not request.user.is_professor():
        return False
    return True


@login_required
def professor_overview(request):
    if not _professor_required(request):
        return HttpResponseForbidden("Acesso restrito a professores.")

    subjects = Subject.objects.filter(professor=request.user).order_by("code")
    classes = ClassGroup.objects.filter(professor=request.user).select_related("subject").order_by("subject__code", "name")
    return render(
        request,
        "academics/professor_overview.html",
        {"subjects": subjects, "classes": classes},
    )


@login_required
def aluno_overview(request):
    enrollments = (
        Enrollment.objects.filter(student=request.user)
        .select_related("class_group__subject", "class_group__professor")
        .order_by("class_group__subject__code", "class_group__name")
    )
    return render(request, "academics/aluno_overview.html", {"enrollments": enrollments})


@login_required
def subject_create(request):
    if not _professor_required(request):
        return HttpResponseForbidden("Acesso restrito a professores.")

    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.professor = request.user
            subject.save()
            return redirect("professor_overview")
    else:
        form = SubjectForm()

    return render(request, "academics/form.html", {"form": form, "title": "Nova matéria"})


@login_required
def classgroup_create(request):
    if not _professor_required(request):
        return HttpResponseForbidden("Acesso restrito a professores.")

    if request.method == "POST":
        form = ClassGroupForm(request.POST, user=request.user)
        if form.is_valid():
            cg = form.save(commit=False)
            cg.professor = request.user
            cg.save()
            return redirect("professor_overview")
    else:
        form = ClassGroupForm(user=request.user)

    return render(request, "academics/form.html", {"form": form, "title": "Nova turma"})


@login_required
def schedule_create(request):
    if not _professor_required(request):
        return HttpResponseForbidden("Acesso restrito a professores.")

    if request.method == "POST":
        form = ScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("professor_overview")
    else:
        form = ScheduleForm(user=request.user)

    return render(request, "academics/form.html", {"form": form, "title": "Novo horário"})


@login_required
def enrollment_create(request):
    if not _professor_required(request):
        return HttpResponseForbidden("Acesso restrito a professores.")

    if request.method == "POST":
        form = EnrollmentForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("professor_overview")
    else:
        form = EnrollmentForm(user=request.user)

    return render(request, "academics/form.html", {"form": form, "title": "Matricular aluno"})

from django.shortcuts import render

# Create your views here.
