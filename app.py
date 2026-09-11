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
# APLICACIÓN PRINCIPAL (ACCESO PERMITIDO)
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
# PESTAÑA 2: ALCANCE Y CONTEXTO (Input: 4 y 5 | Output: 6)
# ---------------------------------------------------------
with tab2:
    st.subheader("Descripción del Conflicto y Propuesta Técnica")
    
    if "auto_actividades" not in st.session_state:
        st.session_state.auto_actividades = ""

    # Inputs escritos/ingresados por el usuario
    intro = st.text_area(
        "4. Introducción / Contexto de la Obra (Input Usuario):", 
        value="", 
        placeholder="Ingrese la introducción del caso, contexto del proyecto y controversia...", 
        height=130
    )
    
    alcance = st.text_area(
        "5. Alcance Detallado (Conceptos a evaluar / Puntos de Prueba - Input Usuario):", 
        value="", 
        placeholder="Escriba o pegue el punteo de los conceptos a evaluar o Puntos de Prueba. Ej:\n- Análisis de mayores gastos generales extraproporcionales\n- Impacto en plazo sobre ruta crítica (TIA)\n- Reajuste polinómico", 
        height=140
    )

    st.markdown("---")
    st.markdown("### ⚡ Generación Automática de Actividades / Etapas")
    st.caption("Presione el botón para estructurar automáticamente el desglose de Actividades (Sección 6) con base en la Introducción y el Alcance ingresados.")

    if st.button("⚙️ Generar 6. Actividades / Etapas Propuestas"):
        if not intro.strip() and not alcance.strip():
            st.warning("Por favor ingrese texto en la Introducción o en el Alcance Detallado antes de generar las Actividades.")
        else:
            texto_base = (intro + " " + alcance).lower()
            
            # Generar Etapas Estructuradas automáticamente
            act_list = [
                "Etapa A: Recopilación, Auditoría Documental y Línea Base Contractual",
                "  • Auditoría e inventario sistemático de la documentación técnica y contractual del proyecto.",
                "  • Revisión de la línea base contractual y verificación de la pertinencia técnica de las reclamaciones."
            ]
            
            # Etapa B: Ajustada dinámicamente según palabras clave detectadas
            act_list.append("\nEtapa B: Análisis Técnico Especializado y Cuantificación de Impactos")
            
            if any(k in texto_base for k in ["plazo", "atraso", "critica", "tia", "cronograma"]):
                act_list.append("  • Análisis forense de plazo e impacto en la ruta crítica mediante metodología Time Impact Analysis (TIA).")
            if any(k in texto_base for k in ["gasto", "costo", "sobrecosto", "general", "directo"]):
                act_list.append("  • Auditoría y cuantificación empírica de mayores costos directos y gastos generales extraproporcionales.")
            if any(k in texto_base for k in ["reajuste", "polinom", "precio", "indice"]):
                act_list.append("  • Evaluación de la reajustabilidad de precios y aplicación de fórmulas polinómicas contractuales.")
            if not any(k in texto_base for k in ["plazo", "gasto", "costo", "reajuste"]):
                act_list.append("  • Evaluación técnica independiente y fundada de las discrepancias señaladas en el alcance.")

            act_list.extend([
                "\nEtapa C: Elaboración y Emisión de Entregables",
                "  • Elaboración y revisión del Informe Técnico Borrador.",
                "  • Emisión del Informe Técnico Final firmado para entrega al Cliente / Tribunal."
            ])
            
            st.session_state.auto_actividades = "\n".join(act_list)
            st.success("¡Actividades y Etapas generadas exitosamente!")

    st.markdown("---")
    # Output generado automáticamente (editable por el usuario)
    actividades = st.text_area(
        "6. Actividades / Etapas Propuestas (Output Generado):", 
        value=st.session_state.auto_actividades, 
        placeholder="Aquí se desplegarán automáticamente las Actividades estructuradas por Etapas...", 
        height=180
    )

# ---------------------------------------------------------
# PESTAÑA 3: HORAS HOMBRE Y PERFILES (5 Profesionales)
# ---------------------------------------------------------
with tab3:
    st.subheader("Estimación de Recursos (5 Profesionales de Asesoría) y Tarifas Editables")
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
    with c2: hh_an1 = st.number_input("HH Profesional 1", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_an1 = st.number_input("Tarifa Prof. 1", min_value=0.0, value=1.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Profesional de Asesoría 2")
    with c2: hh_an2 = st.number_input("HH Profesional 2", min_value=0, value=0, label_visibility="collapsed")
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
    st.info(f"**Total Horas Hombre:** {tot_hh:.0f} HH  |  **Monto Total Calculado:** {tot_uf:.1f} UF")

# ---------------------------------------------------------
# PESTAÑA 4: OFERTA ECONÓMICA Y DESCARGA (5 Hitos Título + %)
# ---------------------------------------------------------
with tab4:
    st.subheader("Condiciones Comerciales y Estructura de Pagos (5 Hitos Personalizables)")
    
    st.markdown("#### Configuración de Hitos de Pago (Título y Porcentaje)")
    
    col_t1, col_p1 = st.columns([3, 1])
    with col_t1: titulo_h1 = st.text_input("Título Hito 1:", value="Anticipo / Orden de Compra")
    with col_p1: pct_h1 = st.number_input("% Hito 1:", min_value=0, max_value=100, value=30 if "Parte" in tipo_encargo else 50)

    col_t2, col_p2 = st.columns([3, 1])
    with col_t2: titulo_h2 = st.text_input("Título Hito 2:", value="Entrega del Informe de Pertinencia")
    with col_p2: pct_h2 = st.number_input("% Hito 2:", min_value=0, max_value=100, value=30 if "Parte" in tipo_encargo else 0)

    col_t3, col_p3 = st.columns([3, 1])
    with col_t3: titulo_h3 = st.text_input("Título Hito 3:", value="Entrega del Informe Borrador")
    with col_p3: pct_h3 = st.number_input("% Hito 3:", min_value=0, max_value=100, value=30 if "Parte" in tipo_encargo else 0)

    col_t4, col_p4 = st.columns([3, 1])
    with col_t4: titulo_h4 = st.text_input("Título Hito 4:", value="Entrega del Informe Final / Firmado")
    with col_p4: pct_h4 = st.number_input("% Hito 4:", min_value=0, max_value=100, value=10 if "Parte" in tipo_encargo else 50)

    col_t5, col_p5 = st.columns([3, 1])
    with col_t5: titulo_h5 = st.text_input("Título Hito 5 (Opcional):", value="Aprobación Final / Cierre")
    with col_p5: pct_h5 = st.number_input("% Hito 5:", min_value=0, max_value=100, value=0)

    tot_pct = pct_h1 + pct_h2 + pct_h3 + pct_h4 + pct_h5
    if tot_pct != 100:
        st.warning(f"Atención: Los porcentajes ingresados suman {tot_pct}%. Deben completar exactamente el 100%.")
    else:
        st.success("Estructura de pagos válida (Suma 100%).")

    hitos_list = []
    if pct_h1 > 0: hitos_list.append(f"{pct_h1}% contra {titulo_h1}")
    if pct_h2 > 0: hitos_list.append(f"{pct_h2}% contra {titulo_h2}")
    if pct_h3 > 0: hitos_list.append(f"{pct_h3}% contra {titulo_h3}")
    if pct_h4 > 0: hitos_list.append(f"{pct_h4}% contra {titulo_h4}")
    if pct_h5 > 0: hitos_list.append(f"{pct_h5}% contra {titulo_h5}")
    forma_pago_texto = " / ".join(hitos_list)

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
