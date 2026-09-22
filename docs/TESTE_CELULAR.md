# Testar chamada pelo celular

Revisado em **17/09/2026**. Professor e aluno devem usar o mesmo endereço HTTPS. No teste local, o banco continua no computador que executa Django.

## Preparar o computador ou notebook

1. Em uma máquina nova, crie um ambiente virtual e instale `requirements.txt`, seguindo o README. Não copie `.venv` da outra máquina.
2. Configure `.env` com `DEBUG=True`. No diretório `backend`, execute `python manage.py prepare_local`: backup do SQLite existente e aplicação de migrations. Isso deve ser conferido em cada instalação.
3. Inicie `python manage.py runserver 127.0.0.1:8000`.
4. Em outro terminal, execute o túnel:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Se não estiver no PATH, use o local em que foi instalado. Exemplo:

```powershell
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url "http://127.0.0.1:8000"
```

O argumento é somente a URL: não copie colchetes nem sintaxe de link Markdown. Se o serviço responder com erro 409, tente novamente mais tarde; esse erro de provisionamento ocorre antes de o túnel alcançar o Django.

5. Adicione o hostname retornado (sem `https://`) a `ALLOWED_HOSTS`. Para acessar o admin pelo túnel, adicione a URL HTTPS completa a `CSRF_TRUSTED_ORIGINS`. Reinicie o Django.
6. Abra o endereço HTTPS no computador e no celular; mantenha servidor e túnel ligados. A rede da faculdade precisa permitir acesso ao domínio. O celular pode usar outra rede com internet.
7. Encerre servidor e túnel após o ensaio: o túnel torna o servidor de desenvolvimento acessível pela internet.

Se o professor abrir em `localhost` ou `127.0.0.1`, o QR apontará para o próprio celular. Por isso ele também precisa abrir o endereço HTTPS. GPS em celular requer contexto seguro, normalmente HTTPS.

## Professor

Se a instituição ainda não existir, no cadastro escolha **Sou professor → Adicionar nova instituição** e preencha o endereço do campus. Antes do ensaio, um administrador deve entrar em `/admin/courses/instituicao/`, abrir a instituição cadastrada, conferir as coordenadas e salvar latitude, longitude e raio. Sem essa confirmação, iniciar chamada continua bloqueado.

1. Entre pelo endereço HTTPS com uma conta de professor vinculada à instituição do teste.
2. Crie ou selecione matéria, turma e aula.
3. Mostre ao aluno o **código de 8 caracteres da turma**.
4. Inicie a chamada e mantenha o QR visível. Seu token dura 30 segundos e é renovado pelas consultas do painel.
5. Acompanhe os resultados abaixo do QR: nome, presente/falta, horário e quantidade aguardando.
6. Encerre a chamada ao terminar.

## Aluno

1. Faça login no mesmo endereço HTTPS, usando o navegador que será aberto pela câmera.
2. Selecione **Entrar em uma turma**, digite o código e confirme a matrícula.
3. O painel consulta chamadas disponíveis a cada cinco segundos enquanto está visível.
4. Leia o QR com a câmera e abra o link no mesmo navegador. Se abrir um navegador interno sem login, autentique-se; pode ser necessário ler o QR atual novamente.
5. Permita a localização e aguarde o resultado: presença dentro do raio ou **falta registrada** fora dele.

Se negar GPS ou houver erro de captura, nada é registrado: corrija a permissão e tente novamente. Uma leitura validada pelo servidor dá 120 segundos para concluir GPS; depois disso, leia o QR atual. A chamada deve continuar aberta.

Depois de registrado, o primeiro resultado fica mantido. Aproximar-se após registrar falta e ler novamente não transforma a falta em presença. Para ensaiar outro cenário, crie uma chamada de teste separada.

## Conferir a localização

O raio é medido da coordenada institucional salva na abertura da sessão, não da posição do notebook. A migration já preenche coordenadas da AEMS; confira no admin se correspondem ao campus e se o raio atende à sala usada.

Em casa, uma chamada da AEMS deve registrar falta por distância. Para testar em outro local, use uma instituição de teste com coordenadas reais desse local. Professores com várias instituições ainda não escolhem o campus ao iniciar a aula; confira qual foi usado.

## Roteiro de aceite

- [ ] Professor cria matéria, turma e aula; seleções e código correspondem à turma correta.
- [ ] Aluno entra por código; aluno de fora da turma não confirma presença.
- [ ] GPS dentro do raio registra presente e aparece no painel do professor.
- [ ] GPS fora do raio registra falta e aparece no painel do professor.
- [ ] Negar GPS ou perder conexão não mostra falso sucesso nem falta automática.
- [ ] QR vencido pede nova leitura; rotação após leitura válida preserva o prazo do comprovante.
- [ ] Encerrar antes do processamento do registro impede a gravação. Em envios próximos ao encerramento, a ordem é definida pelo bloqueio no banco, não pela ordem visual dos cliques.
- [ ] Repetir envio não duplica nem altera o primeiro resultado.
- [ ] Conferir frequência e CSV manualmente com uma turma de dados conhecidos.
- [ ] Testar Android/iPhone disponíveis, menu, formulários e páginas em tela pequena.
- [ ] Registrar data, dispositivo, navegador, rede, cenário e resultado real de cada ensaio.

O usuário já relatou teste de falta fora do raio. Ainda é necessário documentar o sucesso dentro do raio e os demais casos. A imagem do QR depende de `api.qrserver.com`; os avisos não funcionam como push com navegador fechado.

## Ensaio de chamadas simultâneas

Use uma turma de teste, pois iniciar novas sessões influencia a frequência.

1. Abra o painel do mesmo professor em duas abas. Selecione a mesma aula e inicie nas duas: ambas devem usar a mesma sessão ativa.
2. Mantenha as duas abas abertas durante a troca do QR. Depois da renovação, ambas devem convergir para o mesmo token; o instante da atualização visual depende das consultas de cada aba.
3. Com alunos diferentes matriculados, leia o QR e confirme a localização em horários próximos. Confira um registro por aluno e os respectivos resultados.
4. Encerre a chamada em uma aba. A outra deve reconhecer o encerramento na próxima consulta, retirar o QR e manter os resultados finais.
5. Repita o envio de um aluno enquanto a sessão estiver aberta e o comprovante válido: o resultado original deve ser mantido, sem duplicação. Depois do encerramento, novos envios são rejeitados.
6. Encerre próximo ao envio de um aluno. Se o registro obtiver o bloqueio primeiro e passar nas validações, ele será salvo antes do encerramento; se o encerramento vencer, não haverá novo registro.
7. Troque rapidamente matéria, turma e aula durante carregamentos. Uma resposta antiga não deve substituir a seleção atual nem trazer de volta o QR anterior.

Esses cenários têm cobertura automatizada local, mas o ensaio acima ainda precisa ser registrado com aparelhos reais. Para PostgreSQL e comandos de testes, consulte [Guia técnico](GUIA_TECNICO.md) e [Hospedagem](HOSPEDAGEM.md).
