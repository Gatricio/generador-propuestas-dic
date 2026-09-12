import datetime
from io import BytesIO
import streamlit as st
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

# Configuración inicial de Streamlit
st.set_page_config(
    page_title="IDIEM - Generador de Propuestas",
    page_icon="📄",
    layout="wide"
)

# Estilos corporativos en pantalla
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
# PESTAÑA 3: HORAS HOMBRE Y PERFILES
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
    excl1 = st.text_input("Exclusión 1:", value="Visitas a terreno.")
    excl2 = st.text_input("Exclusión 2:", value="Analizar otras situaciones no indicadas en el alcance de la presente propuesta.")
    excl3 = st.text_input("Exclusión 3:", value="Cualquier otra situación no indicada en el alcance, será considerada como adicional y se entregará el plazo y costo de incluirla dentro de este.")
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
    # CONSTRUCTOR NATIVO PYTHON-DOCX (GENERACIÓN DE WORD IMPECABLE)
    # ---------------------------------------------------------
    def set_cell_background(cell, fill_hex):
        tcPr = cell._element.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)

    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        tcPr = cell._element.get_or_add_tcPr()
        tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
        tcPr.append(tcMar)

    def generar_documento_word_nativo():
        doc = Document()

        # Estilos generales del documento
        normal_style = doc.styles['Normal']
        normal_style.font.name = 'Calibri'
        normal_style.font.size = Pt(11)
        normal_style.font.color.rgb = RGBColor(51, 51, 51)

        # 1. RESUMEN
        h1 = doc.add_heading('1   RESUMEN', level=1)
        p = doc.add_paragraph('A continuación, se presenta un cuadro resumen de la presente propuesta técnica y económica:')

        # Tabla 1: Información del Cliente
        p_t1 = doc.add_paragraph()
        r1 = p_t1.add_run('INFORMACIÓN DEL CLIENTE')
        r1.bold = True
        r1.font.color.rgb = RGBColor(0, 40, 85)

        t_client = doc.add_table(rows=5, cols=2)
        t_client.alignment = WD_TABLE_ALIGNMENT.CENTER
        client_data = [
            ("Cliente:", cliente if cliente else "N/A"),
            ("Rut:", rut_cliente if rut_cliente else "N/A"),
            ("Solicitante:", solicitante if solicitante else "N/A"),
            ("Cargo:", cargo_solicitante if cargo_solicitante else "N/A"),
            ("Correo electrónico:", email_solicitante if email_solicitante else "N/A")
        ]
        for idx, (label, val) in enumerate(client_data):
            row = t_client.rows[idx]
            row.cells[0].text = label
            row.cells[1].text = val
            row.cells[0].paragraphs[0].runs[0].bold = True
            set_cell_background(row.cells[0], "F0F4F8")
            set_cell_margins(row.cells[0])
            set_cell_margins(row.cells[1])

        doc.add_paragraph()

        # Tabla 2: Resumen Propuesta Técnica y Económica
        p_t2 = doc.add_paragraph()
        r2 = p_t2.add_run('RESUMEN DE LA PROPUESTA TÉCNICA Y ECONÓMICA')
        r2.bold = True
        r2.font.color.rgb = RGBColor(0, 40, 85)

        t_prop = doc.add_table(rows=7, cols=2)
        t_prop.alignment = WD_TABLE_ALIGNMENT.CENTER
        prop_data = [
            ("Nombre de la propuesta:", nombre_propuesta),
            ("Alcance:", alcance[:200] + "..." if len(alcance) > 200 else alcance),
            ("Ítems de la propuesta:", "Etapa A: Análisis de pertinencia.\nEtapa B: Estimación Gastos Generales.\nEtapa C: Cuantificación mayores costos.\nEtapa D: Informe final."),
            ("Plazo total:", f"{meses_val:.0f} meses" if meses_val.is_integer() else f"{meses_val} meses"),
            ("Oferta económica (valor):", f"UF {tot_uf:,.0f}.-".replace(",", ".")),
            ("Forma de pago:", f"{pct_h1}% {titulo_h1}\n{pct_h2}% {titulo_h2}\n{pct_h3}% {titulo_h3}\n{pct_h4}% {titulo_h4}\n{pct_h5}% {titulo_h5}"),
            ("Condición de pago:", condicion_pago)
        ]
        for idx, (label, val) in enumerate(prop_data):
            row = t_prop.rows[idx]
            row.cells[0].text = label
            row.cells[1].text = val
            row.cells[0].paragraphs[0].runs[0].bold = True
            set_cell_background(row.cells[0], "F0F4F8")
            set_cell_margins(row.cells[0])
            set_cell_margins(row.cells[1])

        doc.add_page_break()

        # 2. PRESENTACIÓN DEL CONSULTOR - IDIEM
        doc.add_heading('2   PRESENTACIÓN DEL CONSULTOR - IDIEM', level=1)
        doc.add_paragraph("IDIEM es el Centro de Investigación, Desarrollo e Innovación de Estructuras y Materiales, dependiente de la Facultad de Ingeniería de la Universidad de Chile, fundado en 1898.")
        doc.add_paragraph("Nuestro centro es una institución con reconocida trayectoria y experiencia en la solución de problemas de la construcción. Los servicios que IDIEM ofrece son una respuesta a las necesidades que la industria requiere, aportando al desarrollo de la infraestructura pública y privada del país.")

        # 3. ASESORÍA CONTRACTUAL EN CONTROVERSIAS Y CLAIMS
        doc.add_heading('3   ASESORÍA CONTRACTUAL EN CONTROVERSIAS Y CLAIMS', level=1)
        doc.add_paragraph("Elaboramos estudios técnicos durante todo el desarrollo del contrato, desde la etapa de licitación, ejecución de la obra, hasta análisis forenses de contratos en caso de reclamaciones posteriores al término de la obra.")

        # 4. INTRODUCCIÓN
        doc.add_heading('4   INTRODUCCIÓN', level=1)
        doc.add_paragraph(intro if intro else "Sin información de introducción ingresada.")

        # 5. ALCANCE
        doc.add_heading('5   ALCANCE', level=1)
        doc.add_paragraph(alcance if alcance else "Sin información de alcance ingresada.")

        # 6. ACTIVIDADES
        doc.add_heading('6   ACTIVIDADES', level=1)
        doc.add_paragraph(actividades if actividades else "Sin actividades generadas.")

        # 7. ANTECEDENTES
        doc.add_heading('7   ANTECEDENTES', level=1)
        doc.add_paragraph("Se requiere contar con la información necesaria para respaldar las situaciones reclamadas, señalados a modo general en los puntos anteriores.")

        # 8. ORGANIGRAMA PROPUESTO
        doc.add_heading('8   ORGANIGRAMA PROPUESTO', level=1)
        doc.add_paragraph("Para el presente proyecto se considera el siguiente equipo de profesionales:")
        doc.add_paragraph("• 1 Profesional Asesor Técnico (Ingeniero Civil o Constructor Civil con más de 15 años de experiencia).")
        doc.add_paragraph("• 1 Jefe de Proyecto (Ingeniero Civil o Constructor Civil con más de 10 años de experiencia).")
        doc.add_paragraph(f"• {num_profesionales_activos} Profesionales de Asesoría (Ingeniero Civil o Constructor Civil dedicados al análisis documental y cálculos).")

        # 9. METODOLOGÍA
        doc.add_heading('9   METODOLOGÍA', level=1)
        doc.add_paragraph("La metodología contempla: Reunión de inicio, Recopilación de antecedentes, Análisis documental, Solicitud de antecedentes adicionales, Reuniones de coordinación, Análisis pericial y Presentación del Informe Final.")

        # 10. PLAZOS DEL SERVICIO
        doc.add_heading('10   PLAZOS DEL SERVICIO', level=1)
        doc.add_paragraph(f"El plazo de ejecución para la entrega del informe preliminar será de {meses_val:.0f} meses, contados a partir de la aceptación de la presente propuesta y de la entrega de antecedentes." if meses_val.is_integer() else f"El plazo de ejecución será de {meses_val} meses.")

        # 11. EXCLUSIONES
        doc.add_heading('11   EXCLUSIONES', level=1)
        doc.add_paragraph("No forma parte del alcance del presente estudio:")
        if excl1.strip(): doc.add_paragraph(f"• {excl1.strip()}")
        if excl2.strip(): doc.add_paragraph(f"• {excl2.strip()}")
        if excl3.strip(): doc.add_paragraph(f"• {excl3.strip()}")
        if excl4.strip(): doc.add_paragraph(f"• {excl4.strip()}")

        # 12. ENTREGABLES
        doc.add_heading('12   ENTREGABLES', level=1)
        doc.add_paragraph("Como resultado del estudio se entregará un informe digital conformado por un documento principal y un anexo digital respaldado.")

        # 13. OFERTA ECONÓMICA
        doc.add_heading('13   OFERTA ECONÓMICA', level=1)
        doc.add_heading('13.1   Precio del servicio', level=2)
        doc.add_paragraph(f"El valor del servicio propuesto corresponde a una suma alzada por un valor de UF: {tot_uf:,.0f}.- (Unidades de Fomento), de acuerdo con el siguiente desglose por categoría profesional:".replace(",", "."))

        # Tabla HH 13.1
        t_hh = doc.add_table(rows=1, cols=6)
        t_hh.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr_cells = t_hh.rows[0].cells
        hdr_titles = ["Profesional", "Cantidad [HH/mes]", "Duración [Meses]", "Total [HH]", "Precio unitario [UF/HH]", "Total [UF]"]
        for i, title in enumerate(hdr_titles):
            hdr_cells[i].text = title
            hdr_cells[i].paragraphs[0].runs[0].bold = True
            set_cell_background(hdr_cells[i], "002855")
            hdr_cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

        hh_rows_data = [
            ("Asesor Técnico", hh_asesor, meses_val, int(hh_asesor * meses_val), f"{tar_asesor:.1f}", int(hh_asesor * tar_asesor * meses_val)),
            ("Jefe Asesoría", hh_jefe, meses_val, int(hh_jefe * meses_val), f"{tar_jefe:.1f}", int(hh_jefe * tar_jefe * meses_val)),
            ("Profesional de asesoría 1", hh_an1, meses_val, int(hh_an1 * meses_val), f"{tar_an1:.1f}", int(hh_an1 * tar_an1 * meses_val)),
            ("Profesional de asesoría 2", hh_an2, meses_val, int(hh_an2 * meses_val), f"{tar_an2:.1f}", int(hh_an2 * tar_an2 * meses_val)),
        ]
        for p_name, hh_m, m_v, tot_h, tar_u, tot_u in hh_rows_data:
            if hh_m > 0:
                row_cells = t_hh.add_row().cells
                row_cells[0].text = p_name
                row_cells[1].text = str(hh_m)
                row_cells[2].text = str(m_v)
                row_cells[3].text = str(tot_h)
                row_cells[4].text = str(tar_u)
                row_cells[5].text = str(tot_u)

        # Fila Total
        tot_cells = t_hh.add_row().cells
        tot_cells[0].text = "TOTAL"
        tot_cells[0].paragraphs[0].runs[0].bold = True
        tot_cells[3].text = str(int(tot_hh))
        tot_cells[3].paragraphs[0].runs[0].bold = True
        tot_cells[5].text = f"{tot_uf:,.0f}".replace(",", ".")
        tot_cells[5].paragraphs[0].runs[0].bold = True

        doc.add_paragraph()
        doc.add_paragraph(regimen_iva)

        doc.add_heading('13.2   Términos financieros', level=2)
        doc.add_paragraph("El servicio se facturará de acuerdo con el siguiente recuadro:")

        # Tabla Hitos 13.2
        t_hitos = doc.add_table(rows=3, cols=6)
        t_hitos.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # Header Hitos
        t_hitos.rows[0].cells[0].text = "Total"
        t_hitos.rows[0].cells[1].text = titulo_h1
        t_hitos.rows[0].cells[2].text = titulo_h2
        t_hitos.rows[0].cells[3].text = titulo_h3
        t_hitos.rows[0].cells[4].text = titulo_h4
        t_hitos.rows[0].cells[5].text = titulo_h5
        for cell in t_hitos.rows[0].cells:
            cell.paragraphs[0].runs[0].bold = True
            set_cell_background(cell, "002855")
            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

        # Fila Porcentajes
        t_hitos.rows[1].cells[0].text = "%"
        t_hitos.rows[1].cells[1].text = f"{pct_h1}%"
        t_hitos.rows[1].cells[2].text = f"{pct_h2}%"
        t_hitos.rows[1].cells[3].text = f"{pct_h3}%"
        t_hitos.rows[1].cells[4].text = f"{pct_h4}%"
        t_hitos.rows[1].cells[5].text = f"{pct_h5}%"

        # Fila Montos UF
        t_hitos.rows[2].cells[0].text = "Monto (UF)"
        t_hitos.rows[2].cells[1].text = str(int(tot_uf * (pct_h1/100)))
        t_hitos.rows[2].cells[2].text = str(int(tot_uf * (pct_h2/100)))
        t_hitos.rows[2].cells[3].text = str(int(tot_uf * (pct_h3/100)))
        t_hitos.rows[2].cells[4].text = str(int(tot_uf * (pct_h4/100)))
        t_hitos.rows[2].cells[5].text = str(int(tot_uf * (pct_h5/100)))

        # 14 a 19 Capítulos Estándar
        doc.add_heading('14   CONSIDERACIONES PARA LA EJECUCIÓN DE LOS TRABAJOS', level=1)
        doc.add_paragraph("Los trabajos se realizarán en dependencias de IDIEM en días hábiles, en horario institucional.")

        doc.add_heading('15   ENTREGA DE INFORMACIÓN', level=1)
        doc.add_paragraph("La documentación proporcionada por el Cliente es fundamental. Se solicita entrega digital en carpetas ordenadas.")

        doc.add_heading('16   COMUNICACIÓN ENTRE LAS PARTES', level=1)
        doc.add_paragraph("Se solicita un único canal de comunicación. Por parte de IDIEM el canal será el Jefe del Proyecto.")

        doc.add_heading('17   TÉRMINO ANTICIPADO', level=1)
        doc.add_paragraph("Cualquiera de las partes tendrá derecho a pedir la terminación anticipada según la legislación chilena aplicable.")

        doc.add_heading('18   DISPOSICIONES ADMINISTRATIVAS', level=1)
        doc.add_paragraph("Para transferencias en cuenta corriente Banco de Chile N° 170-006 44-01 a nombre de Universidad de Chile.")

        doc.add_heading('19   DISPOSICIONES GENERALES', level=1)
        doc.add_paragraph("El precio pactado constituye una suma fija. IDIEM aportará una visión imparcial y técnica en todo momento.")

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    st.download_button(
        label="📥 Descargar Propuesta Emitida Formato Oficial (.docx)",
        data=generar_documento_word_nativo(),
        file_name=f"Propuesta_IDIEM_{codigo if codigo else 'PR.DIC'}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
