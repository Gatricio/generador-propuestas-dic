import os
import time
import re
import datetime
from io import BytesIO
import streamlit as st
from docxtpl import DocxTemplate
from google import genai
from google.genai import types

# Configuración inicial de Streamlit
st.set_page_config(
    page_title="IDIEM - Generador de Propuestas",
    page_icon="📄",
    layout="wide"
)

# Estilos corporativos IDIEM
st.markdown("""
    <style>
    .main-header { font-size:24px; font-weight:bold; color:#002855; margin-bottom:2px; }
    .sub-header { font-size:14px; color:#555; margin-bottom: 20px; }
    .stButton>button { background-color: #0056B3; color: white; font-weight: bold; width: 100%; }
    .plazo-card {
        background-color: #F0F4F8;
        border-left: 5px solid #002855;
        padding: 15px 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# OBTENCIÓN DE MÚLTIPLES API KEYS Y MODELOS DESDE SECRETS
# ---------------------------------------------------------
def obtener_configuracion_gemini():
    keys = []
    models = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
    ]

    if "gemini" in st.secrets:
        gemini_sec = st.secrets["gemini"]
        if "api_keys" in gemini_sec and isinstance(gemini_sec["api_keys"], list):
            keys = [k.strip() for k in gemini_sec["api_keys"] if k.strip()]
        if "models" in gemini_sec and isinstance(gemini_sec["models"], list):
            models = [m.strip() for m in gemini_sec["models"] if m.strip()]

    elif "GEMINI_API_KEYS" in st.secrets:
        raw_keys = st.secrets["GEMINI_API_KEYS"]
        if isinstance(raw_keys, list):
            keys = [k.strip() for k in raw_keys if k.strip()]

    if not keys:
        single_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
        if single_key:
            keys = [single_key.strip()]

    return keys, models

api_keys, modelos_disponibles = obtener_configuracion_gemini()

# ---------------------------------------------------------
# FUNCIONES PARA EXTRACCIÓN DE TEXTO DE ARCHIVOS
# ---------------------------------------------------------
def extraer_texto_pdf(file_bytes):
    try:
        import pypdf
        pdf_reader = pypdf.PdfReader(BytesIO(file_bytes))
        texto = ""
        for page in pdf_reader.pages:
            texto += page.extract_text() or ""
        return texto
    except Exception as e:
        return f"[Error al leer PDF: {str(e)}]"

def extraer_texto_docx(file_bytes):
    try:
        import docx
        doc = docx.Document(BytesIO(file_bytes))
        texto = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return texto
    except Exception as e:
        return f"[Error al leer DOCX: {str(e)}]"

# ---------------------------------------------------------
# FUNCIÓN DE LIMPIEZA DE FORMATO MARKDOWN Y SUBCAPÍTULOS
# ---------------------------------------------------------
def limpiar_formato_texto(texto):
    if not texto:
        return ""
    texto = texto.replace("**", "").replace("*", "")
    texto = re.sub(r'#+\s*', '', texto)
    texto = re.sub(r'^\s*\d+(\.\d+)+\s*', '', texto, flags=re.MULTILINE)
    return texto.strip()

# ---------------------------------------------------------
# PROMPT DEL SISTEMA Y LLAMADA A GEMINI LOTE COMPLETO
# ---------------------------------------------------------
SYSTEM_GUARDRAILS_IDIEM = """
Eres un Ingeniero Especialista Senior de la División de Ingeniería Contractual de IDIEM (Universidad de Chile).
Tu objetivo es redactar propuestas técnicas e informes con el máximo rigor de ingeniería, neutralidad y objetividad.

REGLAS DE ORO DE REDACCIÓN Y FORMATO:
1. ANCLAJE ESTRICTO A LOS ANTECEDENTES Y DOCUMENTOS: Utiliza EXCLUSIVAMENTE la información proporcionada en las notas del usuario y los archivos adjuntos cargados. NO inventes hechos ni asumas datos no documentados.
2. NEUTRALIDAD TÉCNICA ABSOLUTA: Mantén un lenguaje neutral, empírico e imparcial. Prohibido usar calificativos acusatorios o legales (ej: sustituye 'incumplimiento grave' por 'desviación de la línea base').
3. PROHIBICIÓN DE ANÁLISIS O CITAS JURÍDICAS/NORMATIVAS: Mantén el foco 100% en ingeniería civil y contractual. Queda estrictamente prohibido citar artículos de leyes, códigos legales, jurisprudencia o emitir juicios de derecho. Limítate a evaluar aspectos técnicos, físicos, financieros, presupuestarios y de plazo.
4. ESTRUCTURA EN PÁRRAFOS CONTINUOS: Redacta exclusivamente en párrafos formales de ingeniería continuos y fluídos. Queda ESTRICTAMENTE PROHIBIDO el uso de subcapítulos (ej: 4.1, 4.2), títulos secundarios, encabezados (#, ##, ###) o caracteres de formato Markdown como asteriscos de negrita (**).
5. ESTÁNDAR IDIEM: Redacción ejecutiva, clara y en español formal. Queda estrictamente prohibido entregar notas internas, explicaciones de trabajo, razonamientos o textos en inglés.
"""

def crear_cache_contexto_si_aplica(client, modelo, texto_documentos):
    if len(texto_documentos) < 100000:
        return None
    
    try:
        cache = client.caches.create(
            model=modelo,
            config=types.CreateCachedContentConfig(
                contents=[f"DOCUMENTOS DE RESPALDO Y EXPEDIENTES SUBIDOS:\n{texto_documentos}"],
                system_instruction=SYSTEM_GUARDRAILS_IDIEM,
                ttl="1800s"
            )
        )
        return cache
    except Exception:
        return None

def llamar_ia_gemini(prompt_tarea, notas_usuario, texto_adjuntos):
    if not api_keys:
        return "⚠️ Error: No se encontraron API Keys configuradas en st.secrets."

    ultimo_error = ""

    for key in api_keys:
        try:
            client_temp = genai.Client(api_key=key)
            for nombre_modelo in modelos_disponibles:
                intentos = 0
                max_intentos = 5
                
                usar_cache = len(texto_adjuntos) >= 100000
                cache_obj = None

                if usar_cache and ("cache_name" not in st.session_state or not st.session_state.cache_name):
                    cache_obj = crear_cache_contexto_si_aplica(client_temp, nombre_modelo, texto_adjuntos)
                    if cache_obj:
                        st.session_state.cache_name = cache_obj.name

                while intentos < max_intentos:
                    try:
                        if usar_cache and st.session_state.get("cache_name"):
                            prompt_final = f"TAREA A REALIZAR:\n{prompt_tarea}\n\nNOTAS ADICIONALES DEL INGENIERO:\n{notas_usuario}"
                            config_gen = types.GenerateContentConfig(
                                cached_content=st.session_state.cache_name,
                                temperature=0.2,
                                max_output_tokens=2500,
                            )
                        else:
                            contexto_acotado = texto_adjuntos[:25000] if len(texto_adjuntos) > 25000 else texto_adjuntos
                            prompt_final = f"TAREA A REALIZAR:\n{prompt_tarea}\n\nNOTAS DEL INGENIERO:\n{notas_usuario}\n\nDOCUMENTOS DE RESPALDO:\n{contexto_acotado}"
                            config_gen = types.GenerateContentConfig(
                                system_instruction=SYSTEM_GUARDRAILS_IDIEM,
                                temperature=0.2,
                                max_output_tokens=2500,
                            )

                        response = client_temp.models.generate_content(
                            model=nombre_modelo,
                            contents=prompt_final,
                            config=config_gen
                        )

                        if response and response.text:
                            return limpiar_formato_texto(response.text)

                    except Exception as model_err:
                        err_msg = str(model_err)
                        ultimo_error = err_msg

                        if "503" in err_msg or "UNAVAILABLE" in err_msg or "overloaded" in err_msg.lower() or "high demand" in err_msg.lower():
                            intentos += 1
                            time.sleep(3 * intentos)
                            continue

                        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                            break

                        break
        except Exception as key_err:
            ultimo_error = str(key_err)
            continue

    return f"⚠️ Error al conectar con Gemini API (Claves o modelos agotados): {ultimo_error}"

# ---------------------------------------------------------
# FUNCIÓN: CONVERSIÓN DE NÚMEROS A PALABRAS EN ESPAÑOL (UF)
# ---------------------------------------------------------
def numero_a_palabras_uf(n):
    n = int(round(n))
    if n == 0:
        return "cero"

    unidades = ["", "un", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
    especiales = ["diez", "once", "doce", "trece", "catorce", "quince", "diecisiete", "dieciocho", "diecinueve"]
    decenas = ["", "diez", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
    centenas = ["", "ciento", "doscientas", "trescientas", "cuatrocientas", "quinientas", "seiscientas", "setecientas", "ochocientas", "novecientas"]

    def convert_group(n):
        if n == 0:
            return ""
        elif n < 10:
            return unidades[n]
        elif n < 20:
            return especiales[n - 10]
        elif n < 30:
            if n == 20:
                return "veinte"
            return "veinti" + unidades[n - 20]
        elif n < 100:
            u = n % 10
            d = n // 10
            return decenas[d] + (" y " + unidades[u] if u > 0 else "")
        elif n < 1000:
            if n == 100:
                return "cien"
            c = n // 100
            rest = n % 100
            return centenas[c] + (" " + convert_group(rest) if rest > 0 else "")
        return ""

    if n < 1000:
        res = convert_group(n)
    elif n < 1000000:
        miles = n // 1000
        rest = n % 1000
        str_miles = "mil" if miles == 1 else convert_group(miles) + " mil"
        str_rest = convert_group(rest)
        res = str_miles + (" " + str_rest if str_rest else "")
    else:
        millones = n // 1000000
        rest = n % 1000000
        str_mill = "un millón" if millones == 1 else convert_group(millones) + " millones"
        str_rest = numero_a_palabras_uf(rest) if rest > 0 else ""
        res = str_mill + (" " + str_rest if str_rest else "")

    return res.strip()

# ---------------------------------------------------------
# SISTEMA DE AUTENTICACIÓN / LOGIN
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_login():
    user = st.session_state.get("input_user", "").strip()
    pwd = st.session_state.get("input_pwd", "").strip()

    if user == "idiem.dic" and pwd == "2343":
        st.session_state.authenticated = True
    else:
        st.session_state.authenticated = False
        st.error("Usuario o contraseña incorrectos.")

if not st.session_state.authenticated:
    st.markdown('<div class="main-header">IDIEM — UNIVERSIDAD DE CHILE</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">División de Ingeniería Contractual | Acceso Privado</div>', unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.subheader("🔒 Iniciar Sesión")
        st.text_input("Usuario:", key="input_user")
        st.text_input("Contraseña:", type="password", key="input_pwd")
        st.button("Ingresar", on_click=check_login)
    st.stop()

# ---------------------------------------------------------
# APLICACIÓN PRINCIPAL
# ---------------------------------------------------------
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.markdown('<div class="main-header">IDIEM — UNIVERSIDAD DE CHILE</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">División de Ingeniería Contractual | Generador Web de Ofertas Técnicas y Peritajes</div>', unsafe_allow_html=True)
with col_logout:
    if st.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Identificación y Tipo",
    "2. Alcance y Contexto",
    "3. Horas Hombre y Perfiles",
    "4. Oferta Económica, Exclusiones y Descarga"
])

# ---------------------------------------------------------
# PESTAÑA 1: IDENTIFICACIÓN Y TIPO
# ---------------------------------------------------------
with tab1:
    st.subheader("Clasificación del Encargo")
    tipo_encargo = st.radio("Tipo de Servicio:", ["Informe Técnico de Parte (Cliente Directo)", "Peritaje Judicial / Arbitral CAM (Designación por Tribunal)"])

    col1, col2 = st.columns(2)
    with col1:
        codigo = st.text_input("Código de Propuesta:", value="", placeholder="Ingrese código PR.DIC...")
        cliente = st.text_input("Cliente / Razón Social o Tribunal:", value="", placeholder="Ingrese razón social del cliente o Tribunal Arbitral...")
        solicitante = st.text_input("Nombre Solicitante / Juez Árbitro:", value="", placeholder="Nombre del solicitante o Sr. Árbitro...")
        cargo_solicitante = st.text_input("Cargo Solicitante:", value="", placeholder="Cargo del solicitante / Juez Árbitro...")
        fecha_emision = st.date_input("Fecha de Emisión:", value=datetime.date.today(), format="DD/MM/YYYY")
    with col2:
        revision = st.text_input("Revisión N°:", value="0")
        rut_cliente = st.text_input("RUT Cliente / Tribunal:", value="", placeholder="RUT...")
        email_solicitante = st.text_input("Email Solicitante:", value="", placeholder="correo@ejemplo.cl")
        telefono_solicitante = st.text_input("Teléfono Solicitante:", value="", placeholder="+56 9 ...")
        rol_cam = st.text_input("Tribunal / Rol Arbitral CAM (Si aplica):", value="", placeholder="Rol CAM N°...")

    nombre_propuesta = st.text_input("Nombre Oficial de la Propuesta / Peritaje:", value="", placeholder="Ej: INFORME TÉCNICO DE PERTINENCIA, IMPACTO EN PLAZO Y EVALUACIÓN DE MAYORES COSTOS...")

# ---------------------------------------------------------
# PESTAÑA 2: ALCANCE Y CONTEXTO
# ---------------------------------------------------------
with tab2:
    st.subheader("Descripción del Conflicto y Carga de Antecedentes")

    if "text_intro" not in st.session_state:
        st.session_state.text_intro = ""
    if "text_alcance" not in st.session_state:
        st.session_state.text_alcance = ""
    if "auto_actividades" not in st.session_state:
        st.session_state.auto_actividades = ""
    if "texto_adjuntos" not in st.session_state:
        st.session_state.texto_adjuntos = ""
    if "cache_name" not in st.session_state:
        st.session_state.cache_name = None

    # --- MÓDULO DE CARGA DE ARCHIVOS DE RESPALDO ---
    st.markdown("#### 📁 Cargar Documentos de Respaldo (Demanda, Correos, EETT, etc.)")
    st.caption("Sube los archivos PDF o DOCX del caso. La IA leerá el contenido para extraer antecedentes técnicos concretos y alimentar la redacción de los capítulos.")

    uploaded_files = st.file_uploader("Seleccione archivos (.pdf, .docx):", type=["pdf", "docx"], accept_multiple_files=True)

    if uploaded_files:
        texto_extraido_total = []
        for file in uploaded_files:
            bytes_data = file.read()
            if file.name.endswith(".pdf"):
                txt = extraer_texto_pdf(bytes_data)
            elif file.name.endswith(".docx"):
                txt = extraer_texto_docx(bytes_data)
            else:
                txt = ""
            texto_extraido_total.append(f"--- INICIO DOCUMENTO: {file.name} ---\n{txt}\n--- FIN DOCUMENTO ---")

        nuevo_texto = "\n\n".join(texto_extraido_total)
        
        if nuevo_texto != st.session_state.texto_adjuntos:
            st.session_state.texto_adjuntos = nuevo_texto
            st.session_state.cache_name = None

        st.success(f"¡Se han procesado {len(uploaded_files)} archivo(s) correctamente!")

    st.markdown("---")

    # --- CAPÍTULO 4: INTRODUCCIÓN ---
    st.markdown("#### 4. Introducción / Contexto de la Obra")

    intro_input = st.text_area(
        "Ingrese antecedentes del contrato, obra y conflicto (o notas preliminares):",
        value=st.session_state.text_intro,
        placeholder="Ingrese borrador o notas del contexto...",
        height=160
    )
    st.session_state.text_intro = intro_input

    if st.button("✨ Pulir y Desarrollar Capítulo 4 (Introducción con Adjuntos)"):
        # Regla de vocabulario según tipo de encargo
        es_peritaje = "Peritaje" in tipo_encargo
        regla_vocabulario = (
            "Utiliza terminología pericial formal (peritaje, perito, dictamen pericial)."
            if es_peritaje else
            "Queda ESTRICTAMENTE PROHIBIDO usar las palabras 'peritaje', 'perito' o 'dictamen'. Utiliza únicamente 'informe técnico', 'estudio técnico', 'revisión contractual' o 'asesoría'."
        )

        notas_combined = f"TIPO DE ENCARGO: {tipo_encargo}\nCLIENTE: {cliente}\nNOMBRE PROPUESTA: {nombre_propuesta}\nNOTAS INGENIERO: {st.session_state.text_intro}"
        prompt_tarea = (
            f"Redacta el Capítulo 4 'Introducción / Contexto de la Obra' integrando los datos técnicos, contractuales y el contexto presente en los documentos subidos. "
            f"REGLA DE VOCABULARIO: {regla_vocabulario} "
            "REGLA DE NO CITAR LEYES: No cites normas legales, artículos de ley ni realices interpretaciones jurídicas. Limítate al contexto técnico-contractual de ingeniería. "
            "REGLA ESTRICTA DE FORMATO: Redacta únicamente en párrafos continuos. Está PROHIBIDO incluir subcapítulos (como 4.1, 4.2), subtítulos, títulos secundarios, caracteres '#' o negritas con '**'."
        )

        if st.session_state.text_intro.strip() or st.session_state.texto_adjuntos.strip():
            with st.spinner("✨ Puliendo e integrando antecedentes en Capítulo 4..."):
                texto_generado = llamar_ia_gemini(prompt_tarea, notas_combined, st.session_state.texto_adjuntos)
                if texto_generado and not texto_generado.startswith("⚠️️"):
                    st.session_state.text_intro = texto_generado
                    st.rerun()

    st.markdown("---")

    # --- CAPÍTULO 5: ALCANCE DETALLADO Y SELECCIÓN DE MATERIAS CON PRIORIDAD ESTABLECIDA ---
    st.markdown("#### 5. Alcance Detallado (Puntos a evaluar / Puntos de Prueba)")

    st.markdown("##### 📌 Seleccione los Alcances Específicos a Evaluar:")
    st.caption("Marque únicamente las materias que aplican. La redacción seguirá estrictamente la secuencia jerárquica de prioridad técnica del 1 al 9.")

    col_chk1, col_chk2, col_chk3, col_chk4 = st.columns(4)
    with col_chk1:
        chk_pertinencia = st.checkbox("1. Estudio de Pertinencia de Situaciones", value=True)
        chk_ingenieria = st.checkbox("2. Estudio Técnico Ingeniería y Arquitectura")
        chk_adicionales = st.checkbox("3. Obras Adicionales / Obras Extraordinarias")
    with col_chk2:
        chk_plazos = st.checkbox("4. Estudio de Impacto en Plazo", value=True)
        chk_gg = st.checkbox("5a. Gastos Generales", value=True)
        chk_utilidades = st.checkbox("5b. Utilidad / Lucro Cesante")
    with col_chk3:
        chk_multas = st.checkbox("5c. Multas / Sanciones Contractuales")
        chk_accidente = st.checkbox("6. Accidentes / Siniestros")
        chk_productividad = st.checkbox("7. Estudio de Pérdida de Productividad")
    with col_chk4:
        chk_cotizacion = st.checkbox("8. Cotización / Análisis de Precios")

    otros_alcances = st.text_input(
        "9. Otros Alcances Especiales (Opcional):",
        value="",
        placeholder="Ingrese otros puntos específicos de ingeniería contractual..."
    )

    # Construcción ordenada respetando la secuencia estricta de prioridad 1 a 9
    alcances_ordenados = []
    if chk_pertinencia: alcances_ordenados.append("1. Estudio de pertinencia de situaciones.")
    if chk_ingenieria: alcances_ordenados.append("2. Estudio técnico ingeniería y arquitectura.")
    if chk_adicionales: alcances_ordenados.append("3. Obras Adicionales / Obras Extraordinarias.")
    if chk_plazos: alcances_ordenados.append("4. Estudio de impacto en plazo.")
    
    # Consolidación de Costos (Punto 5)
    costos_subitems = []
    if chk_gg: costos_subitems.append("Gastos Generales")
    if chk_utilidades: costos_subitems.append("Utilidad/Lucro Cesante")
    if chk_multas: costos_subitems.append("Multas")
    if costos_subitems:
        str_costos = ", ".join(costos_subitems)
        alcances_ordenados.append(f"5. Estudio de impacto en costo ({str_costos}).")

    if chk_accidente: alcances_ordenados.append("6. Accidentes / Siniestros.")
    if chk_productividad: alcances_ordenados.append("7. Estudio de pérdida de productividad.")
    if chk_cotizacion: alcances_ordenados.append("8. Cotización / Análisis de Precios.")
    if otros_alcances.strip(): alcances_ordenados.append(f"9. Otros Alcances Especiales: {otros_alcances.strip()}")

    str_lista_alcances = "\n".join([f"{a}" for a in alcances_ordenados])

    alcance_input = st.text_area(
        "Ingrese notas adicionales para el alcance (o borrador complementario):",
        value=st.session_state.text_alcance,
        placeholder="Ingrese notas específicas del alcance...",
        height=140
    )
    st.session_state.text_alcance = alcance_input

    if st.button("✨ Pulir y Desarrollar Capítulo 5 (Alcance Detallado)"):
        es_peritaje = "Peritaje" in tipo_encargo
        regla_vocabulario = (
            "Utiliza terminología pericial formal (peritaje, perito, puntos de prueba)."
            if es_peritaje else
            "Queda ESTRICTAMENTE PROHIBIDO usar las palabras 'peritaje', 'perito', 'puntos de prueba' o 'dictamen'. Utiliza únicamente 'estudio técnico', 'alcance de la revisión', 'materias a evaluar' o 'análisis contractual'."
        )

        notas_combined = (
            f"TIPO DE ENCARGO: {tipo_encargo}\n"
            f"SECUENCIA JERÁRQUICA DE PRIORIDAD PARA REDACCIÓN (RESPECTAR ESTRICTAMENTE ESTE ORDEN DE PRESENTACIÓN):\n{str_lista_alcances}\n\n"
            f"NOTAS ADICIONALES DEL ALCANCE:\n{st.session_state.text_alcance}"
        )
        prompt_tarea = (
            "Redacta el Capítulo 5 'Alcance Detallado' en español formal. Incluye un párrafo de encuadre inicial y luego formaliza las materias seleccionadas mediante viñetas ('•') con verbos en infinitivo. "
            f"REGLA DE VOCABULARIO: {regla_vocabulario} "
            "REGLA DE NO CITAR LEYES: No cites leyes, códigos legales ni normas de derecho. Enfócate exclusivamente en aspectos empíricos de ingeniería. "
            "REGLA CRÍTICA DE PRIORIDAD: Presenta y desarrolla los puntos del alcance en el ORDEN SECUENCIAL ESTRICTO indicado (del punto 1 al punto 9). NO alteres el orden jerárquico establecido ni agregues materias no seleccionadas. "
            "REGLA ESTRICTA DE FORMATO: No incluyas subcapítulos (ej: 5.1, 5.2), encabezados (#) ni caracteres '**'."
        )

        if alcances_ordenados or st.session_state.text_alcance.strip() or st.session_state.texto_adjuntos.strip():
            with st.spinner("✨ Puliendo e integrando Alcance en Capítulo 5 según secuencia jerárquica..."):
                texto_generado = llamar_ia_gemini(prompt_tarea, notas_combined, st.session_state.texto_adjuntos)
                if texto_generado and not texto_generado.startswith("⚠️"):
                    st.session_state.text_alcance = texto_generado
                    st.rerun()

    st.markdown("---")
    st.markdown("### ⚡ Generación Extensa de Actividades (Estándar Pericial IDIEM)")

    if st.button("⚙️ Generar 6. Actividades Extensas"):
        es_peritaje = "Peritaje" in tipo_encargo
        regla_vocabulario = (
            "Utiliza terminología pericial formal (peritaje, perito, dictamen pericial)."
            if es_peritaje else
            "Queda ESTRICTAMENTE PROHIBIDO usar las palabras 'peritaje', 'perito', 'pericial' o 'dictamen'. Sustitúyelas únicamente por 'informe técnico', 'estudio', 'revisión contractual', 'asesoría' o 'análisis de ingeniería'."
        )

        notas_combined = f"TIPO DE ENCARGO: {tipo_encargo}\nCLIENTE: {cliente}\nINTRODUCCIÓN (CAP 4): {st.session_state.text_intro}\nALCANCE (CAP 5): {st.session_state.text_alcance}"
        prompt_tarea = (
            "Redacta el Capítulo 6 'Actividades y Etapas Propuestas' de forma estructurada en Etapas secuenciales (Etapa A, Etapa B, etc.) alineadas minuciosamente a los puntos del alcance e hitos documentados. "
            f"REGLA DE VOCABULARIO OBLIGATORIA: {regla_vocabulario} "
            "REGLA DE NO CITAR NORMATIVAS O LEYES: No incluyas citas a leyes, artículos normativos, reglamentos legales ni preceptos de derecho. Limítate a describir la metodología técnica de ingeniería (revisión de libro de obras, análisis de cartas Gantt, cubicaciones, precios unitarios y trazabilidad documental). "
            "REGLA ESTRICTA DE FORMATO: No utilices símbolos de formato Markdown como '#', '##' ni '**'."
        )

        if st.session_state.text_intro.strip() or st.session_state.text_alcance.strip() or st.session_state.texto_adjuntos.strip():
            with st.spinner("⚙️ Generando Capítulo 6 con máximo detalle técnico..."):
                texto_generado = llamar_ia_gemini(prompt_tarea, notas_combined, st.session_state.texto_adjuntos)
                if texto_generado and not texto_generado.startswith("⚠️"):
                    st.session_state.auto_actividades = texto_generado
                    st.rerun()

    st.markdown("---")
    actividades = st.text_area(
        "6. Actividades / Etapas Propuestas (Output Generado):",
        value=st.session_state.auto_actividades,
        height=280
    )

# ---------------------------------------------------------
# PESTAÑA 3: HORAS HOMBRE Y PERFILES CON TARJETA DESTACADA DE PLAZO
# ---------------------------------------------------------
with tab3:
    st.subheader("Estimación de Recursos y Perfiles Profesionales")

    # Módulo visual destacado para la asignación del plazo total
    st.markdown("""
        <div class="plazo-card">
            <h4 style="margin:0; color:#002855;">⏱️ PLAZO TOTAL DEL ESTUDIO PERICIAL</h4>
            <p style="margin:2px 0 10px 0; font-size:13px; color:#555;">Ingrese la duración estimada en meses para el desarrollo integral del encargo pericial.</p>
        </div>
    """, unsafe_allow_html=True)

    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        meses_val = st.number_input(
            "Plazo Total del Estudio (Meses):",
            min_value=0.5,
            step=0.5,
            value=1.0,
            help="Este parámetro escala automáticamente las Horas Hombre (HH) totales y el presupuesto final en UF."
        )

    st.markdown("---")

    col_hdr1, col_hdr2, col_hdr3 = st.columns([2, 1, 1])
    with col_hdr1: st.markdown("**Categoría Profesional**")
    with col_hdr2: st.markdown("**HH / Mes**")
    with col_hdr3: st.markdown("**Tarifa (UF/HH)**")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Asesor Técnico / Revisor / Perito Senior")
    with c2: hh_asesor = st.number_input("HH Asesor", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_asesor = st.number_input("Tarifa Asesor", min_value=0.0, value=0.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Jefe de Proyecto / Perito Principal")
    with c2: hh_jefe = st.number_input("HH Jefe", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_jefe = st.number_input("Tarifa Jefe", min_value=0.0, value=0.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 1")
    with c2: hh_an1 = st.number_input("HH Profesional 1", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an1 = st.number_input("Tarifa Prof. 1", min_value=0.0, value=0.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 2")
    with c2: hh_an2 = st.number_input("HH Profesional 2", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an2 = st.number_input("Tarifa Prof. 2", min_value=0.0, value=0.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 3")
    with c2: hh_an3 = st.number_input("HH Profesional 3", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an3 = st.number_input("Tarifa Prof. 3", min_value=0.0, value=0.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 4")
    with c2: hh_an4 = st.number_input("HH Profesional 4", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an4 = st.number_input("Tarifa Prof. 4", min_value=0.0, value=0.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 5")
    with c2: hh_an5 = st.number_input("HH Profesional 5", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an5 = st.number_input("Tarifa Prof. 5", min_value=0.0, value=0.0, step=0.1, label_visibility="collapsed")

    num_profesionales_activos = sum([1 for hh in [hh_an1, hh_an2, hh_an3, hh_an4, hh_an5] if hh > 0])

    tot_hh = (hh_asesor + hh_jefe + hh_an1 + hh_an2 + hh_an3 + hh_an4 + hh_an5) * meses_val
    tot_uf = (
        hh_asesor * tar_asesor +
        hh_jefe * tar_jefe +
        hh_an1 * tar_an1 +
        hh_an2 * tar_an2 +
        hh_an3 * tar_an3 +
        hh_an4 * tar_an4 +
        hh_an5 * tar_an5
    ) * meses_val

    st.markdown("---")
    st.info(f"**Total Horas Hombre:** {tot_hh:.0f} HH  |  **Monto Total Calculado:** UF {tot_uf:.1f}.-")

# ---------------------------------------------------------
# PESTAÑA 4: OFERTA ECONÓMICA, EXCLUSIONES Y DESCARGA
# ---------------------------------------------------------
with tab4:
    st.subheader("Condiciones Comerciales y Exclusiones")

    st.markdown("#### 11. Exclusiones del Servicio (4 Espacios Editables)")
    excl1 = st.text_input("Exclusión 1:", value="Visitas a terreno adicionales no contempladas expresamente en la propuesta.")
    excl2 = st.text_input("Exclusión 2:", value="Analizar materias o puntos de prueba no incluidos en el alcance o resolución pericial acordada.")
    excl3 = st.text_input("Exclusión 3:", value="Emisión de opiniones legales o interpretaciones de derecho, limitándose el servicio al análisis técnico-contractual de ingeniería.")
    excl4 = st.text_input("Exclusión 4 (Opcional):", value="")

    st.markdown("---")
    st.markdown("#### 13. Estructura de Pagos (5 Hitos Personalizables)")

    col_t1, col_p1 = st.columns([3, 1])
    with col_t1: titulo_h1 = st.text_input("Título Hito 1:", value="al momento de aceptar la presente propuesta.")
    with col_p1: pct_h1 = st.number_input("% Hito 1:", min_value=0, max_value=100, value=30)

    col_t2, col_p2 = st.columns([3, 1])
    with col_t2: titulo_h2 = st.text_input("Título Hito 2:", value="contra la presentación de avance 1.")
    with col_p2: pct_h2 = st.number_input("% Hito 2:", min_value=0, max_value=100, value=20)

    col_t3, col_p3 = st.columns([3, 1])
    with col_t3: titulo_h3 = st.text_input("Título Hito 3:", value="contra la presentación de avance 2.")
    with col_p3: pct_h3 = st.number_input("% Hito 3:", min_value=0, max_value=100, value=20)

    col_t4, col_p4 = st.columns([3, 1])
    with col_t4: titulo_h4 = st.text_input("Título Hito 4:", value="contra entrega de informe borrador.")
    with col_p4: pct_h4 = st.number_input("% Hito 4:", min_value=0, max_value=100, value=20)

    col_t5, col_p5 = st.columns([3, 1])
    with col_t5: titulo_h5 = st.text_input("Título Hito 5:", value="al momento de entregar informe final.")
    with col_p5: pct_h5 = st.number_input("% Hito 5:", min_value=0, max_value=100, value=10)

    tot_pct = pct_h1 + pct_h2 + pct_h3 + pct_h4 + pct_h5
    if tot_pct != 100:
        st.warning(f"Atención: Los porcentajes ingresados suman {tot_pct}%. Deben completar exactamente el 100%.")
    else:
        st.success("Estructura de pagos válida (Suma 100%).")

    condicion_pago = st.text_input("Condición de Pago (Días):", value="30 días desde fecha de emisión de factura.")

    regimen_iva = st.selectbox("Régimen de Impuestos / IVA:", [
        "Exento de IVA (Ley N° 21.094 sobre Universidades Estatales)",
        "Afecto a IVA (Recargo del 19% según Ley N° 21.420)"
    ])

    st.markdown("---")

    # ---------------------------------------------------------
    # GENERACIÓN CON PLANTILLA OFICIAL
    # ---------------------------------------------------------
    def generar_documento_word():
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base_dir, "Plantilla_Oficial_IDIEM.docx")

        if not os.path.exists(template_path):
            st.error(f"❌ No se encontró la plantilla en la ruta: {template_path}. Por favor sube 'Plantilla_Oficial_IDIEM.docx' a GitHub.")
            st.stop()

        doc = DocxTemplate(template_path)

        lista_excl = []
        if excl1.strip(): lista_excl.append(excl1.strip())
        if excl2.strip(): lista_excl.append(excl2.strip())
        if excl3.strip(): lista_excl.append(excl3.strip())
        if excl4.strip(): lista_excl.append(excl4.strip())

        str_duracion = f"{meses_val:.0f}" if meses_val.is_integer() else f"{meses_val}"
        monto_uf_palabras = numero_a_palabras_uf(tot_uf)

        alcance_txt = limpiar_formato_texto(st.session_state.text_alcance)
        intro_txt = limpiar_formato_texto(st.session_state.text_intro)
        actividades_txt = limpiar_formato_texto(actividades)

        if alcance_txt.strip():
            oraciones = [s.strip() for s in alcance_txt.replace("\n", ". ").split(".") if s.strip()]
            num_oraciones = max(1, int(len(oraciones) * 0.20))
            resumen_alcance_20 = ". ".join(oraciones[:num_oraciones]) + "."
        else:
            resumen_alcance_20 = "El presente estudio comprende la evaluación técnica y contractual de los conceptos e impactos reclamados en el proyecto."

        lista_items_propuesta = []
        if actividades_txt.strip():
            lines = actividades_txt.split("\n")
            for line in lines:
                line_str = line.strip()
                if line_str.startswith("Etapa "):
                    lista_items_propuesta.append(line_str)

        if not lista_items_propuesta:
            lista_items_propuesta = [
                "Etapa A: Análisis de antecedentes y línea base contractual",
                "Etapa B: Análisis de pertinencia técnica y trazabilidad documental",
                "Etapa C: Análisis de impacto en el programa de obras (Delay Analysis)",
                "Etapa D: Evaluación económica y cuantificación de mayores costos",
                "Etapa E: Elaboración del Informe Final IDIEM"
            ]

        lista_introduccion_lineas = [l.strip() for l in intro_txt.split("\n") if l.strip()]
        lista_alcance_lineas = [l.strip() for l in alcance_txt.split("\n") if l.strip()]
        lista_actividades_lineas = [l.strip() for l in actividades_txt.split("\n") if l.strip()]

        lista_hitos_forma_pago = []
        raw_hitos = [
            (pct_h1, titulo_h1),
            (pct_h2, titulo_h2),
            (pct_h3, titulo_h3),
            (pct_h4, titulo_h4),
            (pct_h5, titulo_h5)
        ]
        for pct, tit in raw_hitos:
            if pct > 0:
                lista_hitos_forma_pago.append(f"{pct}% {tit}")

        contexto = {
            'CODIGO_PROPUESTA': codigo if codigo else "PR.DIC",
            'NUM_REVISION': revision if revision else "0",
            'NOMBRE_PROPUESTA': nombre_propuesta,
            'NOMBRE_CLIENTE': cliente,
            'RUT_CLIENTE': rut_cliente,
            'NOMBRE_SOLICITANTE': solicitante,
            'CARGO_SOLICITANTE': cargo_solicitante,
            'EMAIL_SOLICITANTE': email_solicitante,
            'TELEFONO_SOLICITANTE': telefono_solicitante,
            'ROL_CAM_O_TRIBUNAL': rol_cam if rol_cam else "N/A",
            'FECHA_EMISION': fecha_emision.strftime("%d-%m-%Y"),
            'SINTESIS_ALCANCE': resumen_alcance_20,
            'LISTA_ITEMS_PROPUESTA': lista_items_propuesta,
            'LISTA_HITOS_FORMA_PAGO': lista_hitos_forma_pago,
            'PLAZO_MESES': str_duracion,
            'PLAZO_TEXTO': f"{str_duracion} meses",
            'NUM_PROFESIONALES_ASESORIA': f"{num_profesionales_activos} Profesionales de Asesoría",
            'MONTO_UF_TOTAL': f"{tot_uf:,.0f}".replace(",", "."),
            'MONTO_UF_PALABRAS': monto_uf_palabras,
            'CONDICION_PAGO': condicion_pago,
            'TEXTO_INTRODUCCION': intro_txt,
            'TEXTO_ALCANCE_DETALLADO': alcance_txt,
            'TEXTO_ACTIVIDADES_ETAPAS': actividades_txt,

            'LISTA_INTRODUCCION_LINEAS': lista_introduccion_lineas,
            'LISTA_ALCANCE_LINEAS': lista_alcance_lineas,
            'LISTA_ACTIVIDADES_LINEAS': lista_actividades_lineas,

            'LISTA_EXCLUSIONES': lista_excl,
            'NOTA_IMPUESTOS_IVA': regimen_iva,

            'HH_ASESOR': hh_asesor,
            'TAR_ASESOR': f"{tar_asesor:.1f}".replace(".", ","),
            'TOT_HH_ASESOR': int(hh_asesor * meses_val),
            'TOT_UF_ASESOR': f"{int(hh_asesor * tar_asesor * meses_val):,.0f}".replace(",", "."),

            'HH_JEFE': hh_jefe,
            'TAR_JEFE': f"{tar_jefe:.1f}".replace(".", ","),
            'TOT_HH_JEFE': int(hh_jefe * meses_val),
            'TOT_UF_JEFE': f"{int(hh_jefe * tar_jefe * meses_val):,.0f}".replace(",", "."),

            'HH_AN1': hh_an1,
            'TAR_AN1': f"{tar_an1:.1f}".replace(".", ","),
            'TOT_HH_AN1': int(hh_an1 * meses_val),
            'TOT_UF_AN1': f"{int(hh_an1 * tar_an1 * meses_val):,.0f}".replace(",", "."),

            'HH_AN2': hh_an2,
            'TAR_AN2': f"{tar_an2:.1f}".replace(".", ","),
            'TOT_HH_AN2': int(hh_an2 * meses_val),
            'TOT_UF_AN2': f"{int(hh_an2 * tar_an2 * meses_val):,.0f}".replace(",", "."),

            'HH_AN3': hh_an3,
            'TAR_AN3': f"{tar_an3:.1f}".replace(".", ","),
            'TOT_HH_AN3': int(hh_an3 * meses_val),
            'TOT_UF_AN3': f"{int(hh_an3 * tar_an3 * meses_val):,.0f}".replace(",", "."),

            'HH_AN4': hh_an4,
            'TAR_AN4': f"{tar_an4:.1f}".replace(".", ","),
            'TOT_HH_AN4': int(hh_an4 * meses_val),
            'TOT_UF_AN4': f"{int(hh_an4 * tar_an4 * meses_val):,.0f}".replace(",", "."),

            'HH_AN5': hh_an5,
            'TAR_AN5': f"{tar_an5:.1f}".replace(".", ","),
            'TOT_HH_AN5': int(hh_an5 * meses_val),
            'TOT_UF_AN5': f"{int(hh_an5 * tar_an5 * meses_val):,.0f}".replace(",", "."),

            'TOT_HH_GENERAL': int(tot_hh),

            'TIT_H1': titulo_h1, 'PCT_H1': pct_h1, 'UF_H1': f"{int(tot_uf * (pct_h1/100)):,.0f}".replace(",", "."),
            'TIT_H2': titulo_h2, 'PCT_H2': pct_h2, 'UF_H2': f"{int(tot_uf * (pct_h2/100)):,.0f}".replace(",", "."),
            'TIT_H3': titulo_h3, 'PCT_H3': pct_h3, 'UF_H3': f"{int(tot_uf * (pct_h3/100)):,.0f}".replace(",", "."),
            'TIT_H4': titulo_h4, 'PCT_H4': pct_h4, 'UF_H4': f"{int(tot_uf * (pct_h4/100)):,.0f}".replace(",", "."),
            'TIT_H5': titulo_h5, 'PCT_H5': pct_h5, 'UF_H5': f"{int(tot_uf * (pct_h5/100)):,.0f}".replace(",", "."),
        }

        doc.render(contexto)

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    st.download_button(
        label="📥 Descargar Propuesta Emitida Formato Oficial (.docx)",
        data=generar_documento_word(),
        file_name=f"Propuesta_IDIEM_{codigo if codigo else 'PR.DIC'}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
