# Teste do AURA pelo celular

## 1. Confirmar a coordenada da AEMS

A instituição foi cadastrada por migration com estes dados:

```text
AEMS
Av. Júlio Ferreira Xavier, 2750
Distrito Industrial
Três Lagoas - MS
Raio inicial: 100 metros
```

A geocodificação automática retornou resultados inconclusivos para esse endereço. Antes de liberar o teste, confirme a posição real da instituição:

1. No celular, abra o Google Maps ou outro mapa confiável.
2. Localize a entrada ou o ponto da AEMS em `Av. Júlio Ferreira Xavier, 2750`.
3. Mantenha o dedo sobre o ponto correto até aparecer o marcador.
4. Copie a latitude e a longitude exibidas.
5. Crie um superusuário local, caso ainda não exista:

```powershell
$python = 'd:\TCC-AURA\.venv-1\Scripts\python.exe'
Push-Location backend
& $python manage.py createsuperuser
Pop-Location
```

6. Faça login no sistema como administrador e obtenha um JWT, ou use a autenticação da API.
7. Confirme a coordenada:

```http
POST /api/instituicoes/1/confirmar-localizacao/
Authorization: Bearer <access-token-do-administrador>
Content-Type: application/json

{
  "latitude": -20.000000,
  "longitude": -51.000000,
  "source": "Google Maps - conferência manual"
}
```

Substitua os valores de exemplo pelas coordenadas reais. A instituição só fica disponível para novos professores depois dessa confirmação.

## 2. Teste na mesma rede Wi-Fi

Para testar apenas HTML, API e GPS, o celular pode acessar o computador pela rede local:

1. Conecte computador e celular à mesma rede Wi-Fi.
2. Descubra o IPv4 do computador com `ipconfig`.
3. Inicie o Django aceitando conexões externas:

```powershell
$python = 'd:\TCC-AURA\.venv-1\Scripts\python.exe'
Push-Location backend
& $python manage.py runserver 0.0.0.0:8000
Pop-Location
```

4. No celular, abra `http://<IP-DO-COMPUTADOR>:8000`.
5. Autorize localização no navegador.
6. Se o Windows Firewall perguntar, permita acesso na rede privada.

Atenção: muitos navegadores móveis bloqueiam geolocalização em HTTP quando o endereço é um IP. `localhost` é tratado de forma especial no próprio computador, mas não no celular.

## 3. Teste recomendado com HTTPS

Para geolocalização consistente e WebAuthn, use um túnel HTTPS temporário, como Cloudflare Tunnel ou ngrok:

```powershell
cloudflared tunnel --url http://localhost:8000
```

ou:

```powershell
ngrok http 8000
```

Abra no celular a URL `https://...` fornecida pelo túnel. Não publique tokens, senhas ou o arquivo `.env`.

WebAuthn exige contexto seguro e pode exigir configuração de `WEBAUTHN_RP_ID` e `WEBAUTHN_RP_ORIGIN` compatíveis com o domínio do túnel. Para o primeiro teste, valide login, GPS, QR Code e presença; depois valide WebAuthn com o domínio HTTPS definitivo.

## 4. Roteiro funcional

### Teste positivo

1. Confirme a coordenada da AEMS.
2. Cadastre um professor selecionando AEMS.
3. Cadastre um aluno.
4. Crie matéria, turma e aula.
5. Matricule o aluno na turma.
6. No computador ou em outro dispositivo, o professor inicia uma sessão.
7. O aluno abre o QR Code no celular.
8. Autoriza a localização.
9. Registra a presença dentro do raio.
10. Confirme no dashboard que a frequência foi atualizada.

### Teste negativo fora do raio

1. Mantenha a mesma sessão ativa.
2. Faça o teste em um ponto além do raio configurado.
3. A API deve responder `400`.
4. A presença não deve ser criada.
5. Volte para dentro do raio e repita; a nova tentativa deve poder funcionar.

### Outros casos

- Negar permissão de localização.
- Desativar o GPS.
- Usar uma instituição sem coordenada confirmada.
- Tentar acessar a sessão sem estar matriculado.
- Encerrar a sessão e tentar registrar depois.
- Aguardar a expiração do QR Code.

## 5. O que registrar para o TCC

Para cada teste, registre:

- Data e horário.
- Modelo do celular e navegador.
- Rede utilizada ou URL HTTPS do túnel.
- Latitude/longitude aproximadas do teste, sem expor dados pessoais desnecessários.
- Raio configurado.
- Resultado esperado.
- Resultado obtido.
- Captura de tela sem tokens, senhas ou informações pessoais.
