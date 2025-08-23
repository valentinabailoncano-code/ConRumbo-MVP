# app.py
import streamlit as st
from pathlib import Path
from streamlit.components.v1 import html
from io import BytesIO
import pandas as pd
from datetime import datetime
import zipfile, os, re
import platform
st.set_page_config(page_title="ConRumbo – Primeros Auxilios (MVP)", page_icon="🆘", layout="wide")


# ======== Estilo formal + botón SOS grande ========
st.markdown("""
<style>
/* limpieza y tipografía */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
:root { --brand:#D90429; --brand-dark:#a1031e; --ok:#16a34a; }
html, body, [class*="css"] { font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji","Segoe UI Emoji"; }

/* contenedor del botón */
.sos-wrap { 
  display:flex; align-items:center; gap:14px; 
  padding:14px 0 6px 0; 
  border-bottom:1px solid #e9e9ee; margin-bottom:14px;
}

/* botón rojo gigante */
.sos-btn {
  appearance:none; border:0; 
  background:var(--brand);
  color:#fff; font-weight:800; letter-spacing:0.5px;
  font-size:28px; line-height:1;
  padding:22px 34px; border-radius:16px;
  box-shadow: 0 6px 0 var(--brand-dark), 0 10px 24px rgba(217,4,41,.25);
  cursor:pointer; text-decoration:none; display:inline-flex; align-items:center; gap:12px;
  transition: transform .04s ease-in-out, box-shadow .2s ease;
}
.sos-btn:active { transform: translateY(2px); box-shadow: 0 4px 0 var(--brand-dark), 0 8px 18px rgba(217,4,41,.25); }
.sos-badge {
  background:#fff; color:var(--brand); font-weight:900; 
  border-radius:999px; padding:6px 10px; font-size:14px;
  box-shadow: inset 0 0 0 2px var(--brand);
}
</style>
""", unsafe_allow_html=True)

EMERGENCY_NUMBER = "112"

# En móvil/navegador compatible abrirá el marcador. En desktop mostrará el número.
sos_html = f'''
<div class="sos-wrap">
  <a class="sos-btn" href="tel:{EMERGENCY_NUMBER}" target="_self">
    <span class="sos-badge">SOS</span> LLAMAR {EMERGENCY_NUMBER}
  </a>
  <div>
    <div style="font-size:14px; color:#6b7280; margin-bottom:2px;">Botón de emergencia</div>
    <div style="font-size:13px; color:#111827;">En caso grave, pulsa el botón (móvil) o marca {EMERGENCY_NUMBER}.</div>
  </div>
</div>
'''
st.markdown(sos_html, unsafe_allow_html=True)

# Aviso para ordenadores (por si el enlace tel: no funciona)
if platform.system() in {"Windows","Darwin","Linux"}:
    st.info(f"Si estás en ordenador, abre tu teléfono y marca **{EMERGENCY_NUMBER}** manualmente.")

# =========================
# Estado de sesión
# =========================
defaults = {
    "emergency_mode": False,
    "scenario": None,
    "step_idx": 0,
    "chat_history": [],
    "progress": {
        "Emergencias": False,
        "Primeros auxilios": False,
        "Kits de supervivencia": False,
        "Mantén la calma (APA)": False,
        "Simulacro completado": False,
    }
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v if not isinstance(v, dict) else v.copy()

# =========================
# Utilidades generales
# =========================
def to_bytes(content: str) -> bytes:
    bio = BytesIO()
    bio.write(content.encode("utf-8"))
    bio.seek(0)
    return bio.read()

def download_md_button(label: str, content: str, filename: str):
    st.download_button(label, data=content.encode("utf-8"), file_name=filename, mime="text/markdown")

# =========================
# Contenidos guía (checklists)
# =========================
SCENARIOS = {
    "Atragantamiento (adulto)": [
        "Comprueba si tose o habla. Si NO puede, es obstrucción severa.",
        "Pide ayuda y llama al 112.",
        "Da 5 golpes entre omóplatos.",
        "Aplica 5 compresiones abdominales (Heimlich).",
        "Alterna 5 golpes / 5 compresiones hasta expulsar el objeto.",
        "Si pierde la consciencia, inicia RCP y usa DEA si lo hay."
    ],
    "Quemadura térmica": [
        "Retira la fuente de calor. No arranques ropa pegada.",
        "Enfría con agua templada 15–20 min. No uses hielo.",
        "Retira anillos/relojes si hay inflamación.",
        "Cubre con paño estéril/limpio. No revientes ampollas.",
        "Quemaduras extensas, químicas o eléctricas: 112."
    ],
    "Desmayo (síncope)": [
        "Túmbala y eleva piernas 20–30 cm.",
        "Afloja ropa apretada, ventila el entorno.",
        "Valora respuesta y respiración.",
        "Si no recupera en 1–2 min o hay signos graves: 112.",
        "Si no respira normalmente, inicia RCP."
    ],
    "Parada cardiorrespiratoria": [
        "Verifica seguridad de la escena.",
        "No respira o jadea: llama 112 inmediatamente.",
        "RCP: 30 compresiones a 100–120/min (profundidad 5–6 cm).",
        "2 ventilaciones si sabes y tienes barrera; si no, solo compresiones.",
        "Usa DEA en cuanto esté disponible y sigue sus instrucciones.",
        "No interrumpas hasta relevo o recuperación de signos de vida."
    ]
}

PRIMEROS_AUX = {
    "Hemorragias": [
        "Presión directa 10 min con apósito/paño limpio.",
        "Eleva el miembro si es posible.",
        "Si no cede o es abundante: 112.",
        "No retires cuerpos extraños incrustados: estabiliza alrededor."
    ],
    "Convulsiones": [
        "Protege la cabeza, retira objetos cercanos.",
        "No sujetes, no introduzcas nada en la boca.",
        "Controla tiempo de convulsión.",
        "Si dura >5 min, se repite, embarazo o lesión: 112.",
        "En recuperación: posición lateral de seguridad."
    ],
    "Intoxicaciones": [
        "Identifica sustancia, cantidad y tiempo.",
        "No provoques el vómito.",
        "Si hay dificultad respiratoria, convulsiones o niños: 112.",
        "Lleva envase/etiqueta al centro sanitario si procede."
    ],
    "Traumatismos": [
        "Inmoviliza el área lesionada.",
        "Hielo envuelto 10–15 min (descansos).",
        "Dolor intenso, deformidad, pérdida de función o cabeza/cuello: 112."
    ]
}

KITS = {
    "Hogar": [
        "Guantes, mascarillas, gasas estériles, vendas, esparadrapo.",
        "Suero fisiológico, clorhexidina/antiséptico.",
        "Tijeras, pinzas, manta térmica, termómetro.",
        "Analgésicos de uso común (si no hay contraindicaciones).",
        "Linterna, pilas, lista de teléfonos de emergencia."
    ],
    "Coche": [
        "Chaleco, triángulos, linterna, manta térmica.",
        "Botiquín básico (guantes, gasas, vendas, antiséptico).",
        "Agua, barritas energéticas, navaja multiusos.",
        "Cargador móvil y power bank."
    ],
    "Montaña": [
        "Manta térmica, silbato, frontal, encendedor.",
        "Vendas elásticas, férula ligera, tiritas, antiséptico.",
        "Sales de rehidratación, comida energética, agua extra.",
        "Mapa/GPX offline, navaja, cordino."
    ]
}

APA_TEXT = (
    "APA – Asegurar la escena · Proteger a la víctima · Avisar al 112.\\n"
    "1) Asegura el entorno (peligros eléctricos, tráfico, fuego).\\n"
    "2) Protégete y protege a la víctima (guantes si es posible, posición segura).\\n"
    "3) Llama al 112 y describe clara y brevemente la situación.\\n"
    "Añade respiración 4‑4‑4: inhala 4s, retén 4s, exhala 4s (3 ciclos)."
)

# =========================
# MANIFIESTO DE MEDIOS (fotos y vídeos) — Rellena 'url' o 'path' cuando tengas material
# =========================
MEDIA = {
    "Atragantamiento (adulto)": {
        "images": [
            {"title": "Golpes interescapulares", "url": "", "path": "assets/atragantamiento/golpes.jpg"},
            {"title": "Compresión abdominal (Heimlich)", "url": "", "path": "assets/atragantamiento/heimlich.jpg"},
        ],
        "videos": [
            {"title": "Secuencia completa (demo)", "url": "", "path": "assets/atragantamiento/atragantamiento_demo.mp4"},
        ],
    },
    "Quemadura térmica": {
        "images": [
            {"title": "Enfriado con agua", "url": "", "path": "assets/quemaduras/enfriar.jpg"},
        ],
        "videos": [
            {"title": "Qué NO hacer con quemaduras", "url": "", "path": "assets/quemaduras/evitar.mp4"},
        ],
    },
    "Desmayo (síncope)": {"images": [], "videos": []},
    "Parada cardiorrespiratoria": {
        "images": [
            {"title": "Compresiones 100–120/min", "url": "", "path": "assets/rcp/compresiones.jpg"},
            {"title": "DEA: colocación parches", "url": "", "path": "assets/rcp/dea_parches.jpg"},
        ],
        "videos": [
            {"title": "DEA: pasos guiados", "url": "", "path": "assets/rcp/dea_pasos.mp4"},
        ],
    },
    "Hemorragias": {
        "images": [{"title": "Presión directa", "url": "", "path": "assets/hemorragias/presion.jpg"}],
        "videos": [{"title": "Torniquete (criterios)", "url": "", "path": ""}],
    },
    "Convulsiones": {"images": [], "videos": []},
    "Intoxicaciones": {"images": [], "videos": []},
    "Traumatismos": {"images": [], "videos": []},
}

# =========================
# Utilidades de VOZ (Web Speech API en el navegador)
# =========================
def tts_button(label, text):
    html(f"""
    <button id="speakBtn" style="padding:8px 12px;border:1px solid #ccc;border-radius:8px;cursor:pointer">{label}</button>
    <script>
      const text = {text!r};
      const btn = document.getElementById("speakBtn");
      if (btn) {{
        btn.onclick = () => {{
          const u = new SpeechSynthesisUtterance(text);
          u.lang = "es-ES";
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(u);
        }};
      }}
    </script>
    """, height=40)

def stt_widget():
    st.caption("🎙️ Usa Chrome/Edge. Pulsa *Escuchar*, habla y *Parar* para usar el texto.")
    stt_code = """
    <div>
      <button id="startRec" style="padding:8px 12px;border:1px solid #ccc;border-radius:8px;margin-right:8px;cursor:pointer">🎙️ Escuchar</button>
      <button id="stopRec" style="padding:8px 12px;border:1px solid #ccc;border-radius:8px;cursor:pointer">■ Parar</button>
      <p id="sttStatus" style="font-family:system-ui, sans-serif; font-size:14px; color:#444;margin-top:8px;"></p>
      <textarea id="sttOut" rows="2" style="width:100%;margin-top:6px;" placeholder="Transcripción de voz…"></textarea>
    </div>
    <script>
      const status = document.getElementById('sttStatus');
      const out = document.getElementById('sttOut');
      let rec, finalText = "";
      function supported() { return ('webkitSpeechRecognition' in window) || ('SpeechRecognition' in window); }
      function getRec() {
        const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition;
        const r = new Ctor();
        r.lang = 'es-ES';
        r.continuous = true;
        r.interimResults = true;
        r.onresult = (e) => {
          let interim = "";
          for (let i = e.resultIndex; i < e.results.length; i++) {
            const t = e.results[i][0].transcript;
            if (e.results[i].isFinal) finalText += t;
            else interim += t;
          }
          out.value = (finalText + " " + interim).trim();
        };
        r.onerror = (e)=>{ status.innerText = "Error: " + e.error; };
        r.onend = ()=>{ status.innerText = "Reconocimiento detenido."; };
        return r;
      }
      if (!supported()) { status.innerText = "⚠️ Tu navegador no soporta reconocimiento de voz."; }
      document.getElementById('startRec').onclick = () => {
        if (!supported()) return;
        finalText = "";
        rec = getRec(); rec.start();
        status.innerText = "🎧 Escuchando…";
      };
      document.getElementById('stopRec').onclick = () => {
        if (rec) rec.stop(); status.innerText = "⏹️ Parado.";
      };
    </script>
    """
    html(stt_code, height=200)
    return st.text_input("👉 (Opcional) Pega o edita el texto reconocido:", key="stt_input")

# =========================
# Bloque reutilizable de medios
# =========================
def media_block(title_key: str):
    st.markdown("#### 📷 Fotos y 🎬 Vídeos")
    data = MEDIA.get(title_key, {"images": [], "videos": []})
    imgs = data.get("images", [])
    vids = data.get("videos", [])

    # Imágenes
    if imgs:
        cols = st.columns(min(3, len(imgs)))
        for i, item in enumerate(imgs):
            with cols[i % len(cols)]:
                src_url = item.get("url")
                src_path = item.get("path")
                title = item.get("title", "")
                if src_url:
                    st.image(src_url, caption=title, use_container_width=True)
                elif src_path and os.path.exists(src_path):
                    st.image(src_path, caption=title, use_container_width=True)
                else:
                    st.info(f"📄 Placeholder — {title} (pendiente)")
    else:
        st.info("Aún no hay imágenes. Añádelas en MEDIA['...']['images'].")

    # Vídeos
    if vids:
        for v in vids:
            t = v.get("title", "Vídeo")
            url = v.get("url")
            path = v.get("path")
            st.markdown(f"**{t}**")
            if url:
                st.video(url)
            elif path and os.path.exists(path):
                st.video(path)
            else:
                st.info("🎬 Placeholder de vídeo (pendiente)")
    else:
        st.info("Aún no hay vídeos. Añádelos en MEDIA['...']['videos'].")

    with st.expander("➕ Añadir material rápido para la demo (no persistente)"):
        up_imgs = st.file_uploader("Sube imágenes", type=["png","jpg","jpeg"], accept_multiple_files=True, key=f"upimg_{title_key}")
        up_vids = st.file_uploader("Sube vídeos", type=["mp4","mov","webm"], accept_multiple_files=True, key=f"upvid_{title_key}")
        if up_imgs:
            st.success(f"Imágenes cargadas: {len(up_imgs)}")
            for f in up_imgs:
                st.image(f, caption=f.name, use_container_width=True)
        if up_vids:
            st.success(f"Vídeos cargados: {len(up_vids)}")
            for f in up_vids:
                st.video(f)

    # Subida rápida para demo (no persiste)
    with st.expander("➕ Añadir material rápido para la demo (no persistente)"):
        up_imgs = st.file_uploader("Sube imágenes", type=["png","jpg","jpeg"], accept_multiple_files=True, key=f"upimg_{title_key}")
        up_vids = st.file_uploader("Sube vídeos", type=["mp4","mov","webm"], accept_multiple_files=True, key=f"upvid_{title_key}")
        if up_imgs:
            st.success(f"Imágenes cargadas: {len(up_imgs)}")
            for f in up_imgs:
                st.image(f, caption=f.name, use_container_width=True)
        if up_vids:
            st.success(f"Vídeos cargados: {len(up_vids)}")
            for f in up_vids:
                st.video(f)

def zip_scenario_assets(scenario: str) -> bytes:
    """Crea un ZIP en memoria con los ficheros locales del escenario."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        media = MEDIA.get(scenario, {})
        for item in media.get("images", []) + media.get("videos", []):
            p = item.get("path")
            if p and os.path.exists(p):
                z.write(p, arcname=os.path.basename(p))
    buf.seek(0)
    return buf.read()

# =========================
# Cabecera
# =========================
col_logo, col_title = st.columns([0.15, 0.85])
with col_logo:
    # Coloca tu logo en assets/evolve_logo.png
    if os.path.exists("assets/evolve_logo.png"):
        st.image("assets/evolve_logo.png", width=96)
with col_title:
    st.title("🆘 ConRumbo – MVP de Primeros Auxilios")
    st.markdown("Asistente accionable: **botón de emergencia**, **chat + voz**, **material descargable**, **fotos/vídeos**.")
st.caption("Demo educativa – No sustituye formación sanitaria ni la atención profesional.")

# =========================
# Navegación (pestañas arriba)
# =========================
tabs = st.tabs([
    "🆘 Emergencias inmediatas",
    "💉 Primeros auxilios",
    "🎒 Kits de supervivencia",
    "📊 Progreso",
    "😌 Mantén la calma (APA)",
    "🤖 Chat (voz y texto)",
    "🗂️ Centro de medios"
])

with st.sidebar:
    st.markdown("### 📥 Descargas técnicas")
    try:
        import inspect
        current_script = inspect.getsourcefile(lambda: None) or __file__
        if os.path.exists(current_script):
            with open(current_script, "rb") as f:
                st.download_button("Descargar app.py", f.read(), file_name="app.py", mime="text/x-python", use_container_width=True)
    except Exception as e:
        st.caption(f"No se pudo preparar la descarga del script: {e}")

    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "rb") as f:
            st.download_button("Descargar requirements.txt", f.read(), file_name="requirements.txt", mime="text/plain", use_container_width=True)

# =========================
# 1) EMERGENCIAS INMEDIATAS
# =========================
with tabs[0]:
    st.subheader("🚨 Botón de emergencia")
    left, right = st.columns([0.58, 0.42])
    with left:
        if st.button("🆘 ACTIVAR / SALIR MODO EMERGENCIA", use_container_width=True):
            st.session_state.emergency_mode = not st.session_state.emergency_mode
            if not st.session_state.emergency_mode:
                st.session_state.scenario = None
                st.session_state.step_idx = 0

        st.session_state.scenario = st.selectbox(
            "Selecciona el tipo de emergencia",
            ["—", *SCENARIOS.keys()],
            index=0 if not st.session_state.scenario
            else ["—", *SCENARIOS.keys()].index(st.session_state.scenario)
        )

        if st.session_state.emergency_mode and st.session_state.scenario in SCENARIOS:
            steps = SCENARIOS[st.session_state.scenario]
            st.success(f"**{st.session_state.scenario}** · Paso {st.session_state.step_idx+1} de {len(steps)}")
            current_text = steps[st.session_state.step_idx]
            st.markdown(f"### ✅ Instrucción\n{current_text}")
            tts_button("🔊 Leer en voz alta", f"{st.session_state.scenario}. {current_text}")

            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("⟸ Anterior", disabled=st.session_state.step_idx == 0, use_container_width=True):
                    st.session_state.step_idx -= 1
            with b2:
                if st.button("⟲ Reiniciar", use_container_width=True):
                    st.session_state.step_idx = 0
            with b3:
                if st.button("Siguiente ⟹", disabled=st.session_state.step_idx == len(steps)-1, use_container_width=True):
                    st.session_state.step_idx += 1

            st.info("Si la situación es grave o dudas: **llama al 112**.")
            st.markdown("---")
            media_block(st.session_state.scenario)
        else:
            st.info("Pulsa **ACTIVAR** y elige un escenario para iniciar la guía.")

    with right:
        st.markdown("#### ⬇️ Descargas del escenario")
        if st.session_state.scenario in SCENARIOS:
            txt = f"# {st.session_state.scenario}\n\n" + "\n".join([f"- {s}" for s in SCENARIOS[st.session_state.scenario]])
            download_button("Descargar guía (.md)", txt, f"ConRumbo_{st.session_state.scenario.replace(' ','_')}.md")

            # ZIP de material (si hay ficheros locales disponibles)
            if st.button("📦 Preparar material (ZIP)"):
                data = zip_scenario_assets(st.session_state.scenario)
                if data:
                    st.download_button(
                        "Descargar ZIP",
                        data=data,
                        file_name=f"ConRumbo_{st.session_state.scenario.replace(' ','_')}_media.zip",
                        mime="application/zip",
                    )
                else:
                    st.warning("No hay archivos locales en assets/ para este escenario todavía.")

    st.session_state.progress["Emergencias"] = True

# =========================
# 2) PRIMEROS AUXILIOS
# =========================
with tabs[1]:
    st.subheader("💉 Guías esenciales")
    for titulo, pasos in PRIMEROS_AUX.items():
        with st.expander(f"📄 {titulo}", expanded=False):
            st.markdown("\n".join([f"- {p}" for p in pasos]))
            txt = f"# {titulo}\n\n" + "\n".join([f"- {p}" for p in pasos])
            download_button(f"Descargar {titulo} (.md)", txt, f"ConRumbo_{titulo.replace(' ','_')}.md")
            st.markdown("---")
            media_block(titulo)
    st.session_state.progress["Primeros auxilios"] = True

# =========================
# 3) KITS DE SUPERVIVENCIA
# =========================
with tabs[2]:
    st.subheader("🎒 Listas recomendadas")
    cols = st.columns(3)
    for i, (kit, items) in enumerate(KITS.items()):
        with cols[i]:
            st.markdown(f"### {kit}")
            st.markdown("\n".join([f"- {it}" for it in items]))
            txt = f"# Kit de supervivencia – {kit}\n\n" + "\n".join([f"- {it}" for it in items])
            download_button(f"Descargar {kit} (.md)", txt, f"ConRumbo_Kit_{kit.replace(' ','_')}.md")
    st.session_state.progress["Kits de supervivencia"] = True

# =========================
# 4) PROGRESO
# =========================
with tabs[3]:
    st.subheader("📊 Tu progreso")
    done_count = 0
    total = len(st.session_state.progress)
    for k in list(st.session_state.progress.keys()):
        st.session_state.progress[k] = st.checkbox(k, value=st.session_state.progress[k])
        done_count += 1 if st.session_state.progress[k] else 0

    pct = int(100 * done_count / total)
    st.progress(pct / 100)
    st.write(f"**Completado: {pct}%**")

    df = pd.DataFrame(
        [{"Módulo": k, "Completado": v, "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")} for k, v in st.session_state.progress.items()]
    )
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exportar progreso (.csv)", data=csv, file_name="ConRumbo_progreso.csv", mime="text/csv")

# =========================
# 5) MANTÉN LA CALMA (APA)
# =========================
with tabs[4]:
    st.subheader("😌 Mantén la calma (APA)")
    st.markdown(
        "**APA** = **Asegurar** la escena · **Proteger** a la víctima · **Avisar** al 112.\n\n" +
        APA_TEXT.replace("\n", "<br>"),
        unsafe_allow_html=True
    )

    st.markdown("#### 🫁 Respiración 4‑4‑4 (guía por voz)")
    tts_button("🔊 Escuchar rutina", "Inhala cuatro segundos. Mantén cuatro. Exhala cuatro. Repite tres ciclos. Mantén la calma. Actúa con seguridad.")
    download_button("Descargar rutina APA (.md)", "# APA – Mantén la calma\n\n" + APA_TEXT, "ConRumbo_APA.md")

    st.session_state.progress["Mantén la calma (APA)"] = True

# =========================
# 6) CHAT (voz y texto)
# =========================
with tabs[5]:
    st.subheader("🤖 Chat de preguntas (voz y texto)")
    st.caption("Describe la situación: *“se está atragantando y no respira”*, *“hay una quemadura con aceite”*, etc.")

    INTENTS = {
        "atragant": "Parece **atragantamiento**. Si no puede toser/hablar: 112, 5 golpes interescapulares y 5 Heimlich, alternando. Si pierde consciencia, inicia RCP.",
        "quemad": "Para **quemaduras**: enfría 15–20 min con agua templada (no hielo), cubre con paño estéril, no revientes ampollas. Si es extensa/química/eléctrica: 112.",
        "desmay": "Para **desmayo**: tumbar, elevar piernas, vigilar respiración. Si no recupera en 1–2 min o hay signos graves: 112.",
        "rcp|parada|no respira|sin respirar": "Si **no respira**: 112 y **RCP**. 30 compresiones a 100–120/min (5–6 cm), 2 ventilaciones si sabes; si no, solo compresiones. Usa DEA si hay.",
        "corte|hemorrag": "Para **hemorragias**: presión directa 10 min, eleva miembro. Si no cede o es abundante: 112.",
        "intoxic": "En **intoxicaciones**: no provoques el vómito. Identifica sustancia/tiempo. Dificultad respiratoria, convulsiones o niños: 112.",
        "convul": "En **convulsiones**: protege cabeza, no sujetes, nada en la boca, controla tiempo. Si >5 min o repetidas: 112.",
        "trauma|golpe": "En **traumatismos**: inmoviliza, hielo envuelto 10–15 min, 112 si dolor intenso, deformidad o cabeza/cuello."
    }
    FAQ = {
        "112": "En España y la UE, el **112** es el número único de emergencias.",
        "dea": "El DEA guía por voz: enciéndelo, coloca parches como indica, no toques al analizar/descargar.",
        "guantes": "Usa **guantes** si puedes. Lávate manos tras asistir y evita contacto con fluidos."
    }

    def route_message(msg: str) -> str:
        low = msg.lower()
        for key, resp in INTENTS.items():
            if re.search(key, low):
                return resp
        for key, resp in FAQ.items():
            if key in low:
                return resp
        return ("No estoy seguro. Si hay peligro vital, **llama al 112**. "
                "Dime: ¿respira con normalidad? ¿está consciente? ¿hay sangrado, quemadura o atragantamiento?")

    # Historial
    for role, text in st.session_state.chat_history:
        st.markdown(f"**{'👤 Tú' if role=='user' else '🤖 ConRumbo'}:** {text}")

    voice_text = stt_widget()
    user_msg = st.text_input("Escribe tu mensaje:", key="chat_input", placeholder="Describe la situación…")

    csend1, csend2 = st.columns([0.55, 0.45])
    with csend1:
        send = st.button("Enviar", use_container_width=True)
    with csend2:
        if voice_text and st.button("Usar texto de voz y enviar", use_container_width=True):
            user_msg = voice_text
            send = True

    if send and user_msg:
        st.session_state.chat_history.append(("user", user_msg))
        bot_resp = route_message(user_msg)
        st.session_state.chat_history.append(("bot", bot_resp))
        with st.expander("🔊 Leer última respuesta"):
            tts_button("Reproducir", bot_resp)
        st.rerun()

# =========================
# 7) CENTRO DE MEDIOS
# =========================
with tabs[6]:
    st.subheader("🗂️ Centro de medios (resumen)")
    faltantes = []
    for k, v in MEDIA.items():
        st.markdown(f"### {k}")
        imgs_all = v.get("images", [])
        vids_all = v.get("videos", [])
        imgs_ok = [i for i in imgs_all if i.get("url") or i.get("path")]
        vids_ok = [i for i in vids_all if i.get("url") or i.get("path")]
        st.write(f"Imágenes configuradas: {len(imgs_ok)} / {len(imgs_all)}")
        st.write(f"Vídeos configurados: {len(vids_ok)} / {len(vids_all)}")
        if len(imgs_ok) < len(imgs_all) or len(vids_ok) < len(vids_all):
            faltantes.append(k)
        st.markdown("---")
    if faltantes:
        st.warning("Faltan medios en: " + ", ".join(faltantes))
    else:
        st.success("¡Todo el material está asignado!")

# =========================
# 8) Descargas técnicas (sidebar)
# =========================
with st.sidebar:
    st.markdown("### 📥 Descargas técnicas")
    try:
        import inspect
        current_script = inspect.getsourcefile(lambda: None) or __file__
        if os.path.exists(current_script):
            with open(current_script, "rb") as f:
                st.download_button(
                    "Descargar app.py",
                    data=f.read(),
                    file_name="app.py",
                    mime="text/x-python",
                    use_container_width=True
                )
    except Exception as e:
        st.caption(f"No se pudo preparar la descarga del script: {e}")

    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "rb") as f:
            st.download_button(
                "Descargar requirements.txt",
                data=f.read(),
                file_name="requirements.txt",
                mime="text/plain",
                use_container_width=True
            )
        
# Pie
st.divider()
st.caption("⚠️ MVP demostrativo/educativo. No sustituye la formación en primeros auxilios ni la atención profesional.")
