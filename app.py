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
    tipo_encargo = st.radio("Tipo de Servicio:", ["Informe Técnico de Parte (Cliente Directo)", "Peritaje Judicial / Arbitral CAM"])
    
    col1, col2 = st.columns(2)
    with col1:
        codigo = st.text_input("Código de Propuesta:", value="", placeholder="Ingrese código PR.DIC...")
        cliente = st.text_input("Cliente / Razón Social:", value="", placeholder="Ingrese razón social del cliente...")
        solicitante = st.text_input("Nombre Solicitante:", value="", placeholder="Nombre del solicitante...")
        cargo_solicitante = st.text_input("Cargo Solicitante:", value="", placeholder="Cargo del solicitante...")
        fecha_emision = st.date_input("Fecha de Emisión:", value=datetime.date.today(), format="DD/MM/YYYY")
    with col2:
        revision = st.text_input("Revisión N°:", value="0")
        rut_cliente = st.text_input("RUT Cliente:", value="", placeholder="RUT cliente...")
        email_solicitante = st.text_input("Email Solicitante:", value="", placeholder="correo@ejemplo.cl")
        telefono_solicitante = st.text_input("Teléfono Solicitante:", value="", placeholder="+56 9 ...")
        rol_cam = st.text_input("Tribunal / Rol Arbitral (Solo CAM):", value="", placeholder="Rol CAM N°...")
    
    nombre_propuesta = st.text_input("Nombre Oficial de la Propuesta:", value="", placeholder="Ej: INFORME TÉCNICO DE CUANTIFICACIÓN DE MAYORES COSTOS...")

# ---------------------------------------------------------
# PESTAÑA 2: ALCANCE Y CONTEXTO
# ---------------------------------------------------------
with tab2:
    st.subheader("Descripción del Conflicto y Propuesta Técnica")
    
    if "auto_actividades" not in st.session_state:
        st.session_state.auto_actividades = ""

    sintesis_alcance = st.text_area(
        "Resumen / Síntesis del Alcance (Para Cuadro Resumen Cap. 1):",
        value="",
        placeholder="Ingrese una síntesis breve del objetivo y alcance del estudio para la tabla del Resumen Ejecutivo...",
        height=90
    )

    intro = st.text_area(
        "4. Introducción / Contexto de la Obra (Input Usuario):", 
        value="", 
        placeholder="Ingrese el contexto detallado de la obra, contrato y controversia...", 
        height=140
    )
    
    alcance = st.text_area(
        "5. Alcance Detallado (Conceptos a evaluar / Puntos de Prueba - Input Usuario):", 
        value="", 
        placeholder="Ingrese el desglose detallado de los puntos de prueba y alcance...", 
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
# PESTAÑA 3: HORAS HOMBRE Y PERFILES (5 Profesionales)
# ---------------------------------------------------------
with tab3:
    st.subheader("Estimación de Recursos y Perfiles Profesionales")
    meses_val = st.number_input("Plazo Total del Estudio (Meses):", min_value=0.5, step=0.5, value=1.0)
    
    col_hdr1, col_hdr2, col_hdr3 = st.columns([2, 1, 1])
    with col_hdr1: st.markdown("**Categoría Profesional**")
    with col_hdr2: st.markdown("**HH / Mes**")
    with col_hdr3: st.markdown("**Tarifa (UF/HH)**")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Asesor Técnico / Revisor")
    with c2: hh_asesor = st.number_input("HH Asesor", min_value=0, value=0, label_visibility="collapsed")
    with c3: tar_asesor = st.number_input("Tarifa Asesor", min_value=0.0, value=0.0, step=0.1, label_visibility="collapsed")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.write("Jefe de Proyecto / Asesoría")
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
    # GENERACIÓN CON PLANTILLA OFICIAL
    # ---------------------------------------------------------
    def generar_documento_word():
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base_dir, "Plantilla_Oficial_IDIEM.docx")
        
        doc = DocxTemplate(template_path)
        
        lista_excl = []
        if excl1.strip(): lista_excl.append(excl1.strip())
        if excl2.strip(): lista_excl.append(excl2.strip())
        if excl3.strip(): lista_excl.append(excl3.strip())
        if excl4.strip(): lista_excl.append(excl4.strip())

        resumen_alcance_final = sintesis_alcance.strip() if sintesis_alcance.strip() else (alcance[:250] + "..." if len(alcance) > 250 else alcance)
        str_duracion = f"{meses_val:.0f}" if meses_val.is_integer() else f"{meses_val}"

        monto_uf_palabras = numero_a_palabras_uf(tot_uf)

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
            'SINTESIS_ALCANCE': resumen_alcance_final,
            'PLAZO_MESES': str_duracion,
            'PLAZO_TEXTO': f"{str_duracion} meses",
            'NUM_PROFESIONALES_ASESORIA': f"{num_profesionales_activos} Profesionales de Asesoría",
            'MONTO_UF_TOTAL': f"{tot_uf:,.0f}".replace(",", "."),
            'MONTO_UF_PALABRAS': monto_uf_palabras,
            'CONDICION_PAGO': condicion_pago,
            'TEXTO_INTRODUCCION': intro,
            'TEXTO_ALCANCE_DETALLADO': alcance,
            'TEXTO_ACTIVIDADES_ETAPAS': actividades,
            'LISTA_EXCLUSIONES': lista_excl,
            'NOTA_IMPUESTOS_IVA': regimen_iva,
            
            # Variables de Horas Hombre y UF por fila fija (Asesor, Jefe y 5 Profesionales)
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
            
            # Datos de Hitos para Tabla 13.2
            'PCT_H1': pct_h1, 'TIT_H1': titulo_h1, 'UF_H1': f"{int(tot_uf * (pct_h1/100)):,.0f}".replace(",", "."),
            'PCT_H2': pct_h2, 'TIT_H2': titulo_h2, 'UF_H2': f"{int(tot_uf * (pct_h2/100)):,.0f}".replace(",", "."),
            'PCT_H3': pct_h3, 'TIT_H3': titulo_h3, 'UF_H3': f"{int(tot_uf * (pct_h3/100)):,.0f}".replace(",", "."),
            'PCT_H4': pct_h4, 'TIT_H4': titulo_h4, 'UF_H4': f"{int(tot_uf * (pct_h4/100)):,.0f}".replace(",", "."),
            'PCT_H5': pct_h5, 'TIT_H5': titulo_h5, 'UF_H5': f"{int(tot_uf * (pct_h5/100)):,.0f}".replace(",", "."),
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
