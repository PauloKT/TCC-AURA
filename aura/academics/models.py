from django.conf import settings
from django.db import models


class Subject(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="subjects",
        limit_choices_to={"role": "PROFESSOR"},
    )

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class ClassGroup(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="classes")
    name = models.CharField(max_length=80, help_text="Ex.: Turma A / 2026.1")
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="classes",
        limit_choices_to={"role": "PROFESSOR"},
    )

    class Meta:
        unique_together = (("subject", "name"),)

    def __str__(self) -> str:
        return f"{self.subject.code} / {self.name}"


class Schedule(models.Model):
    class Weekday(models.IntegerChoices):
        SEG = 1, "Segunda"
        TER = 2, "Terça"
        QUA = 3, "Quarta"
        QUI = 4, "Quinta"
        SEX = 5, "Sexta"
        SAB = 6, "Sábado"
        DOM = 7, "Domingo"

    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE, related_name="schedules")
    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ("weekday", "start_time")

    def __str__(self) -> str:
        return f"{self.class_group} — {self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"


class Enrollment(models.Model):
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        limit_choices_to={"role": "ALUNO"},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("class_group", "student"),)

    def __str__(self) -> str:
        return f"{self.student.username} em {self.class_group}"
