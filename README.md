# ConRumbo — MVP de primeros auxilios guiados

**Autor:** *Valentina Bailon* · **Máster:** *EVOLVE MÁSTER* · **Logo:** *(coloca `assets/logo_evolve.png`)*

ConRumbo es una aplicación en **Streamlit** que ayuda a actuar con rapidez y calma ante una emergencia.
Incluye guías de **emergencias inmediatas**, **primeros auxilios** paso a paso con **fotos y vídeos** (placeholders),
**kits de supervivencia**, **seguimiento de progreso**, un módulo de **apoyo psicológico (APA)** y un **chatbot**
que ofrece instrucciones por texto y **voz**. Dispone de un **botón de emergencia** para llamar al **112**
(o el número configurado) y opciones de descarga de material en PDF/imagen.

> ⚠️ **Descargo de responsabilidad:** ConRumbo **no sustituye atención médica profesional**. En situaciones
> graves llama al **112** de inmediato. El contenido es educativo.

---

## 1.Estructura del proyecto

```
conrumbo/
├─ main.py                    # App principal (Streamlit)
├─ requirements.txt           # Dependencias núcleo (chat + TTS + descargas)
├─ requirements-voice.txt     # Dependencias opcionales para entrada de voz
├─ README.md                  # Este documento
├─ .gitignore
├─ .env.example               # Variables opcionales (Twilio/SMS, etc.)
├─ pages/                     # Páginas secundarias (si usas multipage)
├─ modules/                   # Lógica por módulos (emergencias, kits, etc.)
│  ├─ emergencies.py
│  ├─ first_aid.py
│  ├─ kits.py
│  ├─ progress.py
│  └─ calm_apa.py
├─ assets/
│  ├─ emergencies/
│  │  ├─ atragantamiento/
│  │  │  ├─ fotos/       # .jpg/.png
│  │  │  └─ videos/      # .mp4 (placeholders)
│  │  └─ hemorragia/ ...
│  ├─ first_aid/
│  └─ kits/
└─ downloads/                 # Archivos generados para descargar (PDF, listas, etc.)
```

> Los medios (fotos y vídeos) irán **dentro de cada protocolo** en su carpeta correspondiente.
> Puedes empezar con placeholders y sustituir por tus archivos reales más tarde.

---

## 2. Pasos (VS Code – Terminal integrada)

### 2.1. Crear y activar entorno virtual
**Windows (PowerShell):**
```powershell
cd rutal\proyecto\conrumbo
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

**macOS / Linux (bash/zsh):**
```bash
cd ruta/al/proyecto/conrumbo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 2.2. Instalar dependencias núcleo y ejecutar
```bash
pip install -r requirements.txt
streamlit run main.py
```

### 2.3. (Opcional) Habilitar **entrada de voz** (micrófono)
La salida por voz (TTS) ya está en `requirements.txt`. Para **dictado** por voz:

1. Instala dependencias extra:
   ```bash
   pip install -r requirements-voice.txt
   ```
2. Descarga un **modelo Vosk** (ES pequeño) y colócalo en `models/vosk-es/`:
   - https://alphacephei.com/vosk/models (elige *small es*).  
3. En `main.py`, activa el modo voz marcando el *toggle* de “Entrada por voz (beta)”.

> Nota: en Windows puede requerir *build tools* para `aiortc/av`. Si prefieres algo más sencillo,
> mantén **solo salida de voz (TTS)** que funciona out‑of‑the‑box.

---

## 3. Git y GitHub (organización profesional)

```bash
git init
git add .
git commit -m "feat: ConRumbo MVP inicial"
# Crea un repo vacío en GitHub llamado conrumbo y enlázalo:
git branch -M main
git remote add origin https://github.com/<tu_usuario>/conrumbo.git
git push -u origin main
```

Sugerencias para un repo limpio:
- Usa ramas: `feat/voice`, `feat/emergency-button`, `fix/ui`.
- Issues/Projects para tareas.
- Releases etiquetadas: `v0.1.0-mvp`, etc.
- Añade **MIT LICENSE** si es personal.

---

## 4. Cómo añadir **medios** (fotos/vídeos)

- Coloca archivos en `assets/<modulo>/<protocolo>/{fotos|videos}`.
- En `main.py` se muestran automáticamente si existen.
- Formatos recomendados: `.png/.jpg` para imágenes, `.mp4` (H.264) para vídeo.
- Nombra archivos de forma clara: `paso1_colocar-mano.png`, `paso2_compresion.mp4`.

---

## 5. Funcionalidades del MVP (incluidas)

- 🆘 **Emergencias inmediatas** (botón directo **112** — móvil `tel:112`).
- 💉 **Primeros auxilios** con pasos claros, checklists y **voz TTS**.
- 🎒 **Kits de supervivencia** (hogar, coche, montaña) + descarga en PDF.
- 📊 **Progreso** (módulos completados) con persistencia en cookies/local storage.
- 😌 **Mantén la calma (APA)**: respiración guiada, grounding 5‑4‑3‑2‑1, temporizadores.
- 🤖 **Chatbot**: modo **texto** y **voz (salida)**; **entrada por voz (opcional/beta)**.
- ⬇️ **Descarga de material** (PDF/PNG) generado desde la app.

---

## 6. Variables de entorno (opcional)

Crea un `.env` (o usa `.env.example`) si deseas SMS/WhatsApp o emails:
```
# Twilio (opcional)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM=whatsapp:+14155238886
EMERGENCY_TO=whatsapp:+34XXXXXXXXX

# Correo (opcional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
```

> Si no configuras proveedores, el **botón de emergencia** utilizará `tel:112` (ideal en móvil) y recordará la
> recomendación de **llamar primero**.

---

## 7. Ejecutar pruebas manuales

1. Abrir `streamlit run main.py`.
2. Navegar por cada módulo, marcar pasos como completados y comprobar que se guardan.
3. Probar el **botón 112** desde móvil.
4. Generar una lista PDF desde “Kits” y descargar.
5. Probar **TTS** (voz) en “Primeros auxilios” y en el **Chatbot**.
6. (Opcional) Activar **entrada por voz** si instalaste `requirements-voice.txt` y el modelo Vosk.

---

## 8. Despliegue (opciones)

- **Streamlit Community Cloud**: conecta tu repo, define `main.py` como *entry point*.
- **Railway/Render**: crea servicio Python con `streamlit run main.py`.
- **Docker** (opcional): genera imagen con `EXPOSE 8501` y CMD de streamlit.

---

## 9. Indicaciones de diseño / personalización

- Muestra solo **tu nombre** (personaliza la pantalla “Sobre mí”).  
- Usa el **logo de EVOLVE** en el *header* (`assets/logo_evolve.png`).  
- Paleta calmada (azules/verde menta), tipografía legible, botones grandes.

---

## 10. Roadmap después del MVP

- Geolocalización y envío de ubicación en SMS/WhatsApp (si se configura Twilio).
- Modo **offline** (caché de guías e imágenes).
- Validación clínica del contenido por profesional sanitario.
- Localización EN/FR/IT.

---

## 11. FAQ

**¿Puedo usarlo sin internet?** Sí para la interfaz y TTS local; los vídeos hospedados externos requieren conexión.  
**¿La entrada por voz es obligatoria?** No, es opcional. El TTS (salida de voz) es parte del núcleo.  
**¿Puedo añadir mis vídeos/fotos?** Sí, sustituye los placeholders en `assets/`.

---

## 12. Licencia

MIT (sugerida). Añade tu archivo `LICENSE` en la raíz del repo.
