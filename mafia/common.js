/* Математикалық Мафия: Диверсанттар — ортақ код (студент және апай беттері) */
const MM = (() => {
  const qs = new URLSearchParams(location.search);
  const BROKERS = {
    hivemq: 'wss://broker.hivemq.com:8884/mqtt',
    emqx: 'wss://broker.emqx.io:8084/mqtt',
  };
  const brokerKey = BROKERS[qs.get('b')] ? qs.get('b') : 'hivemq';
  const TOPIC = 'math-mafia-dv-v1/';

  const ROUNDS = [
    null,
    { n: 1, topic: 'Шектер', min: 3, pts: [10] },
    { n: 2, topic: 'Туынды', min: 3, pts: [15] },
    { n: 3, topic: 'Интегралдар', min: 4, pts: [8, 12] },
    { n: 4, topic: 'Матрицалар мен анықтауыштар', min: 4, pts: [10, 15] },
  ];

  // Есептер мен жауап нұсқалары (дұрыс жауап кілті тек апай бетінде, шифрланған)
  const PROB = {
    1: {
      I: { text: 'Шекті есептеңдер:', tex: String.raw`\lim_{x\to\infty}\left(\frac{x+3}{x-1}\right)^{2x+1}`,
        parts: [{ label: 'Жауап', opts: [String.raw`e^{4}`, '1', String.raw`e^{8}`, String.raw`e^{2}`] }] },
      II: { text: 'Шекті есептеңдер:', tex: String.raw`\lim_{x\to 0}\frac{1-\cos 4x}{x\,\sin 2x}`,
        parts: [{ label: 'Жауап', opts: ['8', '4', '16', '2'] }] },
    },
    2: {
      I: { text: 'Функцияның x = 1 нүктесіндегі туындысын табыңдар:', tex: String.raw`y=x^{2}e^{-3x},\qquad y'(1)=\,?`,
        parts: [{ label: 'Жауап', opts: [String.raw`\dfrac{3}{e^{3}}`, String.raw`-\dfrac{6}{e^{3}}`, String.raw`\dfrac{5}{e^{3}}`, String.raw`-\dfrac{1}{e^{3}}`] }] },
      II: { text: 'Функцияның берілген нүктедегі туындысын табыңдар:', tex: String.raw`y=\sin^{2}3x,\qquad y'\!\left(\tfrac{\pi}{12}\right)=\,?`,
        parts: [{ label: 'Жауап', opts: ['1', String.raw`\sqrt{2}`, '3', String.raw`3\sqrt{2}`] }] },
    },
    3: {
      I: { text: 'а) Анықталмаған интегралды табыңдар; ә) анықталған интегралды есептеңдер:', tex: String.raw`\text{а)}\ \int x\,e^{2x}\,dx\qquad \text{ә)}\ \int_{0}^{1}x\,e^{2x}\,dx`,
        parts: [
          { label: 'а) ∫ x·e²ˣ dx', opts: [String.raw`\dfrac{e^{2x}(2x+1)}{4}+C`, String.raw`\dfrac{e^{2x}(2x-1)}{4}+C`, String.raw`\dfrac{x\,e^{2x}}{2}+C`, String.raw`\dfrac{e^{2x}(x-1)}{2}+C`] },
          { label: 'ә) ∫₀¹ x·e²ˣ dx', opts: [String.raw`\dfrac{e^{2}}{4}`, String.raw`\dfrac{e^{2}-1}{4}`, String.raw`\dfrac{3e^{2}-1}{4}`, String.raw`\dfrac{e^{2}+1}{4}`] },
        ] },
      II: { text: 'а) Анықталмаған интегралды табыңдар; ә) анықталған интегралды есептеңдер:', tex: String.raw`\text{а)}\ \int x\cos x\,dx\qquad \text{ә)}\ \int_{0}^{\pi/2}x\cos x\,dx`,
        parts: [
          { label: 'а) ∫ x·cos x dx', opts: [String.raw`x\sin x+\cos x+C`, String.raw`x\sin x-\cos x+C`, String.raw`-x\sin x+\cos x+C`, String.raw`\dfrac{x^{2}}{2}\sin x+C`] },
          { label: 'ә) ∫₀^{π/2} x·cos x dx', opts: [String.raw`\dfrac{\pi}{2}+1`, String.raw`\dfrac{\pi}{2}`, String.raw`\dfrac{\pi}{2}-1`, String.raw`1-\dfrac{\pi}{2}`] },
        ] },
    },
    4: {
      I: { text: 'A матрицасы берілген. а) det A; ә) det(2A) табыңдар:', tex: String.raw`A=\begin{pmatrix}2&-1&3\\1&0&2\\4&1&-1\end{pmatrix}`,
        parts: [{ label: 'а) det A', opts: ['8', '-10', '10', '-4'] }, { label: 'ә) det(2A)', opts: ['-20', '64', '-40', '-80'] }] },
      II: { text: 'B матрицасы берілген. а) det B; ә) det(3B) табыңдар:', tex: String.raw`B=\begin{pmatrix}1&2&0\\3&-1&4\\2&1&1\end{pmatrix}`,
        parts: [{ label: 'а) det B', opts: ['-15', '15', '5', '-5'] }, { label: 'ә) det(3B)', opts: ['15', '135', '45', '-405'] }] },
    },
  };
  const LETTERS = ['A', 'B', 'C', 'D'];

  const GRADE = [[95, 'A', 'Өте жақсы'], [90, 'A-', 'Өте жақсы'], [85, 'B+', 'Жақсы'], [80, 'B', 'Жақсы'], [75, 'B-', 'Жақсы'],
    [70, 'C+', 'Қанағаттанарлық'], [65, 'C', 'Қанағаттанарлық'], [60, 'C-', 'Қанағаттанарлық'], [55, 'D+', 'Қанағаттанарлық'],
    [50, 'D', 'Қанағаттанарлық'], [0, 'F', 'Қанағаттанарлықсыз']];
  const grade = (b) => GRADE.find(g => b >= g[0]);

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const tex = (t, display) => {
    try { return window.katex ? katex.renderToString(t, { throwOnError: false, displayMode: !!display }) : esc(t); }
    catch (e) { return esc(t); }
  };
  const rid = (n = 10) => Array.from(crypto.getRandomValues(new Uint8Array(n)), b => 'abcdefghijkmnpqrstuvwxyz23456789'[b % 32]).join('');
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { } },
  };

  // ---- ECDH (P-256) + AES-GCM: рөлдер тек иесіне ашылады ----
  const b64 = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf)));
  const unb64 = (s) => Uint8Array.from(atob(s), c => c.charCodeAt(0));
  async function keypair(storeKey) {
    const saved = store.get(storeKey);
    if (saved) {
      const priv = await crypto.subtle.importKey('jwk', saved.priv, { name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveKey']);
      return { priv, pubJwk: saved.pub };
    }
    const kp = await crypto.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveKey']);
    const priv = await crypto.subtle.exportKey('jwk', kp.privateKey);
    const pub = await crypto.subtle.exportKey('jwk', kp.publicKey);
    store.set(storeKey, { priv, pub });
    return { priv: kp.privateKey, pubJwk: pub };
  }
  async function shared(priv, pubJwk) {
    const pub = await crypto.subtle.importKey('jwk', pubJwk, { name: 'ECDH', namedCurve: 'P-256' }, false, []);
    return crypto.subtle.deriveKey({ name: 'ECDH', public: pub }, priv, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
  }
  async function seal(key, obj) {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, new TextEncoder().encode(JSON.stringify(obj)));
    return { iv: b64(iv), ct: b64(ct) };
  }
  async function open(key, box) {
    const pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: unb64(box.iv) }, key, unb64(box.ct));
    return JSON.parse(new TextDecoder().decode(pt));
  }

  // ---- MQTT ----
  function connect(room, onMsg, onStatus, subs) {
    const base = TOPIC + room + '/';
    const client = mqtt.connect(BROKERS[brokerKey], {
      clientId: 'mm_' + rid(10), clean: true, reconnectPeriod: 2000, keepalive: 30, connectTimeout: 15000,
    });
    client.on('connect', () => { onStatus('ok'); client.subscribe(subs.map(s => base + s), { qos: 1 }); });
    client.on('reconnect', () => onStatus('wait'));
    client.on('offline', () => onStatus('off'));
    client.on('error', () => onStatus('off'));
    client.on('message', (topic, payload) => {
      const t = topic.slice(base.length);
      let data = null;
      try { data = payload.length ? JSON.parse(payload.toString()) : null; } catch (e) { return; }
      onMsg(t, data);
    });
    return {
      client, base,
      pub(t, obj, retain = false) { client.publish(base + t, obj === null ? '' : JSON.stringify(obj), { qos: 1, retain }); },
    };
  }

  return { qs, BROKERS, brokerKey, TOPIC, ROUNDS, PROB, LETTERS, grade, esc, tex, rid, store, keypair, shared, seal, open, connect, b64, unb64 };
})();
