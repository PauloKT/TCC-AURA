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
    return { style: {}, disabled: true, hidden: false, textContent: '', value: '', children: [],
      selectedOptions: [{ textContent: 'Test' }], classList: { add() {}, remove() {} }, listeners: {},
      addEventListener(event, callback) { this.listeners[event] = callback; },
      dispatchEvent(event) { return this.listeners[event.type]?.call(this, event); },
      removeAttribute(name) { delete this[name]; },
      append(...items) { this.children.push(...items); }, appendChild(item) { this.children.push(item); },
      replaceChildren(...items) { this.children = items; }, querySelectorAll() { return []; }
    };
  }
  const element = id => { if (!elements.has(id)) elements.set(id, makeElement()); return elements.get(id); };
  const context = {
    document: { hidden: false, getElementById: element, addEventListener(event, callback) { events[event] = callback; }, createElement: makeElement },
    window: { isSecureContext: true, location: { pathname: '/confirmar-presenca.html', search: '?sessaoId=1&token=old', origin: 'https://aura.test' }, addEventListener() {} },
    localStorage: { getItem: key => storage.get(key) || null, setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key) },
    navigator: { geolocation: { getCurrentPosition(success, error) { locate = { success, error }; } } },
    URL, URLSearchParams, Date, console, fetch, Event: class Event { constructor(type) { this.type = type; } }, alert() {},
    atob: value => Buffer.from(value, 'base64').toString(),
    setTimeout(callback) { const id = ++sequence; timers.set(id, callback); return id; }, clearTimeout(id) { timers.delete(id); },
    setInterval(callback) { const id = ++sequence; intervals.set(id, callback); return id; }, clearInterval(id) { intervals.delete(id); }
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, 'api.js'), 'utf8'), context);
  context.Aura = context.window.Aura;
  vm.runInContext(fs.readFileSync(path.join(__dirname, file), 'utf8'), context);
  const ready = events.DOMContentLoaded();
  return { element, get locate() { return locate; }, intervals, timers, context, storage, ready };
}
const flush = () => new Promise(resolve => setImmediate(resolve));
const response = (data, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => data });
const prepared = { comprovante: 'signed', turma: 'Turma A', aula: 'Aula 1' };

test('criar turma e aula seleciona os registros e libera a chamada', async () => {
  let group;
  let lesson;
  const ui = harness('professor.js', async (url, options = {}) => {
    if (url === '/api/materias/') return response([{ id: 1, nome: 'Mat', codigo: 'M' }]);
    if (url === '/api/turmas/' && options.method === 'POST') {
      group = { ...JSON.parse(options.body), id: 2, codigo_acesso: 'AB2CD3EF' };
      return response(group, 201);
    }
    if (url === '/api/turmas/?materia=1') return response(group ? [group] : []);
    if (url === '/api/aulas/' && options.method === 'POST') {
      lesson = { ...JSON.parse(options.body), id: 3 };
      return response(lesson, 201);
    }
    if (url === '/api/aulas/?turma=2') return response(lesson ? [lesson] : []);
    throw new Error(url);
  });
  await flush();
  ui.element('materia-select').value = '1';
  ui.element('materia-select').listeners.change.call(ui.element('materia-select'));
  await flush();
  ui.element('turma-nome').value = 'T1';
  ui.element('turma-semestre').value = '2';
  ui.element('turma-ano').value = '2026';
  await ui.element('create-turma-btn').listeners.click();
  await flush();
  assert.equal(ui.element('turma-select').value, '2');
  assert.equal(ui.element('aulas-section').style.display, 'block');
  ui.element('aula-titulo').value = 'Aula';
  ui.element('aula-data').value = '2026-09-15';
  ui.element('aula-inicio').value = '08:00';
  ui.element('aula-fim').value = '10:00';
  await ui.element('create-aula-btn').listeners.click();
  assert.equal(lesson.turma, '2');
  assert.equal(ui.element('aula-select').value, '3');
  assert.equal(ui.element('session-section').style.display, 'block');
  assert.equal(ui.element('invite-code').value, 'AB2CD3EF');
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
  assert.equal(ui.element('materia-select').children.length, 1);
  assert.equal(ui.element('materia-select').children[0].value, 3);
});

test('professor sem matérias recebe indicação de vínculo vazio', async () => {
  const ui = harness('professor.js', async () => response([]));
  await flush();
  assert.match(ui.element('materia-select').innerHTML, /Nenhuma matéria vinculada/);
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
