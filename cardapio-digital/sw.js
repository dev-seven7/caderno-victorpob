/* Service worker do Cardápio Digital (protótipo · 25/11/2026)
   Objetivo: a 2ª visita abre rápido, e o app instalado abre mesmo com a rede ruim.
   - Página (HTML): REDE PRIMEIRO. Toda atualização publicada aparece na hora; o cache só entra se a rede falhar.
   - Fotos (avif/webp/png/svg): cache primeiro, no máximo 160 arquivos (as mais antigas saem).
   - Vídeos: NÃO entram no cache (são grandes e usam pedido por faixa); o navegador cuida deles.
   - Nada de pedido, cupom ou dado do cliente passa por aqui: o protótipo não envia nada, e no produto final
     a API da Databite fica fora do cache (só GET de arquivo estático é guardado).
   Atualizar a versão abaixo invalida tudo de uma vez. */
const VERSAO = "ogro-cd-2026-11-27-pontos";
const CASCA = ["./", "./index.html", "./manifest.webmanifest", "./img/ogro-horizontal-branco.svg", "./img/ogro-quadrado-cor-negativo.svg", "./img/icone-192.png"];
const MAX_FOTOS = 160;

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VERSAO).then(c => c.addAll(CASCA)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSAO).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

async function limitar(cache) {
  const ks = await cache.keys(), fotos = ks.filter(r => /\.(avif|webp|png|jpe?g|svg)$/i.test(new URL(r.url).pathname));
  for (let i = 0; i < fotos.length - MAX_FOTOS; i++) await cache.delete(fotos[i]);
}

self.addEventListener("fetch", e => {
  const req = e.request; if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;                       // fontes do Google, ViaCEP etc.: o navegador decide
  if (/\.(mp4|webm)$/i.test(url.pathname)) return;                  // vídeo fora do cache
  if (req.mode === "navigate" || url.pathname.endsWith("/") || url.pathname.endsWith(".html") || url.pathname.endsWith(".webmanifest")) {
    e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(VERSAO).then(k => k.put(req, c)); return r; })
      .catch(() => caches.match(req, { ignoreSearch: true }).then(r => r || caches.match("./index.html"))));
    return;
  }
  if (/\.(avif|webp|png|jpe?g|svg)$/i.test(url.pathname)) {
    e.respondWith(caches.open(VERSAO).then(async c => {
      const hit = await c.match(req); if (hit) return hit;
      const r = await fetch(req); if (r.ok) { c.put(req, r.clone()); limitar(c); } return r;
    }));
  }
});
