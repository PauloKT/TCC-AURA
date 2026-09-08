from math import isfinite

from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Instituicao, Materia, Turma, Aula, TurmaAluno
from .geocoding import geocode_address
from .serializers import (
    MateriaSerializer,
    TurmaSerializer,
    AulaSerializer,
    TurmaAlunoSerializer,
    InstituicaoSerializer,
)
from django.shortcuts import get_object_or_404


class InstituicaoViewSet(viewsets.ReadOnlyModelViewSet):
    """Lista instituições ativas e permite geocodificação administrativa."""

    queryset = Instituicao.objects.filter(ativa=True)
    serializer_class = InstituicaoSerializer
    permission_classes = [permissions.AllowAny]

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAdminUser],
        url_path='geocodificar',
    )
    def geocodificar(self, request, pk=None):
        instituicao = self.get_object()
        return Response({
            'instituicao': instituicao.nome,
            'endereco': instituicao.endereco_completo,
            'candidatos': geocode_address(instituicao.endereco_completo),
        })

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAdminUser],
        url_path='confirmar-localizacao',
    )
    def confirmar_localizacao(self, request, pk=None):
        """Confirma manualmente a coordenada oficial após conferência."""
        instituicao = self.get_object()
        try:
            latitude = float(request.data['latitude'])
            longitude = float(request.data['longitude'])
        except (KeyError, TypeError, ValueError):
            return Response(
                {'detail': 'Latitude e longitude são obrigatórias e numéricas.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not isfinite(latitude)
            or not isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            return Response(
                {'detail': 'Latitude deve estar entre -90 e 90; longitude entre -180 e 180.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instituicao.latitude = latitude
        instituicao.longitude = longitude
        instituicao.geocodificada_em = timezone.now()
        instituicao.geocoding_source = request.data.get('source', 'confirmacao_manual')[:100]
        instituicao.save(update_fields=[
            'latitude', 'longitude', 'geocodificada_em', 'geocoding_source',
        ])
        return Response(InstituicaoSerializer(instituicao).data)

class IsProfessorOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access to any user, but only professors can edit.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.role == 'professor'

class IsProfessor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'professor'

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