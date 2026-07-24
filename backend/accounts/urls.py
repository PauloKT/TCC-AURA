from django.urls import path
from .views import RegisterView, CustomTokenObtainPairView, AlunoMinhaFrequenciaView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('aluno/minha-frequencia/', AlunoMinhaFrequenciaView.as_view(), name='aluno-minha-frequencia'),
]