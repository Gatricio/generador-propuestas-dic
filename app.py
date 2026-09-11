if st.button("🤖 Redactar Introducción y Actividades a partir del Alcance"):
        if not alcance.strip():
            st.warning("Por favor escriba al menos un concepto en el campo '5. Alcance Detallado' antes de generar.")
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
                        (Redacta un párrafo continuo formal para la Sección 4 'Introducción' introduciendo el proyecto, la solicitud de estudio y el contexto contractual de las discrepancias basadas en los conceptos a evaluar).
                        
                        SECCION_ACTIVIDADES:
                        (Propón el desglose ordenado por etapas para la Sección 6 'Actividades', agrupando los conceptos en Etapa A: Análisis de Pertinencia y Línea Base, Etapa B: Evaluación de Plazo o Costos según corresponda, y Etapa C/D: Elaboración de Informe Técnico Final).
                        """
                        
                        # Intento con fallback automático de modelos
                        modelos_probar = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash', 'gemini-pro']
                        response = None
                        
                        for mod_name in modelos_probar:
                            try:
                                model = genai.GenerativeModel(mod_name)
                                response = model.generate_content(prompt_conceptos)
                                break
                            except Exception:
                                continue

                        if response is None or not response.text:
                            st.error("No se pudo conectar con los modelos de Gemini. Verifica la API Key en Secrets.")
                        else:
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
