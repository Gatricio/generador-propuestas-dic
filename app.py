import streamlit as st
import datetime
from docxtpl import DocxTemplate
from io import BytesIO
import google.generativeai as genai

# Configuración de página
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

st.markdown('<div class="main-header">IDIEM — UNIVERSIDAD DE CHILE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">División de Ingeniería Contractual | Generador Web de Ofertas Técnicas y Peritajes</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Identificación y Tipo", 
    "2. Alcance y Contexto", 
    "3. Horas Hombre y Perfiles",
    "4. Oferta Económica y Descarga"
])

# ---------------------------------------------------------
# PESTAÑA 1: IDENTIFICACIÓN Y TIPO
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
        rol_cam = st.text_input("Tribunal / Rol Arbitral (Solo CAM):", value="", placeholder="Ej: Rol CAM N° 5043-2022")
    
    nombre_proyecto = st.text_input("Nombre del Proyecto / Referencia:", value="", placeholder="Ej: Construcción Obra / Proyecto")
    
    default_prop_title = "PERITAJE TÉCNICO ARBITRAL" if "CAM" in tipo_encargo else "INFORME TÉCNICO DE PERTINENCIA E IMPACTO EN PLAZO Y COSTOS"
    nombre_propuesta = st.text_input("Nombre Oficial de la Propuesta:", value=default_prop_title)

# ---------------------------------------------------------
# PESTAÑA 2: ALCANCE Y CONTEXTO (Basado en Punteo de Conceptos)
# ---------------------------------------------------------
with tab2:
    st.subheader("Descripción del Conflicto y Propuesta Técnica")
    
    if "auto_intro" not in st.session_state:
        st.session_state.auto_intro = ""
    if "auto_actividades" not in st.session_state:
        st.session_state.auto_actividades = ""

    # 4. Alcance Detallado primero para usarlo de input
    alcance = st.text_area(
        "4. Alcance Detallado (Conceptos a evaluar / Puntos de Prueba):", 
        value="", 
        placeholder="Escriba o pegue un punteo de los conceptos a evaluar. Ej:\n- Análisis de mayores gastos generales extraproporcionales\n- Análisis de sobretiempo y pérdida de productividad\n- Actualización de precios mediante fórmula polinómica\n- Análisis forense de plazo (Time Impact Analysis)", 
        height=140
    )

    st.markdown("---")
    st.markdown("### ⚡ Generación Inteligente de Texto (Opcional)")
    st.caption("Con base en los conceptos ingresados arriba en el Alcance, la IA redactará automáticamente el contexto formal de la Introducción y el desglose de Actividades.")

    if st.button("🤖 Redactar Introducción y Actividades a partir del Alcance"):
        if not alcance.strip():
            st.warning("Por favor escriba al menos un concepto en el campo '4. Alcance Detallado' antes de generar.")
        else:
            with st.spinner("Redactando propuesta técnica en lenguaje de ingeniería contractual..."):
                try:
                    api_key = st.secrets.get("GEMINI_API_KEY", "")
                    if not api_key:
                        st.error("Error: No se encontró la API Key en los Secrets de Streamlit.")
                    else:
                        genai.configure(api_key=api_key)
                        
                        prompt_conceptos = f"""
                        Actúa como un Perito e Ingeniero experto de la División de Ingeniería Contractual de IDIEM (Universidad de Chile).
                        
                        DATOS DEL PROYECTO:
                        - Tipo de encargo: {tipo_encargo}
                        - Nombre del proyecto: {nombre_proyecto if nombre_proyecto else 'el proyecto en estudio'}
                        - Conceptos a evaluar (Alcance):
                        {alcance}
                        
                        INSTRUCCIONES:
                        Genera una propuesta técnica formal manteniendo un tono neutral, estrictamente técnico e imparcial. 
                        Debes devolver exactamente este formato de dos secciones:
                        
                        SECCION_INTRO:
                        (Redacta un párrafo continuo formal para la Sección 5 'Introducción' introduciendo el proyecto, la solicitud de estudio y el contexto contractual de las discrepancias basadas en los conceptos a evaluar).
                        
                        SECCION_ACTIVIDADES:
                        (Propón el desglose ordenado por etapas para la Sección 6 'Actividades', agrupando los conceptos en Etapa A: Análisis de Pertinencia y Línea Base, Etapa B: Evaluación de Plazo o Costos según corresponda, y Etapa C/D: Elaboración de Informe Técnico Final).
                        """
                        
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(prompt_conceptos)
                        texto_res = response.text
                        
                        if "SECCION_ACTIVIDADES:" in texto_res:
                            partes = texto_res.split("SECCION_ACTIVIDADES:")
                            st.session_state.auto_intro = partes[0].replace("SECCION_INTRO:", "").strip()
                            st.session_state.auto_actividades = partes[1].strip()
                        else:
                            st.session_state.auto_intro = texto_res
                            st.session_state.auto_actividades = ""
                            
                        st.success("¡Introducción y Actividades generadas correctamente!")
                except Exception as e:
                    st.error(f"Error al generar con IA: {e}")

    st.markdown("---")
    intro = st.text_area("5. Introducción / Contexto de la Obra:", value=st.session_state.auto_intro, placeholder="Ingrese o genere la introducción del caso...", height=130)
    actividades = st.text_area("6. Actividades / Etapas Propuestas:", value=st.session_state.auto_actividades, placeholder="Ingrese o genere las etapas del estudio...", height=150)

# ---------------------------------------------------------
# PESTAÑA 3: HORAS HOMBRE Y PERFILES
# ---------------------------------------------------------
with tab3:
    st.subheader("Estimación de Recursos y Tarifas Editables")
    meses_val = st.number_input("Plazo Total del Estudio (Meses):", min_value=0.5, step=0.5, value=1.0)
    
    col_hdr1, col_hdr2, col_hdr3 = st.columns([2, 1, 1])
    with col_hdr1: st.markdown("**Categoría Profesional**")
    with col_hdr2: st.markdown("**HH / Mes**")
    with col_hdr3: st.markdown("**Tarifa (UF/HH)**")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Asesor Técnico / Revisor")
    with c2: hh_asesor = st.number_input("HH Asesor", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_asesor = st.number_input("Tarifa Asesor", min_value=0.0, value=2.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Jefe de Proyecto / Asesoría")
    with c2: hh_jefe = st.number_input("HH Jefe", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_jefe = st.number_input("Tarifa Jefe", min_value=0.0, value=1.5, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 1")
    with c2: hh_an1 = st.number_input("HH Analista 1", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an1 = st.number_input("Tarifa Analista 1", min_value=0.0, value=1.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 2 (Opcional)")
    with c2: hh_an2 = st.number_input("HH Analista 2", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an2 = st.number_input("Tarifa Analista 2", min_value=0.0, value=1.0, step=0.1, label_visibility="collapsed")

    tot_hh = (hh_asesor + hh_jefe + hh_an1 + hh_an2) * meses_val
    tot_uf = (hh_asesor * tar_asesor + hh_jefe * tar_jefe + hh_an1 * tar_an1 + hh_an2 * tar_an2) * meses_val
    
    st.markdown("---")
    st.info(f"**Total Horas Hombre:** {tot_hh:.0f} HH  |  **Monto Total Calculado:** {tot_uf:.1f} UF")

# ---------------------------------------------------------
# PESTAÑA 4: OFERTA ECONÓMICA Y DESCARGA
# ---------------------------------------------------------
with tab4:
    st.subheader("Condiciones Comerciales y Estructura de Pagos")
    
    st.markdown("#### Estructura de Pagos Personalizada (%)")
    cp1, cp2, cp3, cp4 = st.columns(4)
    with cp1: pct_ant = st.number_input("% Anticipo:", min_value=0, max_value=100, value=30 if "Parte" in tipo_encargo else 50)
    with cp2: pct_av = st.number_input("% Avance / Pertinencia:", min_value=0, max_value=100, value=30 if "Parte" in tipo_encargo else 0)
    with cp3: pct_borr = st.number_input("% Informe Borrador:", min_value=0, max_value=100, value=30 if "Parte" in tipo_encargo else 0)
    with cp4: pct_fin = st.number_input("% Informe Final / Firmado:", min_value=0, max_value=100, value=10 if "Parte" in tipo_encargo else 50)
    
    tot_pct = pct_ant + pct_av + pct_borr + pct_fin
    if tot_pct != 100:
        st.warning(f"Los porcentajes ingresados suman {tot_pct}%. Deben completar el 100%.")
    else:
        st.success("Estructura de pagos válida (100%).")

    partes_pago = []
    if pct_ant > 0: partes_pago.append(f"{pct_ant}% al momento de la orden de compra / anticipo")
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
        file_name=f"Propuesta_IDIEM_{codigo if codigo else 'Borrador'}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
