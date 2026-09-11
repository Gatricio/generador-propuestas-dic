import streamlit as st
import datetime
from docxtpl import DocxTemplate
from io import BytesIO
import google.generativeai as genai

# Configuración inicial de Streamlit
st.set_page_config(
    page_title="IDIEM - Generador de Propuestas",
    page_icon="📄",
    layout="wide"
)

# Estilos visuales institucionales IDIEM
st.markdown("""
    <style>
    .main-header { font-size:24px; font-weight:bold; color:#002855; margin-bottom:2px; }
    .sub-header { font-size:14px; color:#555; margin-bottom: 20px; }
    .stButton>button { background-color: #0056B3; color: white; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">IDIEM — UNIVERSIDAD DE CHILE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">División de Ingeniería Contractual | Generador Web de Ofertas Técnicas y Peritajes</div>', unsafe_allow_html=True)

# Pestañas principales
tab1, tab2, tab3, tab4 = st.tabs([
    "1. Identificación y Tipo", 
    "2. Alcance y Contexto", 
    "3. Horas Hombre y Perfiles",
    "4. Oferta Económica y Descarga"
])

# ---------------------------------------------------------
# PESTAÑA 1: IDENTIFICACIÓN Y TIPO (Campos Limpios)
# ---------------------------------------------------------
with tab1:
    st.subheader("Clasificación del Encargo")
    tipo_encargo = st.radio("Tipo de Servicio:", ["Informe Técnico de Parte (Cliente Directo)", "Peritaje Judicial / Arbitral CAM"])
    
    col1, col2 = st.columns(2)
    with col1:
        codigo = st.text_input("Código de Propuesta:", value="", placeholder="Ej: PR.DIC.2026-001")
        cliente = st.text_input("Cliente / Razón Social:", value="", placeholder="Ej: Nombre Empresa o Cliente")
        solicitante = st.text_input("Nombre Solicitante:", value="", placeholder="Ej: Nombre del contacto / Abogado")
        cargo_solicitante = st.text_input("Cargo Solicitante:", value="", placeholder="Ej: Gerente / Juez Árbitro")
    with col2:
        revision = st.text_input("Revisión N°:", value="0")
        rut_cliente = st.text_input("RUT Cliente:", value="", placeholder="Ej: 76.xxx.xxx-x")
        email_solicitante = st.text_input("Email Solicitante:", value="", placeholder="correo@ejemplo.cl")
        rol_cam = st.text_input("Tribunal / Rol Arbitral (Solo CAM):", value="" if "Parte" in tipo_encargo else "", placeholder="Ej: Rol CAM N° 5043-2022")
    
    nombre_proyecto = st.text_input("Nombre del Proyecto / Referencia:", value="", placeholder="Ej: Construcción Obra / Proyecto")
    
    default_prop_title = "PERITAJE TÉCNICO ARBITRAL" if "CAM" in tipo_encargo else "INFORME TÉCNICO DE PERTINENCIA E IMPACTO EN PLAZO Y COSTOS"
    nombre_propuesta = st.text_input("Nombre Oficial de la Propuesta:", value=default_prop_title)

# ---------------------------------------------------------
# PESTAÑA 2: ALCANCE Y CONTEXTO (+ Asistente IA)
# ---------------------------------------------------------
with tab2:
    st.subheader("Descripción del Conflicto y Propuesta Técnica")
    
    # Módulo de lectura con IA para generación automática
    st.markdown("### 🤖 Asistente de Lectura Automática con IA (Opcional)")
    st.caption("Carga un archivo de respaldo (contrato, orden de compra, carta, correo o reclamo) para redactar la Introducción y las Actividades automáticamente.")
    
    uploaded_file = st.file_uploader("Cargar documento de antecedentes (PDF, TXT, DOCX):", type=["pdf", "txt", "docx"])
    
    if "auto_intro" not in st.session_state:
        st.session_state.auto_intro = ""
    if "auto_actividades" not in st.session_state:
        st.session_state.auto_actividades = ""

    if uploaded_file is not None:
        if st.button("Analizar Documento y Generar Texto con IA"):
            with st.spinner("Procesando y analizando antecedente técnico con Gemini..."):
                try:
                    # Lectura básica del texto del archivo cargado
                    text_content = uploaded_file.read().decode("utf-8", errors="ignore")
                    
                    # Llamada a Gemini para estructuración técnico-contractual
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    prompt_intro = f"Actúa como Contract Manager de IDIEM. Con base en este documento, redacta una Introducción técnica breve (Sección 4 de propuesta) describiendo el contrato, las partes y la controversia:\n{text_content[:4000]}"
                    prompt_act = f"Actúa como Contract Manager de IDIEM. Con base en este documento, propone las Actividades en Etapas (Etapa A: Pertinencia, Etapa B: Plazo, etc.) para la propuesta:\n{text_content[:4000]}"
                    
                    resp_intro = model.generate_content(prompt_intro)
                    resp_act = model.generate_content(prompt_act)
                    
                    st.session_state.auto_intro = resp_intro.text
                    st.session_state.auto_actividades = resp_act.text
                    st.success("¡Análisis completado! Se han rellenado las secciones de Introducción y Actividades.")
                except Exception as e:
                    st.error(f"Error al analizar con IA: {e}")

    intro = st.text_area("4. Introducción / Contexto de la Obra:", value=st.session_state.auto_intro, placeholder="Ingrese o genere la introducción del caso...", height=120)
    
    alcance = st.text_area("5. Alcance Detallado (Conceptos a evaluar):", value="", placeholder="Ingrese los conceptos reclamados o los Puntos de Prueba...", height=120)
    
    actividades = st.text_area("6. Actividades / Etapas Propuestas:", value=st.session_state.auto_actividades, placeholder="Ingrese las etapas del estudio...", height=140)

# ---------------------------------------------------------
# PESTAÑA 3: HORAS HOMBRE Y PERFILES (Valores Editables)
# ---------------------------------------------------------
with tab3:
    st.subheader("Estimación de Recursos y Tarifas Editables")
    meses_val = st.number_input("Plazo Total del Estudio (Meses):", min_value=1.0, step=0.5, value=1.0)
    
    col_hdr1, col_hdr2, col_hdr3 = st.columns([2, 1, 1])
    with col_hdr1:
        st.markdown("**Categoría Profesional**")
    with col_hdr2:
        st.markdown("**HH / Mes**")
    with col_hdr3:
        st.markdown("**Tarifa (UF/HH)**")

    # Asesor Técnico
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Asesor Técnico / Revisor")
    with c2: hh_asesor = st.number_input("HH Asesor", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_asesor = st.number_input("Tarifa Asesor", min_value=0.0, value=2.0, step=0.1, label_visibility="collapsed")

    # Jefe de Proyecto
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Jefe de Proyecto / Asesoría")
    with c2: hh_jefe = st.number_input("HH Jefe", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_jefe = st.number_input("Tarifa Jefe", min_value=0.0, value=1.5, step=0.1, label_visibility="collapsed")

    # Profesional 1
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 1")
    with c2: hh_an1 = st.number_input("HH Analista 1", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an1 = st.number_input("Tarifa Analista 1", min_value=0.0, value=1.0, step=0.1, label_visibility="collapsed")

    # Profesional 2
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 2 (Opcional)")
    with c2: hh_an2 = st.number_input("HH Analista 2", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an2 = st.number_input("Tarifa Analista 2", min_value=0.0, value=1.0, step=0.1, label_visibility="collapsed")

    # Totales Calculados
    tot_hh = (hh_asesor + hh_jefe + hh_an1 + hh_an2) * meses_val
    tot_uf = (hh_asesor * tar_asesor + hh_jefe * tar_jefe + hh_an1 * tar_an1 + hh_an2 * tar_an2) * meses_val
    
    st.markdown("---")
    st.info(f"**Total Horas Hombre:** {tot_hh:.0f} HH  |  **Monto Total Calculado:** {tot_uf:.1f} UF")

# ---------------------------------------------------------
# PESTAÑA 4: OFERTA ECONÓMICA Y DESCARGA (Pago Editable)
# ---------------------------------------------------------
with tab4:
    st.subheader("Condiciones Comerciales y Estructura de Pagos Editables")
    
    st.markdown("#### Estructura de Pagos Personalizada (%)")
    cp1, cp2, cp3, cp4 = st.columns(4)
    with cp1:
        pct_ant = st.number_input("% Anticipo:", min_value=0, max_value=100, value=30 if "Parte" in tipo_encargo else 50)
    with cp2:
        pct_av = st.number_input("% Avance / Pertinencia:", min_value=0, max_value=100, value=30 if "Parte" in tipo_encargo else 0)
    with cp3:
        pct_borr = st.number_input("% Informe Borrador:", min_value=0, max_value=100, value=30 if "Parte" in tipo_encargo else 0)
    with cp4:
        pct_fin = st.number_input("% Informe Final / Firmado:", min_value=0, max_value=100, value=10 if "Parte" in tipo_encargo else 50)
    
    tot_pct = pct_ant + pct_av + pct_borr + pct_fin
    if tot_pct != 100:
        st.warning(f"Atención: Los porcentajes de pago ingresados suman {tot_pct}%. Deben sumar el 100%.")
    else:
        st.success("Estructura de pagos válida (Suma 100%).")

    # Construcción de la cadena de forma de pago
    partes_pago = []
    if pct_ant > 0: partes_pago.append(f"{pct_ant}% al momento de aceptar / anticipo")
    if pct_av > 0: partes_pago.append(f"{pct_av}% contra avance de pertinencia")
    if pct_borr > 0: partes_pago.append(f"{pct_borr}% contra entrega informe borrador")
    if pct_fin > 0: partes_pago.append(f"{pct_fin}% al momento de entregar informe final")
    forma_pago_texto = " / ".join(partes_pago)

    condicion_pago = st.text_input("Condición de Pago (Días):", value="", placeholder="Ej: 30 días desde fecha de emisión de factura")
    
    regimen_iva = st.selectbox("Régimen de Impuestos / IVA:", [
        "Exento de IVA (Ley N° 21.094 sobre Universidades Estatales)",
        "Afecto a IVA (Recargo del 19% según Ley N° 21.420)"
    ])

    st.markdown("---")
    
    # Generador final Word
    def generar_documento_word():
        doc = DocxTemplate("Plantilla_Maestra_IDIEM_v2.docx")
        
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
            'FECHA_EMISION': datetime.date.today().strftime("%d/%m/%Y"),
            'SINTESIS_ALCANCE': alcance[:150] + "..." if alcance else "",
            'SINTESIS_ITEMS': actividades[:150] + "..." if actividades else "",
            'PLAZO_TEXTO': f"{meses_val} meses",
            'MONTO_UF_TOTAL': f"{tot_uf:.1f}",
            'MONTO_LETRAS_UF': f"{tot_uf:.1f} Unidades de Fomento",
            'ESTRUCTURA_FORMA_PAGO': forma_pago_texto,
            'CONDICION_PAGO': condicion_pago,
            'CONSIDERACIONES_INICIALES': "Entrega completa de antecedentes al inicio del servicio.",
            'TEXTO_INTRODUCCION': intro,
            'TEXTO_ALCANCE_DETALLADO': alcance,
            'TEXTO_ACTIVIDADES_ETAPAS': actividades,
            'NOTA_IMPUESTOS_IVA': regimen_iva,
            'PROTOCOLO_COMUNICACION': "Toda comunicación formal se realizará vía correo electrónico con el Jefe de Proyecto." if "Parte" in tipo_encargo else "Toda comunicación entre IDIEM y las partes será a través del Tribunal Arbitral."
        }
        
        doc.render(contexto)
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    st.download_button(
        label="📥 Descargar Propuesta Emitida (.docx)",
        data=generar_documento_word(),
        file_name=f"Propuesta_IDIEM_{codigo if codigo else 'Draft'}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
