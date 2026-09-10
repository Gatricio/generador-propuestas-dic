import streamlit as st
import datetime
from docxtpl import DocxTemplate
from io import BytesIO

st.set_page_config(
    page_title="IDIEM - Generador de Propuestas",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
    <style>
    .main-header { font-size:24px; font-weight:bold; color:#002855; margin-bottom:2px; }
    .sub-header { font-size:14px; color:#555; margin-bottom: 20px; }
    .stButton>button { background-color: #0056B3; color: white; font-weight: bold; }
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

with tab1:
    st.subheader("Clasificación del Encargo")
    tipo_encargo = st.radio("Tipo de Servicio:", ["Informe Técnico de Parte (Cliente Directo)", "Peritaje Judicial / Arbitral CAM"])
    
    col1, col2 = st.columns(2)
    with col1:
        codigo = st.text_input("Código de Propuesta:", "PR.DIC.2026-020")
        cliente = st.text_input("Cliente / Razón Social:", "FLESAN S.A.")
        solicitante = st.text_input("Nombre Solicitante:", "Claudio García Beard")
        cargo_solicitante = st.text_input("Cargo Solicitante:", "Gerente de Proyecto")
    with col2:
        revision = st.text_input("Revisión N°:", "0")
        rut_cliente = st.text_input("RUT Cliente:", "76.259.040-9")
        email_solicitante = st.text_input("Email Solicitante:", "claudio.garcia@flesan.cl")
        rol_cam = st.text_input("Tribunal / Rol Arbitral (Solo CAM):", "N/A" if "Parte" in tipo_encargo else "Rol CAM N° 5043-2022")
    
    nombre_proyecto = st.text_input("Nombre del Proyecto / Referencia:", "Construcción Eje Sargento Menadier, Tramo 2")
    
    default_prop_title = "PERITAJE TÉCNICO ARBITRAL" if "CAM" in tipo_encargo else "INFORME TÉCNICO DE PERTINENCIA E IMPACTO EN PLAZO Y COSTOS"
    nombre_propuesta = st.text_input("Nombre Oficial de la Propuesta:", default_prop_title)

with tab2:
    st.subheader("Descripción del Conflicto y Propuesta Técnica")
    intro = st.text_area("4. Introducción / Contexto de la Obra:", 
                         "Mediante contrato suscrito entre las partes se encomendó la ejecución de la obra. Durante el desarrollo del proyecto surgieron controversias relacionadas con mayores gastos generales, sobrecostos y solicitudes de aumento de plazo...", height=100)
    
    alcance = st.text_area("5. Alcance Detallado (Conceptos a evaluar):", 
                          "(i) Gastos generales por plazo extraproporcional.\n(ii) Reajustabilidad de la oferta según normativas aplicables.\n(iii) Evaluación de impacto en plazo sobre la ruta crítica.", height=120)
    
    actividades = st.text_area("6. Actividades / Etapas Propuestas:", 
                              "Etapa A: Análisis de Pertinencia Técnica y Línea Base Contractual.\nEtapa B: Análisis del Impacto en Plazo (Time Impact Analysis - TIA).\nEtapa C: Cuantificación de Mayores Costos Directos e Indirectos.\nEtapa D: Elaboración del Informe Técnico Final.", height=120)

with tab3:
    st.subheader("Estimación de Recursos y Horas Hombre")
    meses = st.number_input("Plazo Total del Estudio (Meses):", value=2, min_value=1)
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        hh_asesor = st.number_input("HH / Mes Asesor Técnico (2.0 UF/HH):", value=15)
    with col_b:
        hh_jefe = st.number_input("HH / Mes Jefe de Proyecto (1.5 UF/HH):", value=40)
    with col_c:
        hh_analista = st.number_input("HH / Mes Analista Senior (1.0 UF/HH):", value=180)
    
    tot_hh = (hh_asesor + hh_jefe + hh_analista) * meses
    tot_uf = (hh_asesor * 2.0 + hh_jefe * 1.5 + hh_analista * 1.0) * meses
    
    st.info(f"**Total Horas Hombre:** {tot_hh} HH  |  **Monto Estimado:** {tot_uf:.1f} UF")

with tab4:
    st.subheader("Condiciones Comerciales y Emisión")
    forma_pago = st.selectbox("Estructura de Forma de Pago:", [
        "30% Anticipo | 30% Avance | 30% Borrador | 10% Informe Final",
        "40% Anticipo | 30% Borrador | 30% Informe Firmado",
        "50% Anticipo | 50% Informe Firmado (Estructura CAM)"
    ])
    
    condicion_pago = st.text_input("Condición de Pago:", "30 días desde fecha de emisión de factura")
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
            'ROL_CAM_O_TRIBUNAL': rol_cam,
            'FECHA_EMISION': datetime.date.today().strftime("%d/%m/%Y"),
            'SINTESIS_ALCANCE': alcance[:150] + "...",
            'SINTESIS_ITEMS': actividades[:150] + "...",
            'PLAZO_TEXTO': f"{meses} meses",
            'MONTO_UF_TOTAL': f"{tot_uf:.1f}",
            'MONTO_LETRAS_UF': f"{tot_uf:.1f} Unidades de Fomento",
            'ESTRUCTURA_FORMA_PAGO': forma_pago,
            'CONDICION_PAGO': condicion_pago,
            'CONSIDERACIONES_INICIALES': "Entrega completa de antecedentes al inicio del servicio.",
            'TEXTO_INTRODUCCION': intro,
            'TEXTO_ALCANCE_DETALLADO': alcance,
            'TEXTO_ACTIVIDADES_ETAPAS': actividades,
            'NOTA_IMPUESTOS_IVA': regimen_iva,
            'PROTOCOLO_COMUNICACION': "El canal oficial de comunicación será el Jefe de Proyecto asignado por IDIEM."
        }
        
        doc.render(contexto)
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    st.download_button(
        label="📥 Descargar Propuesta Emitida (.docx)",
        data=generar_documento_word(),
        file_name=f"Propuesta_IDIEM_{codigo}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
