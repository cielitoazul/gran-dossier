# Gran Dossier — plantilla. Lee datos/<fecha>.json y genera dias/<fecha>.html + index.html.
# Uso: python3 build.py            (reconstruye todo)
# Antes de escribir nada, el filtro de privacidad revisa los datos y frena si encuentra algo personal.
import html, json, re, sys
from pathlib import Path

RAIZ = Path(__file__).parent
DATOS, DIAS = RAIZ / "datos", RAIZ / "dias"
e = lambda s: html.escape(str(s or ""))

# ---- filtro de privacidad --------------------------------------------------
PROHIBIDO = [r"\bFernando\b", r"\bFer\b", r"Calder[oó]n", r"Chiclayo", r"Lambayeque",
             r"Mall Aventura", r"Real Plaza", r"27cieloazul", r"@gmail"]

def revisar_privacidad(archivo, texto):
    hallazgos = [p for p in PROHIBIDO if re.search(p, texto, re.I)]
    if hallazgos:
        sys.exit(f"✗ FRENADO: {archivo.name} contiene {hallazgos}. Corrige el JSON antes de publicar.")

# ---- piezas ----------------------------------------------------------------
MESES = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
DIAS_SEM = "lunes martes miércoles jueves viernes sábado domingo".split()
KIND = {
    "illness-script": ("Illness Script", "#0d9488"), "detcsp": ("DETcSp", "#0891b2"),
    "tutor": ("Tutor", "#7c3aed"), "enam": ("ENAM", "#d97706"),
    "escriba": ("Escriba", "#2563eb"), "paciente": ("Paciente Std", "#db2777"),
}
CINE = {"MA": "#dc2626", "RP": "#2563eb"}  # Mall Aventura rojito, Real Plaza azulito

def fecha_larga(f):
    from datetime import date
    y, m, d = map(int, f.split("-"))
    return f"{DIAS_SEM[date(y, m, d).weekday()]} {d} de {MESES[m-1]} de {y}"

def doi(x):
    return f'<a class="lnk" href="https://doi.org/{e(x)}" target="_blank" rel="noopener">↗ DOI</a>' if x else ""

def pendiente(titulo, nota="Se llena al correr el Reporte Mañanero."):
    return f'<div class="block"><h3>{e(titulo)}</h3><div class="pend">⏳ Pendiente · {e(nota)}</div></div>'

def dossier(d):
    top = "".join(f"""
      <article class="pcard{' first' if i == 1 else ''}">
        <span class="rank">{i}</span>
        <div class="src">{e(p['fuente'])}</div>
        <h4>{e(p['titulo'])}</h4>
        <p>{e(p['por_que_te_importa'])}</p>
        <div class="pred"><b>Predicción</b><span>opinión, sin fuente</span>{e(p['prediccion'])}</div>
        {doi(p['doi'])}
      </article>""" for i, p in enumerate(d["top3"], 1))
    radar = "".join(f"""
      <li class="ritem"><span class="rn">{i:02d}</span><div>
        <div class="src">{e(p['fuente'])}</div>
        <div class="rt">{e(p['titulo'])}</div>
        <div class="rl">{e(p['una_linea'])}</div>
        <div class="pred"><b>Predicción</b>{e(p['prediccion'])}</div>{doi(p['doi'])}
      </div></li>""" for i, p in enumerate(d["radar"], 1))
    lista = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)
    ideas = "".join(
        f'<li><span class="tag" style="--k:{KIND.get(x["tipo"], (x["tipo"], "#64748b"))[1]}">'
        f'{e(KIND.get(x["tipo"], (x["tipo"],))[0])}</span>{e(x["idea"])}</li>' for x in d["ideas"])
    m = d["meta"]
    return f"""
    <div class="block">
      <h3>📚 Dossier · {e(d['titulo'])}</h3>
      <div class="stats"><span><b>{m['encontrados']}</b> encontrados</span><span><b>{m['revisados']}</b> revisados</span>
        <span><b>{len(d['top3']) + len(d['radar'])}</b> curados</span></div>
      <h5>🏆 Top 3</h5><div class="pgrid">{top}</div>
      <h5>📡 Radar</h5><ol class="radar">{radar}</ol>
      <div class="cols">
        <div class="panel"><h5>💎 Perlas del día</h5><ul class="dots">{lista(d['perlas'])}</ul></div>
        <div class="panel"><h5>❓ Preguntas del día</h5><ul class="dots q">{lista(d['preguntas'])}</ul></div>
      </div>
      <div class="panel"><h5>💡 Ideas del día</h5><ul class="ideas">{ideas}</ul></div>
      <p class="fine">Fuente: artículos obtenidos de {e(m['fuente'])} · ventana {e(m['ventana'])}.
        Predicciones, preguntas e ideas son opinión del modelo, no evidencia.</p>
    </div>"""

def fuentes(fs):
    return " · ".join(f'<a class="lnk" href="{e(f["url"])}" target="_blank" rel="noopener">↗ {e(f["label"])}</a>' for f in fs or [])

def noticias(titulo, items, aviso=""):
    if not items:
        return pendiente(titulo)
    cuerpo = "".join(f"""<div class="news"><h4>{e(n['titulo'])}</h4><p>{e(n['texto'])}</p>
      <div class="fuentes">{fuentes(n.get('fuentes'))}</div></div>""" for n in items)
    nota = f'<div class="pend">⚠️ {e(aviso)}</div>' if aviso else ""
    return f'<div class="block"><h3>{e(titulo)}</h3>{cuerpo}{nota}</div>'

def economico(ec):
    if not ec:
        return pendiente("💰 Dato Económico")
    filas = "".join(f"<tr><td>{e(a)}</td><td><b>{e(b)}</b></td><td>{e(c)}</td></tr>" for a, b, c in ec["filas"])
    return f"""<div class="block"><h3>💰 Dato Económico</h3>
      <table class="tbl"><tr><th>Indicador</th><th>Valor</th><th>Fuente</th></tr>{filas}</table>
      <p class="impact"><b>Impacto en ti:</b> {e(ec['impacto'])}</p><div class="fuentes">{fuentes(ec.get('fuentes'))}</div></div>"""

def cartelera(c):
    leyenda = " ".join(f'<span class="cine" style="--c:{col}">{k}</span>' for k, col in CINE.items())
    if not c:
        return f"""<div class="block"><h3>🎟️ Cartelera</h3><div class="legend">{leyenda}</div>
          <div class="pend">⏳ Pendiente · Se llena con el script de cartelera.</div></div>"""
    filas = ""
    for sala in CINE:
        for peli, score, horas in c.get(sala, []):
            filas += (f'<tr><td><span class="cine" style="--c:{CINE[sala]}">{sala}</span></td>'
                      f'<td><b>{e(peli)}</b></td><td>{e(score)}</td><td class="horas">{e(horas)}</td></tr>')
    return f"""<div class="block"><h3>🎟️ Cartelera</h3><div class="legend">{leyenda}</div>
      <table class="tbl"><tr><th>Sala</th><th>Película</th><th>Score</th><th>Horarios</th></tr>{filas}</table>
      <p class="fine">{e(c.get('nota'))}</p></div>"""

def veredicto(v):
    if not v:
        return pendiente("🎯 Veredicto para Lucho")
    return f"""<div class="block"><h3>🎯 Veredicto para Lucho</h3><p>{e(v['texto'])}</p>
      <blockquote class="frase">«{e(v['frase'])}»</blockquote></div>"""

def youtube(yt):
    if not isinstance(yt, dict):
        return aviso("📺 YouTube Watchlist", yt)
    filas = "".join(f"""<tr><td>{e(pri)}</td><td><b>{e(canal)}</b><div class="fine">{e(cat)}</div></td>
      <td><a href="{e(url)}" target="_blank" rel="noopener">{e(tit)}</a></td><td class="horas">{e(dur)}</td></tr>"""
      for canal, cat, tit, dur, pri, url in yt["videos"])
    return f"""<div class="block"><h3>📺 YouTube Watchlist</h3>
      <table class="tbl"><tr><th></th><th>Canal</th><th>Video</th><th>Dur.</th></tr>{filas}</table>
      <p class="fine">{e(yt.get('nota'))}</p></div>"""

def aviso(titulo, texto):
    return f'<div class="block"><h3>{e(titulo)}</h3><div class="pend">⚠️ {e(texto)}</div></div>' if texto else pendiente(titulo)

def evangelio(ev):
    return f"""
    <section class="gospel">
      <div class="g-head">✝️ Evangelio del día · <span>{e(ev['dia_liturgico'])}</span></div>
      <blockquote>«{e(ev['versiculo'])}» <cite>{e(ev['versiculo_cita'])}</cite></blockquote>
      <p>{e(ev['idea_central'])}</p>
      <a class="lnk" href="{e(ev['url'])}" target="_blank" rel="noopener">↗ Leer {e(ev['cita'])} completo en {e(ev['fuente'])}</a>
      {f'<p class="fine">{e(ev["nota"])}</p>' if ev.get('nota') else ''}
    </section>"""

# ---- estilos compartidos ---------------------------------------------------
CSS = """
:root{--bg:#f8fafc;--card:#fff;--soft:#f1f5f9;--line:#e2e8f0;--text:#0f172a;--muted:#64748b;--dim:#94a3b8;
  --accent:#2563eb;--accent-soft:#eff6ff;--gold:#b45309;--gold-soft:#fffbeb;}
@media (prefers-color-scheme:dark){:root{--bg:#0b0d12;--card:#13161d;--soft:#1a1e28;--line:#252a36;--text:#e8eaf0;
  --muted:#9aa0b0;--dim:#5f6678;--accent:#60a5fa;--accent-soft:#172033;--gold:#fbbf24;--gold-soft:#231d0f;}}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,system-ui,'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:var(--accent)} .wrap{max-width:860px;margin:0 auto;padding:20px 16px 64px}
header.top{padding:24px 16px 8px;max-width:860px;margin:0 auto}
.back{font-size:13px;color:var(--muted);text-decoration:none} h1{font-size:26px;font-weight:800;margin-top:6px}
.sub{color:var(--muted);font-size:14px;text-transform:capitalize}
.summary{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:16px 0}
.summary h2{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.summary li{margin:6px 0 6px 18px;font-size:15px}
.gospel{background:var(--gold-soft);border:1px solid color-mix(in srgb,var(--gold) 30%,transparent);border-radius:14px;padding:16px 18px;margin-bottom:18px}
.g-head{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--gold)} .g-head span{text-transform:none;font-weight:500}
blockquote{font-size:17px;font-style:italic;margin:10px 0 8px} cite{font-style:normal;font-size:13px;color:var(--muted)}
.gospel p{font-size:14px;color:var(--muted);margin-bottom:8px}
nav.tabs{position:sticky;top:0;z-index:5;background:var(--bg);display:flex;gap:6px;padding:10px 0;border-bottom:1px solid var(--line)}
nav.tabs button{flex:1;border:1px solid var(--line);background:var(--card);color:var(--text);border-radius:10px;padding:10px 6px;font-size:14px;font-weight:600;cursor:pointer}
nav.tabs button.on{background:var(--accent);border-color:var(--accent);color:#fff}
.tab{display:none;padding-top:16px} .tab.on{display:block}
.block{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:14px}
.block h3{font-size:16px;margin-bottom:10px} h5{font-size:12px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin:18px 0 10px}
.pend{background:var(--soft);border:1px dashed var(--line);border-radius:10px;padding:10px 12px;font-size:13px;color:var(--muted)}
.stats{display:flex;gap:8px;flex-wrap:wrap} .stats span{background:var(--soft);border-radius:99px;padding:3px 10px;font-size:12px;color:var(--muted)}
.stats b{color:var(--accent)}
.pgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.pcard{position:relative;background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:16px}
.pcard.first{border-color:var(--accent);background:var(--accent-soft)}
.rank{position:absolute;top:12px;right:12px;width:24px;height:24px;border-radius:50%;background:var(--accent);color:#fff;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center}
.src{font-size:11px;font-weight:600;letter-spacing:.03em;text-transform:uppercase;color:var(--dim);margin-bottom:4px;padding-right:28px}
.pcard h4{font-size:15px;line-height:1.35;margin-bottom:8px} .pcard p{font-size:13.5px;color:var(--muted);margin-bottom:10px}
.pred{font-size:13px;background:var(--card);border-left:3px solid var(--accent);border-radius:0 8px 8px 0;padding:7px 10px;margin:6px 0 8px}
.pred b{display:block;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--accent)}
.pred span{font-size:10.5px;color:var(--dim);margin-left:4px} .pcard .pred{background:var(--card)}
.lnk{font-size:12px;font-weight:600;text-decoration:none}
.radar{list-style:none} .ritem{display:grid;grid-template-columns:28px 1fr;gap:8px;padding:12px 0;border-top:1px solid var(--line)}
.rn{font-weight:700;color:var(--accent);font-size:13px} .rt{font-weight:600;font-size:14px} .rl{font-size:13.5px;color:var(--muted);margin:2px 0}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px}
.panel{background:var(--soft);border-radius:12px;padding:4px 14px 12px;margin-top:12px}
.dots{list-style:none} .dots li{position:relative;padding-left:16px;margin:8px 0;font-size:13.5px}
.dots li::before{content:'';position:absolute;left:0;top:8px;width:6px;height:6px;border-radius:50%;background:var(--accent)}
.dots.q li::before{border-radius:1px;transform:rotate(45deg)}
.ideas{list-style:none} .ideas li{display:flex;gap:10px;align-items:baseline;margin:8px 0;font-size:13.5px}
.tag{flex-shrink:0;min-width:92px;text-align:center;font-size:10.5px;font-weight:700;text-transform:uppercase;color:var(--k);
  background:color-mix(in srgb,var(--k) 14%,transparent);border:1px solid color-mix(in srgb,var(--k) 35%,transparent);border-radius:99px;padding:2px 8px}
.legend{display:flex;gap:8px;margin-bottom:10px}
.cine{font-size:12px;font-weight:800;color:#fff;background:var(--c);border-radius:6px;padding:2px 8px}
.fine{font-size:11.5px;color:var(--dim);margin-top:14px}
.days{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-top:16px}
.day{display:block;text-decoration:none;color:var(--text);background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}
.day:first-child{border-color:var(--accent)} .day .d{font-weight:700;text-transform:capitalize} .day .f{font-size:13px;color:var(--muted);margin-top:4px}
.news{padding:10px 0;border-top:1px solid var(--line)} .news:first-of-type{border-top:none;padding-top:0}
.news h4{font-size:15px;margin-bottom:4px} .news p{font-size:14px;color:var(--muted);margin-bottom:6px}
.fuentes{display:flex;flex-wrap:wrap;gap:4px 10px} .poder{margin-bottom:14px}
.tbl{width:100%;border-collapse:collapse;font-size:13.5px;display:block;overflow-x:auto}
.tbl th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--dim);padding:6px 8px;border-bottom:1px solid var(--line)}
.tbl td{padding:8px;border-bottom:1px solid var(--line);vertical-align:top} .horas{white-space:nowrap;color:var(--muted)}
.impact{font-size:14px;margin:10px 0 6px} .frase{font-size:15px;margin-top:10px;color:var(--accent)}
footer{color:var(--dim);font-size:12px;text-align:center;margin-top:32px}
@media(max-width:640px){.cols{grid-template-columns:1fr} h1{font-size:22px}}
"""

JS = """
const tabs=[...document.querySelectorAll('nav.tabs button')],panels=[...document.querySelectorAll('.tab')];
function show(id){tabs.forEach(b=>b.classList.toggle('on',b.dataset.t===id));panels.forEach(p=>p.classList.toggle('on',p.id===id));
  try{history.replaceState(null,'','#'+id)}catch(_){}}
tabs.forEach(b=>b.onclick=()=>show(b.dataset.t));
show(['medicina','actualidad','ocio'].includes(location.hash.slice(1))?location.hash.slice(1):'medicina');
"""

def pagina(titulo, cuerpo, js=""):
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{e(titulo)}</title>
<style>{CSS}</style></head><body>{cuerpo}{f'<script>{js}</script>' if js else ''}</body></html>"""

def render_dia(d):
    med, act, oc = d["medicina"], d["actualidad"], d["ocio"]
    cuerpo = f"""
<header class="top"><a class="back" href="../index.html">← Todos los días</a>
  <h1>📅 {e(fecha_larga(d['fecha']))}</h1><div class="sub">Gran Dossier · para Lucho</div></header>
<main class="wrap">
  <section class="summary"><h2>☀️ Resumen del día</h2><ul>{''.join(f'<li>{e(x)}</li>' for x in d['resumen'])}</ul></section>
  {evangelio(d['evangelio']) if d.get('evangelio') else ''}
  <nav class="tabs"><button data-t="medicina">🩺 Medicina</button><button data-t="actualidad">🌎 Actualidad</button><button data-t="ocio">🎬 Ocio</button></nav>
  <section class="tab" id="medicina">
    {noticias('🩺 Radar Médico & IA', med.get('radar_medico'))}
    {dossier(med['dossier']) if med.get('dossier') else pendiente('📚 Dossier de papers')}
  </section>
  <section class="tab" id="actualidad">
    {f'<div class="pend poder">🏛️ {e(act["poder"])}</div>' if act.get('poder') else ''}
    {noticias('🇵🇪 La Pepa (Nacional)', act.get('nacional'), act.get('aviso_nivel2', ''))}
    {noticias('🚨 Alarma de Narrativa', act.get('narrativa'))}
    {economico(act.get('economico'))}
  </section>
  <section class="tab" id="ocio">
    {aviso('🌟 Lo mejor en streaming', oc.get('streaming'))}
    {noticias('🆕 Estrenos de la semana', oc.get('estrenos'))}
    {cartelera(oc.get('cartelera'))}
    {veredicto(oc.get('veredicto'))}
    {youtube(oc.get('youtube'))}
  </section>
  <footer>Gran Dossier · generado automáticamente</footer>
</main>"""
    return pagina(f"Gran Dossier — {d['fecha']}", cuerpo, JS)

def render_index(dias):
    tarjetas = "".join(f"""<a class="day" href="dias/{d['fecha']}.html"><div class="d">{e(fecha_larga(d['fecha']))}</div>
      <div class="f">{e(d['evangelio']['dia_liturgico'].split('·')[-1].strip()) if d.get('evangelio') else ''}</div></a>"""
      for d in dias)
    cuerpo = f"""<header class="top"><h1>📚 Gran Dossier</h1><div class="sub">Medicina · Actualidad · Ocio — un día por página</div></header>
<main class="wrap"><div class="days">{tarjetas}</div><footer>Gran Dossier</footer></main>"""
    return pagina("Gran Dossier", cuerpo)

# ---- construir -------------------------------------------------------------
archivos = sorted(DATOS.glob("*.json"), reverse=True)
dias = []
for a in archivos:
    texto = a.read_text()
    revisar_privacidad(a, texto)
    dias.append(json.loads(texto))
DIAS.mkdir(exist_ok=True)
for d in dias:
    (DIAS / f"{d['fecha']}.html").write_text(render_dia(d))
    print(f"✓ dias/{d['fecha']}.html")
(RAIZ / "index.html").write_text(render_index(dias))
print(f"✓ index.html ({len(dias)} días)")
