const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function harness(file, fetch, initial = {}) {
  const elements = new Map();
  const events = {};
  const intervals = new Map();
  const timers = new Map();
  const storage = new Map(Object.entries({ access_token: 'x.' + Buffer.from('{"role":"professor"}').toString('base64') + '.y', ...initial }));
  let locate;
  let sequence = 0;
  function makeElement() {
    return { style: {}, dataset: {}, disabled: true, hidden: false, textContent: '', value: '', children: [],
      selectedOptions: [{ textContent: 'Test' }], classList: { add() {}, remove() {} }, listeners: {},
      addEventListener(event, callback) { this.listeners[event] = callback; },
      dispatchEvent(event) { return this.listeners[event.type]?.call(this, event); },
      removeAttribute(name) { delete this[name]; },
      setAttribute(name, value) { this[name] = value; },
      getAttribute(name) { return this[name]; },
      focus() { this.focused = true; },
      reset() {}, showModal() { this.open = true; }, close() { this.open = false; },
      append(...items) { this.children.push(...items); }, appendChild(item) { this.children.push(item); },
      replaceChildren(...items) { this.children = items; }, querySelectorAll() { return []; }, querySelector() { return null; }
    };
  }
  const element = id => { if (!elements.has(id)) elements.set(id, makeElement()); return elements.get(id); };
  const context = {
    document: { body: { dataset: {} }, hidden: false, getElementById: element, querySelectorAll() { return []; }, querySelector: element, addEventListener(event, callback) { events[event] = callback; }, createElement: makeElement },
    window: { isSecureContext: true, location: { hash: '', pathname: '/confirmar-presenca.html', search: '?sessaoId=1&token=old', origin: 'https://aura.test' }, addEventListener() {}, dispatchEvent() {} },
    localStorage: { getItem: key => storage.get(key) || null, setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key) },
    navigator: { geolocation: { getCurrentPosition(success, error) { locate = { success, error }; } } },
    URL, URLSearchParams, Date, console, fetch, Event: class Event { constructor(type) { this.type = type; } }, alert() {},
    atob: value => Buffer.from(value, 'base64').toString(),
    setTimeout(callback) { const id = ++sequence; timers.set(id, callback); return id; }, clearTimeout(id) { timers.delete(id); },
    setInterval(callback) { const id = ++sequence; intervals.set(id, callback); return id; }, clearInterval(id) { intervals.delete(id); }
  };
  vm.createContext(context);
  context.location = context.window.location;
  vm.runInContext(fs.readFileSync(path.join(__dirname, 'api.js'), 'utf8'), context);
  context.Aura = context.window.Aura;
  if (file.includes('workspace')) {
    vm.runInContext(fs.readFileSync(path.join(__dirname, 'ui.js'), 'utf8'), context);
    context.UI = context.window.UI;
  }
  vm.runInContext(fs.readFileSync(path.join(__dirname, file), 'utf8'), context);
  const ready = events.DOMContentLoaded();
  return { element, events, get locate() { return locate; }, intervals, timers, context, storage, ready };
}
const flush = () => new Promise(resolve => setImmediate(resolve));
const response = (data, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => data });
const prepared = { comprovante: 'signed', turma: 'Turma A', aula: 'Aula 1' };

function deferred() {
  let resolve, reject;
  const promise = new Promise((accept, fail) => { resolve = accept; reject = fail; });
  return {promise, resolve, reject};
}
const activeSession = (id, token = `session-${id}`) => ({id, token_atual: token, token_expira_em: new Date(Date.now() + 30000).toISOString(), professor_radius_meters: 100});
function chooseLesson(ui, id) {
  ui.element('aula-select').value = String(id);
  ui.element('aula-select').dispatchEvent({type:'change'});
}
function callHarness(fetchSession) {
  return harness('professor.js', (url, options) => {
    if (url === '/api/materias/') return Promise.resolve(response([]));
    return fetchSession(url, options);
  });
}

test('início duplicado é bloqueado e resposta antiga não altera a nova aula', async () => {
  const first = deferred(), second = deferred();
  let starts = 0;
  const ui = callHarness(async url => {
    if (url === '/api/sessoes/') return ++starts === 1 ? first.promise : second.promise;
    if (url.endsWith('/resultados/')) return response({ativa:true,resultados:[]});
    throw new Error(url);
  });
  chooseLesson(ui, 3);
  const firstClick = ui.element('start-session-btn').dispatchEvent({type:'click'});
  await ui.element('start-session-btn').dispatchEvent({type:'click'});
  assert.equal(starts, 1);
  chooseLesson(ui, 4);
  const secondClick = ui.element('start-session-btn').dispatchEvent({type:'click'});
  first.resolve(response(activeSession(9)));
  await firstClick;
  assert.equal(ui.element('start-session-btn').disabled, true);
  assert.equal(ui.element('qr-code-img').src, undefined);
  second.resolve(response(activeSession(10)));
  await secondClick;
  assert.equal(starts, 2);
  assert.match(decodeURIComponent(ui.element('qr-code-img').src), /sessaoId=10/);
  assert.equal(ui.element('call-state').textContent, 'Chamada aberta');
});

test('renovação automática e cliques simultâneos compartilham uma única consulta QR', async () => {
  const renewal = deferred();
  let renewals = 0;
  const ui = callHarness(async url => {
    if (url === '/api/sessoes/') return response({...activeSession(9),token_expira_em:new Date(Date.now() - 1000).toISOString()});
    if (url.endsWith('/resultados/')) return response({ativa:true,resultados:[]});
    if (url.endsWith('/token/')) { renewals++; return renewal.promise; }
    throw new Error(url);
  });
  chooseLesson(ui, 3);
  await ui.element('start-session-btn').dispatchEvent({type:'click'});
  ui.element('refresh-results-btn').dispatchEvent({type:'click'});
  ui.element('refresh-results-btn').dispatchEvent({type:'click'});
  assert.equal(renewals, 1);
  renewal.resolve(response(activeSession(9,'renewed')));
  await flush();
  assert.match(decodeURIComponent(ui.element('qr-code-img').src), /token=renewed/);
  assert.equal(ui.intervals.size, 1);
});

test('QR atrasado não substitui o QR da mesma sessão retomada', async () => {
  const renewal = deferred();
  let starts = 0;
  const ui = callHarness(async url => {
    if (url === '/api/sessoes/') return response(activeSession(9,++starts === 1 ? 'initial' : 'current'));
    if (url.endsWith('/resultados/')) return response({ativa:true,resultados:[]});
    if (url.endsWith('/token/')) return renewal.promise;
    throw new Error(url);
  });
  chooseLesson(ui, 3);
  await ui.element('start-session-btn').dispatchEvent({type:'click'});
  ui.element('refresh-results-btn').dispatchEvent({type:'click'});
  chooseLesson(ui, 4);
  chooseLesson(ui, 3);
  await ui.element('start-session-btn').dispatchEvent({type:'click'});
  renewal.resolve(response(activeSession(9,'stale')));
  await flush();
  assert.match(decodeURIComponent(ui.element('qr-code-img').src), /token=current/);
  assert.equal(ui.intervals.size, 1);
});

test('encerramento duplicado é bloqueado e retorno antigo preserva a nova chamada', async () => {
  const closure = deferred();
  let starts = 0, closes = 0;
  const ui = callHarness(async url => {
    if (url === '/api/sessoes/') return response(activeSession(++starts));
    if (url.endsWith('/resultados/')) return response({ativa:true,resultados:[]});
    if (url.endsWith('/encerrar/')) { closes++; return closure.promise; }
    throw new Error(url);
  });
  chooseLesson(ui, 3);
  await ui.element('start-session-btn').dispatchEvent({type:'click'});
  const firstClose = ui.element('end-session-btn').dispatchEvent({type:'click'});
  await ui.element('end-session-btn').dispatchEvent({type:'click'});
  assert.equal(closes, 1);
  chooseLesson(ui, 4);
  await ui.element('start-session-btn').dispatchEvent({type:'click'});
  closure.resolve(response({}));
  await firstClose;
  assert.match(decodeURIComponent(ui.element('qr-code-img').src), /sessaoId=2/);
  assert.equal(ui.element('call-state').textContent, 'Chamada aberta');
  assert.equal(ui.element('end-session-btn').hidden, false);
  assert.equal(ui.intervals.size, 1);
});

test('encerramento por outra tela retira QR mesmo com renovação pendente', async () => {
  const renewal = deferred(), poll = deferred();
  let polls = 0;
  const ui = callHarness(async url => {
    if (url === '/api/sessoes/') return response(activeSession(9));
    if (url.endsWith('/resultados/')) return ++polls === 1 ? response({ativa:true,resultados:[]}) : poll.promise;
    if (url.endsWith('/token/')) return renewal.promise;
    throw new Error(url);
  });
  chooseLesson(ui, 3);
  await ui.element('start-session-btn').dispatchEvent({type:'click'});
  await flush();
  ui.element('refresh-results-btn').dispatchEvent({type:'click'});
  poll.resolve(response({ativa:false,encerrada_em:new Date().toISOString(),resultados:[{aluno:'Aluno1',status:'presente'}],aguardando:0}));
  await flush();
  renewal.resolve(response(activeSession(9,'late')));
  await flush();
  assert.equal(ui.element('call-state').textContent, 'Chamada encerrada');
  assert.equal(ui.element('qr-code-img').src, undefined);
  assert.equal(ui.element('qr-code-container').style.display, 'none');
  assert.equal(ui.element('attendance-list').children[0].textContent, 'Aluno1 - Presente');
  assert.equal(ui.element('attendance-results').hidden, false);
  assert.equal(ui.intervals.size, 0);
  assert.equal(ui.timers.size, 0);
});

test('resposta de resultados fora de ordem não reabre uma chamada encerrada', async () => {
  const stale = deferred(), latest = deferred();
  let polls = 0;
  const ui = callHarness(async url => {
    if (url === '/api/sessoes/') return response(activeSession(9));
    if (url.endsWith('/resultados/')) return ++polls === 1 ? stale.promise : latest.promise;
    if (url.endsWith('/token/')) return response(activeSession(9));
    throw new Error(url);
  });
  chooseLesson(ui, 3);
  await ui.element('start-session-btn').dispatchEvent({type:'click'});
  ui.element('refresh-results-btn').dispatchEvent({type:'click'});
  latest.resolve(response({ativa:false,resultados:[{aluno:'Aluno2',status:'falta'}]}));
  await flush();
  stale.resolve(response({ativa:true,resultados:[]}));
  await flush();
  assert.equal(ui.element('call-state').textContent, 'Chamada encerrada');
  assert.equal(ui.element('attendance-list').children[0].textContent, 'Aluno2 - Falta');
  assert.equal(ui.intervals.size, 0);
  assert.equal(ui.timers.size, 0);
});

test('encerramento já realizado em outra tela consulta o estado final após erro 400', async () => {
  let closed = false, renewals = 0;
  const ui = callHarness(async url => {
    if (url === '/api/sessoes/') return response(activeSession(9));
    if (url.endsWith('/resultados/')) return response({ativa:!closed,resultados:[]});
    if (url.endsWith('/encerrar/')) { closed = true; return response({detail:'Sessão já encerrada.'},400); }
    if (url.endsWith('/token/')) { renewals++; return response(activeSession(9)); }
    throw new Error(url);
  });
  chooseLesson(ui, 3);
  await ui.element('start-session-btn').dispatchEvent({type:'click'});
  await flush();
  await ui.element('end-session-btn').dispatchEvent({type:'click'});
  assert.equal(ui.element('call-state').textContent, 'Chamada encerrada');
  assert.equal(ui.element('start-session-btn').disabled, false);
  assert.equal(ui.element('end-session-btn').hidden, true);
  assert.equal(renewals, 0);
});

test('menu superior abre, fecha por Escape e fecha ao clicar fora', async () => {
  const ui = harness('ui.js', async () => { throw new Error('Não deve consultar API'); });
  await ui.ready;
  const toggle = ui.element('menu-toggle');
  const menu = ui.element('navigation-menu');
  toggle.setAttribute('aria-expanded','false'); menu.hidden = true;
  toggle.listeners.click({currentTarget:toggle});
  assert.equal(menu.hidden,false);
  assert.equal(toggle.getAttribute('aria-expanded'),'true');
  ui.events.keydown({key:'Escape'});
  assert.equal(menu.hidden,true);
  assert.equal(toggle.focused,true);
  toggle.listeners.click({currentTarget:toggle});
  ui.events.click({target:{closest:()=>null}});
  assert.equal(menu.hidden,true);
  assert.equal(toggle.getAttribute('aria-expanded'),'false');
});

test('selecionar uma aula carrega matéria, turma e código corretos', async () => {
  const ui = harness('professor.js', async url => {
    if (url === '/api/materias/') return response([{id:1,nome:'POO',codigo:'POO'}]);
    if (url === '/api/turmas/?materia=1') return response([{id:2,nome:'TADS',semestre:'2',ano:2026,codigo_acesso:'AB2CD3EF'}]);
    if (url === '/api/aulas/?turma=2') return response([{id:3,titulo:'Objetos',data:'2026-09-16',hora_inicio:'08:00',hora_fim:'10:00'}]);
    throw new Error(url);
  });
  await flush();
  await ui.context.window.AuraCall.select(1,2,3);
  assert.equal(ui.element('session-section').style.display, 'block');
  assert.equal(ui.element('aula-select').value,'3');
  assert.equal(ui.element('invite-code').value,'AB2CD3EF');
  assert.match(ui.element('call-title').textContent,/Objetos/);
});

test('painel vazio oferece ações e erro de formulário permanece no diálogo', async () => {
  const empty = {materias:[],turmas:[],aulas:[],frequencias:[],recentes:[],sessoes:[]};
  const ui = harness('workspace.js', async (url, options) => {
    if (url === '/api/interface/painel/') return response(empty);
    if (url === '/api/materias/' && options.method === 'POST') return response({codigo:['Este código já existe.']},400);
    throw new Error(url);
  });
  await flush();
  assert.match(ui.element('subject-list').innerHTML,/Criar matéria/);
  await ui.events.click({target:{closest:()=>({dataset:{new:'materia'},hasAttribute:()=>false})}});
  ui.element('materia-nome').value='POO'; ui.element('materia-codigo').value='POO';
  ui.element('materia-carga').value='60'; ui.element('materia-freq').value='75';
  await ui.element('materia-form').listeners.submit({preventDefault(){}});
  assert.match(ui.element('materia-error').textContent,/Código: Este código já existe/);
  assert.equal(ui.element('materia-dialog').open,true);
  assert.equal(ui.element('create-materia-btn').disabled,false);
});

test('painel calcula indicadores reais e escapa nomes nos cards', async () => {
  const ui = harness('workspace.js', async () => response({materias:[{id:1,nome:'<img src=x onerror=alert(1)>',codigo:'POO',carga_horaria:60,frequencia_minima:75}],turmas:[],aulas:[],frequencias:[],recentes:[],sessoes:[]}));
  await flush();
  assert.match(ui.element('subject-list').innerHTML,/&lt;img/);
  assert.doesNotMatch(ui.element('subject-list').innerHTML,/<img/);
  assert.match(ui.element('dashboard-stats').innerHTML,/Alunos em atenção/);
});

test('professor renova login expirado e carrega as matérias para seleção', async () => {
  const ui = harness('professor.js', async (url, options) => {
    if (url === '/api/token/refresh/') return response({ access: 'renovado' });
    assert.equal(url, '/api/materias/');
    if (options.headers.Authorization !== 'Bearer renovado') return response({}, 401);
    return response([{ id: 3, nome: 'PTeste', codigo: 'PT' }]);
  }, { refresh_token: 'refresh' });
  await flush();
  assert.equal(ui.storage.get('access_token'), 'renovado');
  assert.equal(ui.element('materia-select').children.length, 2);
  assert.equal(ui.element('materia-select').children[1].value, 3);
});

test('professor sem matérias recebe indicação de vínculo vazio', async () => {
  const ui = harness('professor.js', async () => response([]));
  await flush();
  assert.match(ui.element('materia-select').children[0].textContent, /Nenhuma matéria vinculada/);
});

test('QR válido e GPS confirmam automaticamente uma única vez', async () => {
  const calls = [];
  const ui = harness('confirmar-presenca.js', async (url, options) => {
    calls.push([url, options]);
    return response(url.endsWith('preparar/') ? prepared : { presenca: { valida: true } });
  });
  await flush();
  ui.locate.success({ coords: { latitude: 0, longitude: 0 } });
  await ui.ready;
  assert.match(ui.element('success-message').textContent, /confirmada com sucesso/);
  assert.equal(calls.length, 2);
  assert.equal(JSON.parse(calls[1][1].body).comprovante, 'signed');
  await ui.element('confirm-btn').listeners.click();
  assert.equal(calls.length, 2);
});

test('GPS negado permite tentar novamente sem confirmar presença', async () => {
  let writes = 0;
  const ui = harness('confirmar-presenca.js', async url => {
    if (url.endsWith('registrar/')) writes++;
    return response(prepared);
  });
  await flush();
  ui.locate.error({ code: 1 });
  await ui.ready;
  assert.match(ui.element('error-message').textContent, /Permita/);
  assert.equal(ui.element('confirm-btn').disabled, false);
  assert.equal(writes, 0);
});

test('fora do raio exibe erro e nunca mostra sucesso', async () => {
  const ui = harness('confirmar-presenca.js', async url => response(
    url.endsWith('preparar/') ? prepared : { detail: 'Você está fora do raio permitido.' }, url.endsWith('preparar/') ? 200 : 400));
  await flush();
  ui.locate.success({ coords: { latitude: 10, longitude: 10 } });
  await ui.ready;
  assert.match(ui.element('error-message').textContent, /fora do raio/);
  assert.equal(ui.element('success-message').textContent, '');
});

test('falta registrada conclui o fluxo sem oferecer reenvio', async () => {
  const ui = harness('confirmar-presenca.js', async url => response(
    url.endsWith('preparar/') ? prepared : { presenca: { valida: false }, detail: 'Falta registrada: fora do raio.' }));
  await flush();
  ui.locate.success({ coords: { latitude: 10, longitude: 10 } });
  await ui.ready;
  assert.equal(ui.element('flow-status').textContent, 'Falta registrada.');
  assert.equal(ui.element('confirm-btn').hidden, true);
  assert.equal(ui.element('back-link').hidden, false);
  assert.equal(ui.element('success-message').textContent, '');
});

test('aluno sem login é encaminhado para autenticação antes de obter GPS', async () => {
  const ui = harness('confirmar-presenca.js', () => { throw new Error('Não deve consultar API'); }, { access_token: null });
  await ui.ready;
  assert.match(ui.context.window.location.href, /^\/login.html\?next=/);
  assert.equal(ui.locate, undefined);
});

test('login volta ao endereço interno solicitado e bloqueia redirecionamento externo', async () => {
  for (const next of ['/aluno.html?convite=abc', 'https://evil.test/aluno.html']) {
    const ui = harness('login.js', async () => response({ access: 'x.' + Buffer.from('{"role":"aluno"}').toString('base64') + '.y', refresh: 'refresh', user: { role: 'aluno' } }));
    ui.context.window.location.search = '?next=' + encodeURIComponent(next);
    ui.element('username').value = 'aluno'; ui.element('password').value = 'senha';
    await ui.element('login-form').listeners.submit({ preventDefault() {} });
    assert.equal(ui.context.window.location.href, next.startsWith('/') ? next : 'aluno.html');
  }
});

test('painel avisa chamada iniciada e remove aviso após confirmação', async () => {
  let active = [];
  const ui = harness('aluno.js', async url => response(url.includes('turmas') ? { turmas: [] } : { chamadas: active }));
  await flush();
  active = [{ id: 1, turma: 'A', materia: 'Matemática', aula: 'Aula 1' }];
  await [...ui.timers.values()][0]();
  assert.equal(ui.element('calls-list').children.length, 1);
  assert.match(ui.element('calls-list').children[0].children[0].textContent, /Chamada iniciada/);
  active = [];
  await [...ui.timers.values()][0]();
  assert.equal(ui.element('calls-list').children.length, 0);
});

test('entrada por código envia o código da turma em maiúsculas', async () => {
  let joined;
  const ui = harness('aluno.js', async (url, options) => {
    if (url.includes('entrar-turma')) { joined = JSON.parse(options.body); return response({ detail: 'Matriculado com sucesso.' }); }
    return response(url.includes('turmas') ? { turmas: [] } : { chamadas: [] });
  });
  await flush();
  ui.element('invite-code').value = ' ab2cd3ef ';
  await ui.element('join-form').listeners.submit({ preventDefault() {} });
  assert.equal(joined.codigo_acesso, 'AB2CD3EF');
  assert.match(ui.element('join-message').textContent, /Matriculado/);
});

test('QR expirado renova token sem criar outra sessão e permite encerrar', async () => {
  const calls = [];
  const ui = harness('professor.js', async (url, options) => {
    calls.push([url, options]);
    if (url.endsWith('materias/')) return response([]);
    if (url.endsWith('resultados/')) return response({ resultados: [{ aluno: 'Aluno1', status: 'presente' }, { aluno: 'Aluno2', status: 'falta' }] });
    if (url.endsWith('encerrar/')) return response({});
    if (url.endsWith('sessoes/')) return response({ id: 9, token_atual: 'old', token_expira_em: new Date(Date.now() - 1000).toISOString() });
    if (url.endsWith('9/token/')) return response({ token_atual: 'new', token_expira_em: new Date(Date.now() + 30000).toISOString() });
    throw new Error(url);
  });
  ui.element('aula-select').value = '3';
  ui.element('aula-select').listeners.change.call(ui.element('aula-select'));
  await ui.element('start-session-btn').listeners.click();
  await flush();
  assert.equal(calls.filter(([url]) => url.endsWith('sessoes/')).length, 1);
  assert.match(decodeURIComponent(ui.element('qr-code-img').src), /token=new/);
  assert.equal(ui.intervals.size, 1);
  assert.equal(ui.element('attendance-list').children[0].textContent, 'Aluno1 - Presente');
  assert.equal(ui.element('attendance-list').children[1].textContent, 'Aluno2 - Falta');
  await ui.element('end-session-btn').listeners.click();
  assert.equal(ui.intervals.size, 0);
  assert.equal(ui.element('end-session-btn').hidden, true);
});

function registrationHarness(fetch) {
  const ui = harness('register.js', fetch);
  const values = {username:'professor',email:'professor@gmail.com',password:'Senha123!',password2:'Senha123!',role:'professor',institution_nome:'Campus Novo',institution_logradouro:'Rua A',institution_numero:'10',institution_bairro:'Centro',institution_cidade:'Três Lagoas',institution_estado:'ms'};
  ui.context.FormData = class { get(key) { return values[key] ?? ''; } };
  ui.element('register-form').querySelector = () => ui.element('submit-registration');
  ui.element('role').value = 'professor';
  ui.element('role').listeners.change();
  return {...ui, values};
}

test('cadastro alterna instituição existente e nova sem exigir campos ocultos', async () => {
  const ui = registrationHarness(async () => response([]));
  await flush();
  assert.equal(ui.element('institution-group').hidden, false);
  assert.equal(ui.element('instituicao').required, true);
  ui.element('new-institution-toggle').listeners.click();
  assert.equal(ui.element('new-institution-fields').hidden, false);
  assert.equal(ui.element('new-institution-fields').disabled, false);
  assert.equal(ui.element('instituicao').disabled, true);
  assert.equal(ui.element('instituicao').required, false);
  assert.equal(ui.element('institution-name').focused, true);
  ui.element('role').value = 'aluno';
  ui.element('role').listeners.change();
  assert.equal(ui.element('institution-group').hidden, true);
  assert.equal(ui.element('new-institution-fields').disabled, true);
  assert.equal(ui.element('matricula').required, true);
  ui.element('role').value = 'professor';
  ui.element('role').listeners.change();
  ui.element('new-institution-toggle').listeners.click();
  assert.equal(ui.element('new-institution-fields').disabled, true);
  assert.equal(ui.element('instituicao').required, true);
});

test('cadastro envia endereço da nova instituição e informa localização pendente', async () => {
  let sent;
  const ui = registrationHarness(async (url, options) => {
    if (url === '/api/instituicoes/') return response([]);
    sent = JSON.parse(options.body);
    return response({message:'ok'}, 201);
  });
  await flush();
  ui.element('new-institution-toggle').listeners.click();
  await ui.element('register-form').listeners.submit({preventDefault(){}});
  assert.equal(sent.nova_instituicao.estado, 'MS');
  assert.equal(sent.nova_instituicao.nome, 'Campus Novo');
  assert.equal(sent.instituicoes, undefined);
  assert.match(ui.element('success-message').textContent, /administrador.*localização/);
  assert.equal(ui.element('register-form').hidden, true);
});

test('erro de endereço aninhado aparece como texto e permite corrigir o cadastro', async () => {
  const ui = registrationHarness(async url => url === '/api/instituicoes/' ? response([]) : response({nova_instituicao:{estado:['Informe uma UF válida.']}},400));
  await flush();
  ui.element('new-institution-toggle').listeners.click();
  await ui.element('register-form').listeners.submit({preventDefault(){}});
  assert.equal(ui.element('error-message').textContent, 'Informe uma UF válida.');
  assert.equal(ui.element('submit-registration').disabled, false);
  assert.equal(ui.element('register-form').hidden, false);
});

test('cadastro existente continua enviando apenas as instituições selecionadas', async () => {
  let sent;
  const ui = registrationHarness(async (url, options) => {
    if (url === '/api/instituicoes/') return response([]);
    sent = JSON.parse(options.body);
    return response({},201);
  });
  await flush();
  ui.element('instituicao').selectedOptions = [{value:'7'}];
  await ui.element('register-form').listeners.submit({preventDefault(){}});
  assert.deepEqual(sent.instituicoes,[7]);
  assert.equal(sent.nova_instituicao,undefined);
});
