from rest_framework import viewsets, permissions
from .models import Materia, Turma, Aula, TurmaAluno
from .serializers import (
    MateriaSerializer,
    TurmaSerializer,
    AulaSerializer,
    TurmaAlunoSerializer,
)
from django.shortcuts import get_object_or_404

class IsProfessorOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access to any user, but only professors can edit.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and user.is_authenticated and user.role == 'professor'

class IsProfessor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and user.is_authenticated and user.role == 'professor'

class MateriaViewSet(viewsets.ModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfessorOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'professor':
            # Professors can see all subjects (or only theirs)
            return Materia.objects.all()
        # Alunos can see all subjects (for enrollment)
        return Materia.objects.all()

    def perform_create(self, serializer):
        serializer.save(professor=self.request.user)

class TurmaViewSet(viewsets.ModelViewSet):
    queryset = Turma.objects.all()
    serializer_class = TurmaSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfessorOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'professor':
            return Turma.objects.filter(materia__professor=user)
        elif user.role == 'aluno':
            # Return turmas where the aluno is enrolled
            return Turma.objects.filter(turmaaluno__aluno=user)
        return Turma.objects.none()

    def perform_create(self, serializer):
        # Ensure the materia belongs to the professor
        serializer.save()

class AulaViewSet(viewsets.ModelViewSet):
    queryset = Aula.objects.all()
    serializer_class = AulaSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfessorOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'professor':
            return Aula.objects.filter(turma__materia__professor=user)
        elif user.role == 'aluno':
            return Aula.objects.filter(turma__turmaaluno__aluno=user)
        return Aula.objects.none()

    def perform_create(self, serializer):
        serializer.save()

class TurmaAlunoViewSet(viewsets.ModelViewSet):
    queryset = TurmaAluno.objects.all()
    serializer_class = TurmaAlunoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'professor':
            # Professors can see enrollments in their turmas
            return TurmaAluno.objects.filter(turma__materia__professor=user)
        elif user.role == 'aluno':
            # Alunos see their own enrollments
            return TurmaAluno.objects.filter(aluno=user)
        return TurmaAluno.objects.none()

    def perform_create(self, serializer):
        # Ensure the aluno is the requesting user if role is aluno
        if self.request.user.role == 'aluno':
            serializer.save(aluno=self.request.user)
        else:
            serializer.save()