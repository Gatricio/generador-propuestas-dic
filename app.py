import os
import re
import datetime
from io import BytesIO
import streamlit as st
from docxtpl import DocxTemplate

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
# FUNCIONES DE MEJORA Y PULIDO DE REDACCIÓN (CAPS 4 Y 5)
# ---------------------------------------------------------
def pulir_introduccion(texto, cliente_val, propuesta_val):
    if not texto.strip():
        return ""
    
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
    
    reemplazos = {
        r"\bcodelco\b": "CODELCO",
        r"\bmetro\b": "METRO S.A.",
        r"\bminvu\b": "MINVU",
        r"\bmop\b": "MOP",
        r"\bcam\b": "CAM Santiago",
        r"\bito\b": "ITO",
        r"\brdi\b": "RDI",
        r"\brcop\b": "RCOP",
        r"\bee.tt\b": "EETT",
        r"\beett\b": "EETT",
        r"\ba causa de\b": "en razón de",
        r"\bpor culpa de\b": "derivado de la situación ocurrida en",
        r"\batraso\b": "desviación en los plazos de ejecución",
    }
    
    texto_procesado = "\n".join(lineas)
    for patron, reemp in reemplazos.items():
        texto_procesado = re.sub(patron, reemp, texto_procesado, flags=re.IGNORECASE)
    
    cliente_ref = cliente_val if cliente_val.strip() else "el Cliente"
    prop_ref = propuesta_val if propuesta_val.strip() else "el estudio técnico-contractual solicitado"
    
    parrafos_pulidos = []
    parrafos_pulidos.append(
        f"El presente documento corresponde a la propuesta técnica y económica desarrollada por IDIEM para {cliente_ref}, "
        f"referida al servicio denominado \"{prop_ref}\"."
    )
    
    for l in lineas:
        l_corregida = l[0].upper() + l[1:] if len(l) > 1 else l.upper()
        if not l_corregida.endswith("."):
            l_corregida += "."
        
        if "propuesta técnica" not in l_corregida.lower() and "idiem" not in l_corregida.lower():
            parrafos_pulidos.append(l_corregida)
            
    return "\n\n".join(parrafos_pulidos)


def pulir_alcance(texto):
    if not texto.strip():
        return ""
    
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
    
    reemplazos = {
        r"\bver\b": "Evaluar y analizar",
        r"\brevisar\b": "Analizar la pertinencia técnico-contractual de",
        r"\bcalcular\b": "Cuantificar económicamente",
        r"\bver si\b": "Determinar si",
        r"\bcobrar\b": "Valorizar",
    }
    
    items_pulidos = []
    items_pulidos.append("De acuerdo con los requerimientos expresados, el alcance del presente estudio considera analizar e informar sobre los siguientes puntos específicos:")
    
    for l in lineas:
        l_clean = re.sub(r"^[\-\*\•\d\.\)]+\s*", "", l).strip()
        if not l_clean:
            continue
            
        for patron, reemp in reemplazos.items():
            l_clean = re.sub(patron, reemp, l_clean, flags=re.IGNORECASE)
            
        l_clean = l_clean[0].upper() + l_clean[1:] if len(l_clean) > 1 else l_clean.upper()
        if not l_clean.endswith("."):
            l_clean += "."
            
        items_pulidos.append(f"• {l_clean}")
        
    return "\n".join(items_pulidos)

# ---------------------------------------------------------
# FUNCIÓN: CONVERSIÓN DE NÚMEROS A PALABRAS EN ESPAÑOL (UF)
# ---------------------------------------------------------
def numero_a_palabras_uf(n):
    n = int(round(n))
    if n == 0:
        return "cero"

    unidades = ["", "un", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
    especiales = ["diez", "once", "doce", "trece", "catorce", "quince", "diecisiete", "diecisiete", "dieciocho", "diecinueve"]
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
# PESTAÑA 2: ALCANCE Y CONTEXTO
# ---------------------------------------------------------
with tab2:
    st.subheader("Descripción del Conflicto y Propuesta Técnica")
    
    if "text_intro" not in st.session_state:
        st.session_state.text_intro = ""
    if "text_alcance" not in st.session_state:
        st.session_state.text_alcance = ""
    if "auto_actividades" not in st.session_state:
        st.session_state.auto_actividades = ""

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
        if st.session_state.text_intro.strip():
            texto_pulido = pulir_introduccion(st.session_state.text_intro, cliente, nombre_propuesta)
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
        if st.session_state.text_alcance.strip():
            texto_pulido = pulir_alcance(st.session_state.text_alcance)
            st.session_state.text_alcance = texto_pulido
            st.session_state.key_alcance_area = texto_pulido

    st.button("✨ Pulir y Mejorar Redacción del Capítulo 5 (Alcance)", on_click=aplicar_pulido_cap5)

    st.markdown("---")
    st.markdown("### ⚡ Generación Extensa de Actividades (Estándar Pericial IDIEM)")

    if st.button("⚙️ Generar 6. Actividades Extensas"):
        if not st.session_state.text_intro.strip() and not st.session_state.text_alcance.strip():
            st.warning("Por favor ingrese texto en la Introducción o en el Alcance Detallado antes de generar.")
        else:
            txt_comb = (st.session_state.text_intro + " " + st.session_state.text_alcance).lower()
            client_ref = cliente if cliente else "el Cliente / Solicitante"
            
            # Verificación estricta de solicitud de visita a terreno
            requiere_terreno = any(k in txt_comb for k in ["terreno", "visita", "inspección in situ", "recorrido", "recinto", "inspeccion in situ"])

            act_blocks = ["Para responder de manera integral al alcance solicitado, se contemplan las siguientes etapas y actividades de ingeniería contractual:\n"]
            
            etapa_letra = 'A'

            # --- ETAPA DE TERRENO SOLO SI FUE SOLICITADA ---
            if requiere_terreno:
                act_blocks.append(f"Etapa {etapa_letra}: Inspección en terreno y verificación in situ")
                act_blocks.append("Considera la realización de una visita a terreno por parte del equipo especialista de IDIEM para examinar directamente las condiciones físicas de la obra, recintos e instalaciones involucradas en el alcance. Durante la inspección se resguardará el principio de neutralidad técnica, recopilando antecedentes empíricos sin emitir juzamientos preliminares.\n")
                etapa_letra = chr(ord(etapa_letra) + 1)

            # --- ETAPA DE LÍNEA BASE Y PERTINENCIA ---
            act_blocks.append(f"Etapa {etapa_letra}: Análisis de antecedentes y línea base contractual")
            act_blocks.append(f"Considera la revisión exhaustiva de los antecedentes contractuales, de licitación y del expediente proporcionados por {client_ref} (bases de licitación, aclaraciones, contrato, programas de obra oficiales Rev0, especificaciones técnicas y ofertas) para establecer la línea base contractual y el orden de prelación aplicable a las materias en controversia.\n")
            etapa_letra = chr(ord(etapa_letra) + 1)

            act_blocks.append(f"Etapa {etapa_letra}: Análisis de pertinencia técnica y trazabilidad documental")
            act_blocks.append("Evaluación sistemática de cada evento o punto de prueba reclamado para determinar si constituye un cambio de condición respecto de la línea base, ordenando la documentación contemporánea de la obra (libros de obra, cartas formales, RDI, informes de inspección y minutas) que permita acreditar objetivamente su origen, atribución y consecuencia.\n")
            etapa_letra = chr(ord(etapa_letra) + 1)

            # --- ETAPA DE PLAZOS (DELAY ANALYSIS) ---
            if any(k in txt_comb for k in ["plazo", "atraso", "retraso", "ruta crítica", "programa", "cronograma", "hitos", "delay"]):
                act_blocks.append(f"Etapa {etapa_letra}: Análisis de impacto en el programa de obras (Delay Analysis)")
                act_blocks.append("Revisión de la lógica de programación y ruta crítica en los programas oficiales (Primavera P6 / MS Project). Se insertarán los eventos validados como actividades independientes para evaluar su impacto real sobre los plazos contractuales, hitos intermedios y la eventual concurrencia de retrasos.\n")
                etapa_letra = chr(ord(etapa_letra) + 1)

            # --- ETAPA DE COSTOS Y PERJUICIOS (EVALUACIÓN ECONÓMICA LIMPIA Y FIEL) ---
            if any(k in txt_comb for k in ["costo", "gasto", "económic", "presupuesto", "adicional", "perjuicio", "daño", "cuantific", "productividad", "rendimiento"]):
                act_blocks.append(f"Etapa {etapa_letra}: Evaluación económica y cuantificación de perjuicios / mayores costos")
                act_blocks.append("Determinación, revisión y cuantificación económica objetiva de los mayores costos directos, indirectos o daños validados en el alcance, aplicando criterios técnicos de mercado, valores de subcontratación y/o la consideración de reajustes e intereses según lo establecido en los antecedentes del caso.\n")
                etapa_letra = chr(ord(etapa_letra) + 1)

            # --- ETAPA FINAL ---
            act_blocks.append(f"Etapa {etapa_letra}: Elaboración del Informe Final IDIEM")
            act_blocks.append("Consolidación de los análisis en un informe técnico pericial imparcial y fundado, estructurado en lenguaje de ingeniería neutral, que dé respuesta expresa a cada uno de los puntos del alcance con sus correspondientes matrices y carpetas de respaldo documental.\n")

            st.session_state.auto_actividades = "\n".join(act_blocks)
            st.success("¡Actividades generadas ajustándose estrictamente al texto introducido!")

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
