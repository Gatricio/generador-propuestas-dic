import os
import datetime
from io import BytesIO
import streamlit as st
from docxtpl import DocxTemplate
from google import genai
import pypdf
import docx

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
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# INICIALIZACIÓN CLIENTE GEMINI API
# ---------------------------------------------------------
@st.cache_resource
def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

client = get_gemini_client()

# ---------------------------------------------------------
# FUNCIONES PARA EXTRACCIÓN DE TEXTO DE ARCHIVOS
# ---------------------------------------------------------
def extraer_texto_pdf(file_bytes):
    try:
        pdf_reader = pypdf.PdfReader(BytesIO(file_bytes))
        texto = ""
        for page in pdf_reader.pages:
            texto += page.extract_text() or ""
        return texto
    except Exception as e:
        return f"[Error al leer PDF: {str(e)}]"

def extraer_texto_docx(file_bytes):
    try:
        doc = docx.Document(BytesIO(file_bytes))
        texto = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return texto
    except Exception as e:
        return f"[Error al leer DOCX: {str(e)}]"

# ---------------------------------------------------------
# PROMPT DEL SISTEMA: GUARDARRAÍLES Y TONO PERICIAL IDIEM
# ---------------------------------------------------------
SYSTEM_GUARDRAILS_IDIEM = """
Eres un Ingeniero Perito Senior de la División de Ingeniería Contractual de IDIEM (Universidad de Chile).
Tu objetivo es redactar propuestas técnicas e informes periciales con el máximo rigor de ingeniería, neutralidad y objetividad.

REGLAS DE ORO Y GUARDARRAÍLES DE NEUTRALIDAD:
1. ANCLAJE ESTRICTO A LOS ANTECEDENTES: Utiliza EXCLUSIVAMENTE la información proporcionada en los textos y archivos subidos. NO inventes hechos, NO asumas datos no documentados y NO agregues información externa o de la web.
2. NEUTRALIDAD TÉCNICA ABSOLUTA: Mantén un lenguaje neutral, empírico e imparcial.
   - PROHIBIDO usar adjetivos o calificativos acusatorios o jurídicos (ej: "incumplimiento grave", "actitud negligente", "pretensión infundada", "culpabilidad", "parábolas").
   - SUSTITUYE por descripciones objetivas de ingeniería (ej: "desviación respecto de la línea base", "modificación de la secuencia constructiva", "evento registrado en Libro de Obras N° X").
3. ENFOQUE DIRECTO A LAS NECESIDADES DEL CLIENTE: Identifica con precisión las solicitudes específicas expresadas en las demandas, correos o antecedentes cargados.
4. ESTÁNDAR IDIEM: Toda cuantificación debe fundamentarse en datos comprobables, análisis de ruta crítica (Delay Analysis), valores de subcontrato o precios de mercado, sin juicios de valor.
"""

def llamar_ia_gemini(prompt_tarea, contexto_usuario):
    if not client:
        return "⚠️ Error: No se ha configurado la variable de entorno GEMINI_API_KEY en los Secrets de Streamlit."
    try:
        prompt_completo = f"{SYSTEM_GUARDRAILS_IDIEM}\n\nTAREA:\n{prompt_tarea}\n\nANTECEDENTES DEL CASO:\n{contexto_usuario}"
        
        # Modelo oficial universal soportado por Google Gen AI API
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt_completo,
            config={
                'temperature': 0.3,
                'max_output_tokens': 4000,
            }
        )
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Error al conectar con Gemini API: {str(e)}"

# ---------------------------------------------------------
# FUNCIÓN: CONVERSIÓN DE NÚMEROS A PALABRAS EN ESPAÑOL (UF)
# ---------------------------------------------------------
def numero_a_palabras_uf(n):
    n = int(round(n))
    if n == 0:
        return "cero"

    unidades = ["", "un", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
    especiales = ["diez", "once", "doce", "trece", "catorce", "quince", "diecisiete", "dieciocho", "diecinueve"]
    especiales[6] = "dieciséis"
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
# PESTAÑA 2: ALCANCE Y CONTEXTO (CON CARGA DE ARCHIVOS)
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

    # --- MÓDULO DE CARGA DE ARCHIVOS ---
    st.markdown("#### 📁 Cargar Documentos de Respaldo (Opcional)")
    st.caption("Puedes subir la demanda, descripción de la obra, laudos o correos del cliente en formato PDF o DOCX para que el sistema adapte la propuesta directamente a las necesidades del caso.")
    
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
            texto_extraido_total.append(f"--- DOCUMENTO: {file.name} ---\n{txt}\n")
        
        st.session_state.texto_adjuntos = "\n".join(texto_extraido_total)
        st.success(f"¡Se han procesado {len(uploaded_files)} archivo(s) correctamente!")

    st.markdown("---")

    # --- CAPÍTULO 4: INTRODUCCIÓN ---
    st.markdown("#### 4. Introducción / Contexto de la Obra")
    
    intro_input = st.text_area(
        "Ingrese antecedentes del contrato, obra y conflicto:", 
        value=st.session_state.text_intro, 
        placeholder="Ingrese borrador o notas del contexto...", 
        height=160,
        key="key_intro_area"
    )
    st.session_state.text_intro = intro_input

    def aplicar_pulido_cap4():
        contexto_combinado = f"CLIENTE: {cliente}\nNOMBRE PROPUESTA: {nombre_propuesta}\n\nTEXTO CAPÍTULO 4:\n{st.session_state.text_intro}\n\nANTECEDENTES SUBIDOS:\n{st.session_state.texto_adjuntos}"
        prompt_tarea = "Redacta el Capítulo 4 'Introducción / Contexto de la Obra' estructurado en párrafos ejecutivos claros, objetivos y formales. Mantiene la neutralidad e imparcialidad pericial de IDIEM."
        
        if st.session_state.text_intro.strip() or st.session_state.texto_adjuntos.strip():
            with st.spinner("✨ Puliendo Capítulo 4 con Gemini IA y Guardarraíles IDIEM..."):
                texto_pulido = llamar_ia_gemini(prompt_tarea, contexto_combinado)
                st.session_state.text_intro = texto_pulido
                st.session_state.key_intro_area = texto_pulido

    st.button("✨ Pulir y Mejorar Redacción del Capítulo 4 (Introducción)", on_click=aplicar_pulido_cap4)

    st.markdown("---")

    # --- CAPÍTULO 5: ALCANCE DETALLADO ---
    st.markdown("#### 5. Alcance Detallado (Puntos a evaluar / Puntos de Prueba)")
    
    alcance_input = st.text_area(
        "Ingrese el desglose de materias, reclamaciones o Puntos de Prueba:", 
        value=st.session_state.text_alcance, 
        placeholder="Ingrese borrador o lista de puntos de prueba...", 
        height=160,
        key="key_alcance_area"
    )
    st.session_state.text_alcance = alcance_input

    def aplicar_pulido_cap5():
        contexto_combinado = f"TEXTO CAPÍTULO 5:\n{st.session_state.text_alcance}\n\nANTECEDENTES SUBIDOS:\n{st.session_state.texto_adjuntos}"
        prompt_tarea = "Redacta el Capítulo 5 'Alcance Detallado' formalizando los puntos específicos a evaluar mediante viñetas ('•') con verbos en infinitivo. Separa formalmente las exclusiones si las hubiere. Mantiene la estricta neutralidad de IDIEM."
        
        if st.session_state.text_alcance.strip() or st.session_state.texto_adjuntos.strip():
            with st.spinner("✨ Puliendo Capítulo 5 con Gemini IA y Guardarraíles IDIEM..."):
                texto_pulido = llamar_ia_gemini(prompt_tarea, contexto_combinado)
                st.session_state.text_alcance = texto_pulido
                st.session_state.key_alcance_area = texto_pulido

    st.button("✨ Pulir y Mejorar Redacción del Capítulo 5 (Alcance)", on_click=aplicar_pulido_cap5)

    st.markdown("---")
    st.markdown("### ⚡ Generación Extensa de Actividades (Estándar Pericial IDIEM)")

    def aplicar_generar_actividades():
        contexto_combinado = f"CLIENTE: {cliente}\n\nINTRODUCCIÓN (CAP 4):\n{st.session_state.text_intro}\n\nALCANCE (CAP 5):\n{st.session_state.text_alcance}\n\nANTECEDENTES SUBIDOS:\n{st.session_state.texto_adjuntos}"
        prompt_tarea = """
        Redacta el Capítulo 6 'Actividades y Etapas Propuestas' estructurado en Etapas secuenciales (Etapa A, Etapa B, etc.) alineadas exactamente a los puntos del alcance.
        - NO incluyas inspección en terreno si no se menciona expresamente.
        - NO incluyas normativas MOP si se trata de un contrato privado salvo que se soliciten.
        - Redacta cada actividad en párrafos independientes y con la profundidad técnica de IDIEM.
        """
        if st.session_state.text_intro.strip() or st.session_state.text_alcance.strip() or st.session_state.texto_adjuntos.strip():
            with st.spinner("⚙️ Generando Capítulo 6 con Gemini IA y Guardarraíles IDIEM..."):
                actividades_gen = llamar_ia_gemini(prompt_tarea, contexto_combinado)
                st.session_state.auto_actividades = actividades_gen

    st.button("⚙️ Generar 6. Actividades Extensas", on_click=aplicar_generar_actividades)

    st.markdown("---")
    actividades = st.text_area(
        "6. Actividades / Etapas Propuestas (Output Generado):", 
        value=st.session_state.auto_actividades, 
        height=280
    )

# ---------------------------------------------------------
# PESTAÑA 3: HORAS HOMBRE Y PERFILES
# ---------------------------------------------------------
with tab3:
    st.subheader("Estimación de Recursos y Perfiles Profesionales")
    meses_val = st.number_input("Plazo Total del Estudio (Meses):", min_value=0.5, step=0.5, value=1.0)
    
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

        alcance_txt = st.session_state.text_alcance
        intro_txt = st.session_state.text_intro

        if alcance_txt.strip():
            oraciones = [s.strip() for s in alcance_txt.replace("\n", ". ").split(".") if s.strip()]
            num_oraciones = max(1, int(len(oraciones) * 0.20))
            resumen_alcance_20 = ". ".join(oraciones[:num_oraciones]) + "."
        else:
            resumen_alcance_20 = "El presente estudio comprende la evaluación técnica y contractual de los conceptos e impactos reclamados en el proyecto."

        lista_items_propuesta = []
        if actividades.strip():
            lines = actividades.split("\n")
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
        lista_actividades_lineas = [l.strip() for l in actividades.split("\n") if l.strip()]

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
            'TEXTO_ACTIVIDADES_ETAPAS': actividades,
            
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
