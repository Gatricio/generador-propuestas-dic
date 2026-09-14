import os
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
    tipo_encargo = st.radio("Tipo de Servicio:", ["Informe Técnico de Parte (Cliente Directo)", "Peritaje Judicial / Arbitral CAM (Designación de Tribunal)"])
    
    col1, col2 = st.columns(2)
    with col1:
        codigo = st.text_input("Código de Propuesta:", value="", placeholder="Ingrese código PR.DIC...")
        cliente = st.text_input("Cliente / Razón Social o Tribunal:", value="", placeholder="Ingrese razón social o Tribunal Arbitral CAM...")
        solicitante = st.text_input("Nombre Solicitante / Juez Árbitro:", value="", placeholder="Nombre del solicitante o Sr. Árbitro...")
        cargo_solicitante = st.text_input("Cargo Solicitante:", value="", placeholder="Cargo del solicitante / Juez Árbitro...")
        fecha_emision = st.date_input("Fecha de Emisión:", value=datetime.date.today(), format="DD/MM/YYYY")
    with col2:
        revision = st.text_input("Revisión N°:", value="0")
        rut_cliente = st.text_input("RUT Cliente / Tribunal:", value="", placeholder="RUT...")
        email_solicitante = st.text_input("Email Solicitante:", value="", placeholder="correo@ejemplo.cl")
        telefono_solicitante = st.text_input("Teléfono Solicitante:", value="", placeholder="+56 9 ...")
        rol_cam = st.text_input("Tribunal / Rol Arbitral CAM:", value="", placeholder="Rol CAM N°...")
    
    nombre_propuesta = st.text_input("Nombre Oficial de la Propuesta / Peritaje:", value="", placeholder="Ej: PERITAJE TÉCNICO INDEPENDIENTE ROL CAM N°...")

# ---------------------------------------------------------
# PESTAÑA 2: ALCANCE Y CONTEXTO
# ---------------------------------------------------------
with tab2:
    st.subheader("Descripción del Conflicto y Propuesta Técnica")
    
    if "auto_actividades" not in st.session_state:
        st.session_state.auto_actividades = ""

    tipo_estudio = st.selectbox(
        "Seleccione el Enfoque Metodológico Específico de IDIEM:",
        [
            "Peritaje Judicial / Arbitral CAM (Designación por Tribunal y Respuesta a Puntos de Prueba)",
            "Estudio de Pertinencia e Impacto en Plazo y Costos (Claims / Obras de Infraestructura)",
            "Peritaje de Auditoría Normativa de Infraestructura y Brechas Sanitarias/Técnicas",
            "Informe Forense de Evaluación de Causales de Término Anticipado de Contrato",
            "Análisis Pericial de Discrepancias Metodológicas y Contra-peritaje de Prueba",
            "Análisis Técnico-Contractual de Rendimientos, Productividad y Equipos"
        ]
    )

    intro = st.text_area(
        "4. Introducción / Contexto de la Obra (Input Usuario):", 
        value="", 
        placeholder="Ingrese el contexto detallado del juicio arbitral, partes intervinientes, contrato y controversia...", 
        height=140
    )
    
    alcance = st.text_area(
        "5. Alcance Detallado (Puntos de Prueba decretados por el Tribunal - Input Usuario):", 
        value="", 
        placeholder="Ingrese los Puntos de Prueba transcritos del Acta de Designación Pericial...", 
        height=140
    )

    st.markdown("---")
    st.markdown("### ⚡ Generación Extensa de Actividades (Estándar Pericial IDIEM)")

    if st.button("⚙️ Generar 6. Actividades Extensas"):
        if not intro.strip() and not alcance.strip():
            st.warning("Por favor ingrese texto en la Introducción o en el Alcance Detallado antes de generar.")
        else:
            act_blocks = ["Para responder expresamente a cada uno de los puntos de prueba decretados por el Tribunal Arbitral, se contempla desarrollar las siguientes etapas y actividades:\n"]
            
            if "Designación por Tribunal" in tipo_estudio:
                act_blocks.append("Etapa A: Visita a terreno y verificación in situ\n")
                act_blocks.append("Considera la asistencia a una inspección en terreno por parte del Perito Senior y del Jefe de Proyecto IDIEM a las instalaciones objeto de la controversia. Se solicitará la presencia del Tribunal Arbitral y de las Partes con el fin de observar el estado real de las obras, tomar notas y recepcionar consultas. Durante la visita, IDIEM resguardará el estricto principio de neutralidad pericial, limitándose a la constatación de hechos empíricos sin emitir juzgamientos preliminares.\n")
                
                act_blocks.append("Etapa B: Análisis de los documentos del expediente y definición de la línea base contractual\n")
                act_blocks.append("Considera la revisión exhaustiva de todos los antecedentes allegados al expediente del proceso arbitral (contrato de construcción, bases de licitación, aclaraciones, ofertas, especificaciones técnicas, programas de obra oficiales y resoluciones). A partir de este análisis se establecerá la línea base contractual y el orden de prelación aplicable para la resolución técnica de las controversias.\n")
                
                act_blocks.append("Etapa C: Análisis de pertinencia técnica de los Puntos de Prueba\n")
                act_blocks.append("Considera la revisión sistemática de los registros contemporáneos de la obra (libros de obra, cartas formales, RDI, informes de inspección, minutas y estados de pago) para dar respuesta a cada punto de prueba, determinando la ocurrencia real de los hechos, el cumplimiento de las Especificaciones Técnicas, la factibilidad de reutilización de equipos, el origen de adicionales y la procedencia de retenciones o cobros de garantías.\n")

                act_blocks.append("Etapa D: Análisis retrospectivo de impacto en plazo (Ruta Crítica)\n")
                act_blocks.append("Realización de un análisis retrospectivo de retrasos sobre los programas maestros oficiales aprobados (Primavera P6 / MS Project), evaluando el efecto que cada evento validado tuvo sobre los hitos intermedios y la fecha de término, determinando la existencia de atrasos concurrentes o alteraciones de la secuencia constructiva.\n")

                act_blocks.append("Etapa E: Análisis de impactos económicos y perjuicios\n")
                act_blocks.append("Cuantificación objetiva de los mayores costos directos, indirectos, gastos generales proporcionales o sobrecostos por terminación de obras derivados de los puntos de prueba validados, realizando la homogeneización de monedas (CLP / UF / USD) según corresponda.\n")

                act_blocks.append("Etapa F: Elaboración del Informe Pericial Imparcial\n")
                act_blocks.append("Emisión de un Informe Técnico Pericial independiente, claro y debidamente fundado, redactado en lenguaje de ingeniería neutral, que dé respuesta expresa y ordenada a cada uno de los Puntos de Prueba del S.J.A., acompañado de sus respectivas carpetas y anexos de respaldo documental.\n")

            elif "Auditoría Normativa" in tipo_estudio:
                act_blocks.append("Etapa A: Revisión normativa y marco de cumplimiento\n")
                act_blocks.append("Identificación del marco legal, reglamentario y normativo sanitario aplicable a la infraestructura (p. ej. Decreto Supremo N° 45 MINSAL), construyendo la matriz de cumplimiento que sirva de base para el análisis pericial.\n")

                act_blocks.append("Etapa B: Análisis del grado de cumplimiento normativo y verificación técnica\n")
                act_blocks.append("Verificación técnica y métrica in situ de las condiciones de infraestructura (planos as-built, resoluciones sanitarias, permisos municipales e instalaciones críticas) identificando cumplimientos e incumplimientos verificables al momento relevante.\n")

                act_blocks.append("Etapa C: Definición y cuantificación de adecuaciones normativas\n")
                act_blocks.append("Identificación de brechas detectadas y cubicación económica de las obras necesarias para la normalización técnica de los recintos sobre bases de mercado objetivas.\n")

                act_blocks.append("Etapa D: Identificación de obras ejecutadas en periodos recientes\n")
                act_blocks.append("Análisis documental para distinguir entre labores de mantención ordinaria y adecuaciones normativas obligatorias ejecutadas, valorizando los costos incurridos.\n")

                act_blocks.append("Etapa E: Presentación del Informe Pericial al Tribunal\n")
                act_blocks.append("Entrega de un Informe Técnico Pericial imparcial y fundado que dé respuesta expresa a los puntos del alcance solicitado por la parte demandante o el tribunal.\n")

            elif "Pertinencia e Impacto en Plazo y Costos" in tipo_estudio:
                act_blocks.append("Etapa A: Análisis de pertinencia técnico-contractual de las situaciones reclamadas\n")
                act_blocks.append("Revisión de la línea base contractual y programática para verificar si cada evento reclamado constituye un cambio de condición respecto de lo originalmente pactado, construyendo la trazabilidad documental de respaldo.\n")

                act_blocks.append("Etapa B: Análisis de impacto en el programa de obras (Delay Analysis)\n")
                act_blocks.append("Evaluación sobre los programas de obra aprobados (Rev0/Rev1) mediante modelamiento de impactos en la ruta crítica para cuantificar las extensiones de plazo procedentes.\n")

                act_blocks.append("Etapa C: Cuantificación de mayores costos y Gastos Generales\n")
                act_blocks.append("Determinación de costos directos, indirectos y Gastos Generales extra proporcionales conforme a la normativa contractual aplicable.\n")

                act_blocks.append("Etapa D: Elaboración del Informe Final\n")
                act_blocks.append("Consolidación del estudio en un informe técnico imparcial y fundado con carpetas de respaldo contemporáneo.\n")

            else:
                act_blocks.append("Etapa A: Definición de la línea base contractual e identificación de hechos\n")
                act_blocks.append("Revisión de los antecedentes contractuales y del expediente para establecer los parámetros de comparación técnica.\n")

                act_blocks.append("Etapa B: Análisis técnico pericial y contrastación documental\n")
                act_blocks.append("Evaluación sistemática de los registros de obra, pruebas técnicas y mediciones de campo.\n")

                act_blocks.append("Etapa C: Cuantificación de impactos y variaciones\n")
                act_blocks.append("Determinación económica e impacto en plazo de las desviaciones identificadas.\n")

                act_blocks.append("Etapa D: Emisión del Informe Pericial IDIEM\n")
                act_blocks.append("Redacción del dictamen pericial neutral con sus anexos de respaldo.\n")

            st.session_state.auto_actividades = "\n".join(act_blocks)
            st.success("¡Actividades redactadas bajo el estándar de Peritaje por Designación Arbitral (CAM)!")

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
    excl2 = st.text_input("Exclusión 2:", value="Analizar materias o puntos de prueba no incluidos en la resolución pericial o alcance acordado.")
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

        if alcance.strip():
            oraciones = [s.strip() for s in alcance.replace("\n", ". ").split(".") if s.strip()]
            num_oraciones = max(1, int(len(oraciones) * 0.20))
            resumen_alcance_20 = ". ".join(oraciones[:num_oraciones]) + "."
        else:
            resumen_alcance_20 = "El presente peritaje comprende la evaluación técnica e independiente de los puntos de prueba decretados por el Tribunal Arbitral."

        lista_items_propuesta = []
        if actividades.strip():
            lines = actividades.split("\n")
            for line in lines:
                line_str = line.strip()
                if line_str.startswith("Etapa "):
                    lista_items_propuesta.append(line_str)
        
        if not lista_items_propuesta:
            lista_items_propuesta = [
                "Etapa A: Visita a terreno y verificación in situ",
                "Etapa B: Análisis de los documentos del expediente",
                "Etapa C: Análisis de pertinencia técnica de los Puntos de Prueba",
                "Etapa D: Análisis retrospectivo de impacto en plazo",
                "Etapa E: Análisis de impactos económicos",
                "Etapa F: Elaboración del Informe Pericial Imparcial"
            ]

        lista_introduccion_lineas = [l.strip() for l in intro.split("\n") if l.strip()]
        lista_alcance_lineas = [l.strip() for l in alcance.split("\n") if l.strip()]
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
            'TEXTO_INTRODUCCION': intro,
            'TEXTO_ALCANCE_DETALLADO': alcance,
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
