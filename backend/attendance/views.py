from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import SessaoChamada, Presenca
from .serializers import SessaoChamadaSerializer, SessaoTokenSerializer, PresencaSerializer, PresencaCreateSerializer
from courses.models import Aula
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from courses.models import TurmaAluno
from .geolocation import validate_coordinates, validate_radius

User = get_user_model()

class IsProfessor(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'professor'

class IsAluno(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'aluno'


class CanViewSessionToken(IsAuthenticated):
    """Permite token ao professor responsável ou a aluno matriculado."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'professor':
            return obj.aula.turma.materia.professor_id == request.user.id
        return TurmaAluno.objects.filter(
            turma=obj.aula.turma,
            aluno=request.user,
        ).exists()

class SessaoChamadaViewSet(viewsets.ModelViewSet):
    queryset = SessaoChamada.objects.all()
    serializer_class = SessaoChamadaSerializer
    permission_classes = [IsProfessor]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'professor':
            return (
                SessaoChamada.objects
                .filter(aula__turma__materia__professor=user)
                .select_related('aula', 'aula__turma', 'aula__turma__materia')
            )
        if user.role == 'aluno' and self.action == 'token':
            return (
                SessaoChamada.objects
                .filter(aula__turma__alunos__aluno=user)
                .select_related('aula', 'aula__turma', 'aula__turma__materia')
            )
        return SessaoChamada.objects.none()

    def get_permissions(self):
        if self.action == 'token':
            return [CanViewSessionToken()]
        return super().get_permissions()

    def perform_create(self, serializer):
        # Garante que a aula pertence a uma materia do professor.
        aula_id = self.request.data.get('aula')
        if not aula_id:
            raise ValidationError({'aula': 'Campo "aula" é obrigatório.'})
        aula = get_object_or_404(
            Aula.objects.select_related('turma', 'turma__materia'),
            id=aula_id,
            turma__materia__professor=self.request.user,
        )

        professor = self.request.user
        instituicao = professor.instituicoes.filter(ativa=True).first() or professor.instituicao
        if instituicao:
            lat = instituicao.latitude
            lng = instituicao.longitude
            radius_value = instituicao.radius_meters
        else:
            # Compatibilidade temporária com professores criados antes do cadastro de instituições.
            lat = professor.latitude
            lng = professor.longitude
            radius_value = professor.radius_meters

        if lat is None or lng is None:
            raise ValidationError({
                'detail': 'A instituição precisa ter uma localização confirmada antes de iniciar a sessão.'
            })
        try:
            lat, lng = validate_coordinates(lat, lng)
            radius = validate_radius(radius_value)
        except ValueError as exc:
            raise ValidationError({'detail': str(exc)}) from exc

        serializer.save(
            aula=aula,
            professor_latitude=lat,
            professor_longitude=lng,
            professor_radius_meters=radius,
        )

    @action(detail=True, methods=['get'], url_path='token')
    def token(self, request, pk=None):
        """
        GET /api/sessoes/{id}/token/
        Returns current token, expiration, seconds remaining, and professor location.
        """
        sessao = self.get_object()
        # If token expired or not active, refresh automatically
        if request.user.role == 'professor' and not sessao.is_token_valid():
            sessao.refresh_token()
        serializer = SessaoTokenSerializer(sessao)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='encerrar')
    def encerrar(self, request, pk=None):
        """
        POST /api/sessoes/{id}/encerrar/
        Ends the session.
        """
        sessao = self.get_object()
        if not sessao.ativa:
            return Response({'detail': 'Sessão já está encerrada.'}, status=status.BAD_REQUEST)
        sessao.ativa = False
        sessao.encerrada_em = timezone.now()
        sessao.save(update_fields=['ativa', 'encerrada_em'])
        return Response({'detail': 'Sessão encerrada com sucesso.'}, status=status.OK)

class PresencaCreateView(viewsets.GenericViewSet):
    """
    POST /api/presenca/registrar/
    Expects: sessao_id, token, latitude, longitude
    """
    serializer_class = PresencaCreateSerializer
    permission_classes = [IsAluno]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        presenca = serializer.save()
        return Response({
            'detail': 'Presença registrada com sucesso.',
            'presenca': PresencaSerializer(presenca).data
        }, status=status.HTTP_201_CREATED)