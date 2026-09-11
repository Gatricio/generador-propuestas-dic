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
    tipo_encargo = st.radio("Tipo de Servicio:", ["Informe Técnico de Parte (Cliente Directo)", "Peritaje Judicial / Arbitral CAM"])
    
    col1, col2 = st.columns(2)
    with col1:
        codigo = st.text_input("Código de Propuesta:", value="", placeholder="Ej: PR.DIC.2026-040")
        cliente = st.text_input("Cliente / Razón Social:", value="", placeholder="Ej: Consorcio Icafal - L&D SpA")
        solicitante = st.text_input("Nombre Solicitante:", value="", placeholder="Ej: Alfredo Vial R.")
        cargo_solicitante = st.text_input("Cargo Solicitante:", value="", placeholder="Ej: Abogado representante")
    with col2:
        revision = st.text_input("Revisión N°:", value="0")
        rut_cliente = st.text_input("RUT Cliente:", value="", placeholder="Ej: 77.433.027-5")
        email_solicitante = st.text_input("Email Solicitante:", value="", placeholder="avial@amlv.cl")
        rol_cam = st.text_input("Tribunal / Rol Arbitral (Solo CAM):", value="", placeholder="Ej: Rol CAM N° 5043-2022")
    
    nombre_proyecto = st.text_input("Nombre del Proyecto / Referencia:", value="", placeholder="Ej: NORMALIZACIÓN HOSPITAL DR. LEOPOLDO ORTEGA DE CHILE CHICO")
    
    default_prop_title = "PERITAJE TÉCNICO ARBITRAL" if "CAM" in tipo_encargo else "INFORME TÉCNICO DE CUANTIFICACIÓN DE MAYORES COSTOS"
    nombre_propuesta = st.text_input("Nombre Oficial de la Propuesta:", value=default_prop_title)

# ---------------------------------------------------------
# PESTAÑA 2: ALCANCE Y CONTEXTO
# ---------------------------------------------------------
with tab2:
    st.subheader("Descripción del Conflicto y Propuesta Técnica")
    
    if "auto_actividades" not in st.session_state:
        st.session_state.auto_actividades = ""

    intro = st.text_area(
        "4. Introducción / Contexto de la Obra (Input Usuario):", 
        value="", 
        placeholder="Ingrese la introducción del caso, antecedentes del contrato, montos, plazos y convenios modificatorios...", 
        height=140
    )
    
    alcance = st.text_area(
        "5. Alcance Detallado (Conceptos a evaluar / Puntos de Prueba - Input Usuario):", 
        value="", 
        placeholder="Ingrese los puntos del alcance a evaluar...", 
        height=140
    )

    st.markdown("---")
    st.markdown("### ⚡ Generación Extensa de Actividades (Estándar Pericial IDIEM)")

    if st.button("⚙️ Generar 6. Actividades Extensas"):
        if not intro.strip() and not alcance.strip():
            st.warning("Por favor ingrese texto en la Introducción o en el Alcance Detallado antes de generar.")
        else:
            txt_comb = (intro + " " + alcance).lower()
            client_ref = cliente if cliente else "el Cliente / Consorcio"
            
            act_blocks = []
            act_blocks.append("Para desarrollar el alcance, se contempla desarrollar las siguientes etapas y actividades:\n")
            
            act_blocks.append("Etapa A: Análisis de pertinencia de las situaciones reclamadas\n")
            act_blocks.append("A.1 Análisis de antecedentes de la obra contratada")
            act_blocks.append(
                "Considera la revisión y análisis de los antecedentes contractuales, tales como las Bases de licitación, "
                "especificaciones técnicas, términos de referencia, presupuesto de la oferta, aclaraciones, consultas y respuestas, "
                f"entre otros documentos proporcionados por {client_ref} que estén disponibles para su revisión, para establecer la línea base "
                "del contrato en relación a los conceptos reclamados.\n"
            )
            
            act_blocks.append("A.2 Análisis de los convenios modificatorios")
            act_blocks.append(
                "En esta etapa se revisarán los convenios modificatorios y demás antecedentes contractuales disponibles, "
                "con el propósito de identificar y determinar los días correspondientes a aumentos de plazo extra proporcionales. "
                "Para cada uno de estos aumentos, IDIEM analizará los antecedentes técnicos, contractuales y de ejecución de las obras "
                "que permitan identificar las circunstancias que efectivamente dieron origen a su otorgamiento.\n"
            )
            
            act_blocks.append("A.3 Análisis y validación de las situaciones reclamadas")
            act_blocks.append(
                "Se considerará la revisión y análisis de los registros documentales de la obra, con el propósito de constatar la existencia "
                "de las situaciones reclamadas respecto de la línea base establecida en A.1. De acuerdo con las situaciones indicadas "
                f"por {client_ref}, se desarrollarán los análisis específicos de obras extraordinarias, pérdidas de productividad, "
                "garantías, anticipos, multas, reajustes y valores proforma según corresponda.\n"
            )

            act_blocks.append("Etapa B: Estimación de los Gastos Generales Extra proporcionales\n")
            act_blocks.append(
                "Esta etapa considera la determinación y cuantificación de los gastos generales asociados al período de plazo "
                "extra proporcional previamente identificado y validado en la Etapa A. Se estimarán los gastos generales mediante "
                "el 12% establecido en el artículo 147 del DS N° 75 (RCOP) o sobre la base de la oferta del Contratista.\n"
            )

            act_blocks.append("Etapa C: Cuantificación de mayores costos\n")
            act_blocks.append(
                "Esta etapa considera la determinación y cuantificación de los mayores costos efectivamente incurridos por el Contratista "
                "como consecuencia de las situaciones reclamadas y validadas en las etapas anteriores (costos directos, pérdida de productividad, "
                "costos financieros y levantamiento de observaciones).\n"
            )

            act_blocks.append("Etapa D: Elaboración del Informe Final\n")
            act_blocks.append(
                "A partir de los análisis indicados en las etapas anteriores, se emitirá un informe final junto a sus anexos de respaldos."
            )

            st.session_state.auto_actividades = "\n".join(act_blocks)
            st.success("¡Actividades redactadas exitosamente!")

    st.markdown("---")
    actividades = st.text_area(
        "6. Actividades / Etapas Propuestas (Output Generado):", 
        value=st.session_state.auto_actividades, 
        height=280
    )

# ---------------------------------------------------------
# PESTAÑA 3: HORAS HOMBRE Y PERFILES (Organograma Dinámico)
# ---------------------------------------------------------
with tab3:
    st.subheader("Estimación de Recursos y Perfiles Profesionales")
    meses_val = st.number_input("Plazo Total del Estudio (Meses):", min_value=0.5, step=0.5, value=3.0)
    
    col_hdr1, col_hdr2, col_hdr3 = st.columns([2, 1, 1])
    with col_hdr1: st.markdown("**Categoría Profesional**")
    with col_hdr2: st.markdown("**HH / Mes**")
    with col_hdr3: st.markdown("**Tarifa (UF/HH)**")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Asesor Técnico / Revisor")
    with c2: hh_asesor = st.number_input("HH Asesor", min_value=0, value=10, label_visibility="collapsed")
    with c3: tar_asesor = st.number_input("Tarifa Asesor", min_value=0.0, value=2.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Jefe de Proyecto / Asesoría")
    with c2: hh_jefe = st.number_input("HH Jefe", min_value=0, value=60, label_visibility="collapsed")
    with c3: tar_jefe = st.number_input("Tarifa Jefe", min_value=0.0, value=1.5, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 1")
    with c2: hh_an1 = st.number_input("HH Profesional 1", min_value=0, value=180, label_visibility="collapsed")
    with c3: tar_an1 = st.number_input("Tarifa Prof. 1", min_value=0.0, value=1.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 2")
    with c2: hh_an2 = st.number_input("HH Profesional 2", min_value=0, value=180, label_visibility="collapsed")
    with c3: tar_an2 = st.number_input("Tarifa Prof. 2", min_value=0.0, value=1.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 3")
    with c2: hh_an3 = st.number_input("HH Profesional 3", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an3 = st.number_input("Tarifa Prof. 3", min_value=0.0, value=1.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 4")
    with c2: hh_an4 = st.number_input("HH Profesional 4", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an4 = st.number_input("Tarifa Prof. 4", min_value=0.0, value=1.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 5")
    with c2: hh_an5 = st.number_input("HH Profesional 5", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an5 = st.number_input("Tarifa Prof. 5", min_value=0.0, value=1.0, step=0.1, label_visibility="collapsed")

    # Conteo dinámico de profesionales activos
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
    
    # --- SECCIÓN NUEVA DE EXCLUSIONES (11) ---
    st.markdown("#### 11. Exclusiones del Servicio (4 Espacios Editables)")
    st.caption("Escriba o modifique las exclusiones específicas para este encargo:")
    
    excl1 = st.text_input("Exclusión 1:", value="Visitas a terreno.")
    excl2 = st.text_input("Exclusión 2:", value="Analizar otras situaciones no indicadas en el alcance de la presente propuesta.")
    excl3 = st.text_input("Exclusión 3:", value="Cualquier otra situación no indicada en el alcance, será considerada como adicional y se entregará el plazo y costo de incluirla dentro de este.")
    excl4 = st.text_input("Exclusión 4 (Opcional):", value="")

    st.markdown("---")
    st.markdown("#### 13. Estructura de Pagos (5 Hitos Personalizables)")
    
    col_t1, col_p1 = st.columns([3, 1])
    with col_t1: titulo_h1 = st.text_input("Título Hito 1:", value="al momento de aceptar la presente propuesta")
    with col_p1: pct_h1 = st.number_input("% Hito 1:", min_value=0, max_value=100, value=30)

    col_t2, col_p2 = st.columns([3, 1])
    with col_t2: titulo_h2 = st.text_input("Título Hito 2:", value="contra la presentación de avance 1")
    with col_p2: pct_h2 = st.number_input("% Hito 2:", min_value=0, max_value=100, value=20)

    col_t3, col_p3 = st.columns([3, 1])
    with col_t3: titulo_h3 = st.text_input("Título Hito 3:", value="contra la presentación de avance 2")
    with col_p3: pct_h3 = st.number_input("% Hito 3:", min_value=0, max_value=100, value=20)

    col_t4, col_p4 = st.columns([3, 1])
    with col_t4: titulo_h4 = st.text_input("Título Hito 4:", value="contra entrega de informe borrador")
    with col_p4: pct_h4 = st.number_input("% Hito 4:", min_value=0, max_value=100, value=20)

    col_t5, col_p5 = st.columns([3, 1])
    with col_t5: titulo_h5 = st.text_input("Título Hito 5:", value="al momento de entregar informe final")
    with col_p5: pct_h5 = st.number_input("% Hito 5:", min_value=0, max_value=100, value=10)

    tot_pct = pct_h1 + pct_h2 + pct_h3 + pct_h4 + pct_h5
    if tot_pct != 100:
        st.warning(f"Atención: Los porcentajes ingresados suman {tot_pct}%. Deben completar exactamente el 100%.")
    else:
        st.success("Estructura de pagos válida (Suma 100%).")

    # Lista consolidada de forma de pago
    hitos_list = []
    if pct_h1 > 0: hitos_list.append(f"{pct_h1}% {titulo_h1}.")
    if pct_h2 > 0: hitos_list.append(f"{pct_h2}% {titulo_h2}.")
    if pct_h3 > 0: hitos_list.append(f"{pct_h3}% {titulo_h3}.")
    if pct_h4 > 0: hitos_list.append(f"{pct_h4}% {titulo_h4}.")
    if pct_h5 > 0: hitos_list.append(f"{pct_h5}% {titulo_h5}.")
    forma_pago_texto = "\n".join(hitos_list)

    condicion_pago = st.text_input("Condición de Pago (Días):", value="30 días desde fecha de emisión de factura.")
    
    regimen_iva = st.selectbox("Régimen de Impuestos / IVA:", [
        "Exento de IVA (Ley N° 21.094 sobre Universidades Estatales)",
        "Afecto a IVA (Recargo del 19% según Ley N° 21.420)"
    ])

    st.markdown("---")
    
    # Generador final mapeado a la Plantilla Oficial de 19 Capítulos
    def generar_documento_word():
        doc = DocxTemplate("Plantilla_Maestra_IDIEM_v2.docx")
        
        # Construcción de la lista de exclusiones para el Word
        lista_exclusiones = []
        if excl1.strip(): lista_exclusiones.append(excl1.strip())
        if excl2.strip(): lista_exclusiones.append(excl2.strip())
        if excl3.strip(): lista_exclusiones.append(excl3.strip())
        if excl4.strip(): lista_exclusiones.append(excl4.strip())

        contexto = {
            'CODIGO_PROPUESTA': codigo,
            'NUM_REVISION': revision,
            'NOMBRE_PROPUESTA': nombre_propuesta,
            'NOMBRE_CLIENTE': cliente,
            'RUT_CLIENTE': rut_cliente,
            'NOMBRE_SOLICITANTE': solicitante,
            'CARGO_SOLICITANTE': cargo_solicitante,
            'EMAIL_SOLICITANTE': email_solicitante,
            'NOMBRE_PROYECTO': nombre_proyecto,
            'ROL_CAM_O_TRIBUNAL': rol_cam if rol_cam else "N/A",
            'FECHA_EMISION': datetime.date.today().strftime("%d-%m-%Y"),
            'PLAZO_TEXTO': f"{meses_val:.0f} meses" if meses_val.is_integer() else f"{meses_val} meses",
            'NUM_PROFESIONALES_ASESORIA': f"{num_profesionales_activos} Profesionales de Asesoría",
            'MONTO_UF_TOTAL': f"{tot_uf:,.0f}".replace(",", "."),
            'ESTRUCTURA_FORMA_PAGO': forma_pago_texto,
            'CONDICION_PAGO': condicion_pago,
            'TEXTO_INTRODUCCION': intro,
            'TEXTO_ALCANCE_DETALLADO': alcance,
            'TEXTO_ACTIVIDADES_ETAPAS': actividades,
            'LISTA_EXCLUSIONES': lista_exclusiones,
            'NOTA_IMPUESTOS_IVA': regimen_iva,
            'HH_ASESOR': hh_asesor, 'TAR_ASESOR': f"{tar_asesor:.1f}", 'TOT_HH_ASESOR': int(hh_asesor * meses_val), 'TOT_UF_ASESOR': int(hh_asesor * tar_asesor * meses_val),
            'HH_JEFE': hh_jefe, 'TAR_JEFE': f"{tar_jefe:.1f}", 'TOT_HH_JEFE': int(hh_jefe * meses_val), 'TOT_UF_JEFE': int(hh_jefe * tar_jefe * meses_val),
            'HH_AN1': hh_an1, 'TAR_AN1': f"{tar_an1:.1f}", 'TOT_HH_AN1': int(hh_an1 * meses_val), 'TOT_UF_AN1': int(hh_an1 * tar_an1 * meses_val),
            'HH_AN2': hh_an2, 'TAR_AN2': f"{tar_an2:.1f}", 'TOT_HH_AN2': int(hh_an2 * meses_val), 'TOT_UF_AN2': int(hh_an2 * tar_an2 * meses_val),
            'PCT_H1': pct_h1, 'TIT_H1': titulo_h1, 'UF_H1': int(tot_uf * (pct_h1/100)),
            'PCT_H2': pct_h2, 'TIT_H2': titulo_h2, 'UF_H2': int(tot_uf * (pct_h2/100)),
            'PCT_H3': pct_h3, 'TIT_H3': titulo_h3, 'UF_H3': int(tot_uf * (pct_h3/100)),
            'PCT_H4': pct_h4, 'TIT_H4': titulo_h4, 'UF_H4': int(tot_uf * (pct_h4/100)),
            'PCT_H5': pct_h5, 'TIT_H5': titulo_h5, 'UF_H5': int(tot_uf * (pct_h5/100)),
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
