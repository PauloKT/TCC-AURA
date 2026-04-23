from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        PROFESSOR = "PROFESSOR", "Professor"
        ALUNO = "ALUNO", "Aluno"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ALUNO,
    )

    def is_professor(self) -> bool:
        return self.role == self.Role.PROFESSOR

    def is_aluno(self) -> bool:
        return self.role == self.Role.ALUNO
