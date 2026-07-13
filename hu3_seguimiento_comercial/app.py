import streamlit as st
import pandas as pd
import sys
import os
import asyncio
import logging

# --- PARCHE DEFINITIVO PARA WINDOWS ---
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)
# --------------------------------------

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.database import obtener_todos_los_leads, actualizar_lead
from hu3_seguimiento_comercial.agent_dashboard import generar_sugerencia_comercial
from shared.ui_styles import aplicar_estilos_globales

#st.set_page_config(page_title="CRM Ejecutivo", layout="centered")

# Inyectar el diseño unificado
aplicar_estilos_globales()

with st.sidebar:
    st.markdown("### 📌 Accesos Rápidos")
    st.markdown("- [📊 Resumen Operativo](#resumen-operativo)")
    st.markdown("- [📋 Área de Gestión](#area-de-gestion)")
    st.markdown("---")

st.markdown('<div class="topbar-marca">Atlas Financial AI</div>', unsafe_allow_html=True)
st.title("💼 Panel de Control Comercial")

st.markdown("Gestión de Leads y Acciones Sugeridas por IA")
st.markdown("---")

leads = obtener_todos_los_leads()

if not leads:
    st.info("No hay leads registrados en el CRM en este momento.")
else:
    # ==========================================
    # 1. PUERTA DE ENTRADA: RESUMEN OPERATIVO
    # ==========================================
    st.subheader("📊 Resumen Operativo", anchor="resumen-operativo")
    
    total_leads = len(leads)
    total_pendientes = len([l for l in leads if l.estado_accion == "Pendiente"])
    total_aprobados = len([l for l in leads if l.estado_accion == "Aprobado"])
    total_rechazados = len([l for l in leads if l.estado_accion == "Rechazado"])
    total_gestionados = total_aprobados + total_rechazados
    
    # Fila de métricas destacadas
    col_met_1, col_met_2, col_met_3 = st.columns(3)
    col_met_1.metric("Total de Leads", total_leads)
    col_met_2.metric("Pendientes por Gestionar", total_pendientes)
    col_met_3.metric("Leads Gestionados", total_gestionados)
    
    # Fila de gráficos estructurados y minimalistas
    col_graf_1, col_graf_2 = st.columns(2)
    with col_graf_1:
        df_flujo = pd.DataFrame({
            "Estado": ["Pendientes", "Gestionados"],
            "Cantidad": [total_pendientes, total_gestionados]
        }).set_index("Estado")
        st.bar_chart(df_flujo, color="#3498db") # Azul plano
        
    with col_graf_2:
        df_conversion = pd.DataFrame({
            "Decisión": ["Aprobados", "Rechazados"],
            "Cantidad": [total_aprobados, total_rechazados]
        }).set_index("Decisión")
        st.bar_chart(df_conversion, color="#2ecc71") # Verde plano

    st.markdown("---")
# ==========================================
    # 2. ÁREA DE TRABAJO: GESTIÓN DE LEADS
    # ==========================================
    st.subheader("📋 Área de Gestión", anchor="area-de-gestion")
    
    # --- NUEVOS FILTROS COMERCIALES GLOBALES ---
    st.markdown("Filtros de visualización:")
    col_busqueda, col_filtro, col_orden = st.columns([2, 1, 1])
    
    with col_busqueda:
        busqueda_nombre = st.text_input(
            "🔍 Buscar por nombre o empresa:", 
            placeholder="Ej. Constructora Andina..."
        )
    with col_filtro:
        filtro_prioridad = st.selectbox(
            "Prioridad del Lead:",
            options=["Todas", "Alta", "Media", "Baja"],
            index=0
        )
    with col_orden:
        orden_mostrar = st.selectbox(
            "Orden de llegada:",
            options=["Más recientes primero", "Más antiguos primero"],
            index=0
        )
        
    # 1. Aplicar ordenamiento a la lista global
    leads_ordenados = list(reversed(leads)) if orden_mostrar == "Más recientes primero" else leads
    
    # 2. Aplicar búsqueda por nombre (Case-insensitive)
    if busqueda_nombre:
        leads_ordenados = [l for l in leads_ordenados if busqueda_nombre.lower() in l.nombre.lower()]

    tab_pendientes, tab_gestionados = st.tabs(["⏳ Pendientes", "🗃️ Historial"])
    
    with tab_pendientes:
        # Filtrar por estado Pendiente y prioridad
        pendientes = [l for l in leads_ordenados if l.estado_accion == "Pendiente"]
        if filtro_prioridad != "Todas":
            pendientes = [l for l in pendientes if l.prioridad == filtro_prioridad]
            
        if not pendientes:
            st.success("✅ ¡Todo al día! No hay acciones pendientes con estos filtros.")
            
        for lead in pendientes:
            with st.expander(f"👤 {lead.nombre} (Prioridad: {lead.prioridad})", expanded=True):
                st.write(f"**Email:** {lead.email} | **Tipo:** {lead.tipo_cliente}")
                st.write(f"**Resumen IA:** {lead.resumen_conversacion_comercial}")
                st.write(f"**Tema Academia:** {lead.tema_aprendizaje} (Quiz: {lead.score_quiz}/3)")
                st.markdown("---")
                
                # Integración con Gemini y protección anti-errores
                if not lead.accion_propuesta or lead.accion_propuesta == "Requiere revisión manual" or "✨" in lead.accion_propuesta:
                    with st.spinner("🤖 Gemini está analizando este lead..."):
                        sugerencia_ia = generar_sugerencia_comercial(
                            lead.resumen_conversacion_comercial, 
                            lead.tipo_cliente, 
                            lead.presupuesto
                        )
                        lead.accion_propuesta = sugerencia_ia
                        actualizar_lead(lead)
                
                st.caption("✨ Sugerencia generada por Google Gemini")
                accion_editable = st.text_input("Acción propuesta a ejecutar (Editable):", value=lead.accion_propuesta, key=f"txt_{lead.id}")
                
                col_btn_1, col_btn_2 = st.columns(2)
                with col_btn_1:
                    if st.button("👍 Aprobar / Guardar", key=f"app_{lead.id}", use_container_width=True):
                        lead.accion_propuesta = accion_editable
                        lead.estado_accion = "Aprobado"
                        actualizar_lead(lead)
                        st.rerun()
                with col_btn_2:
                    if st.button("❌ Rechazar", key=f"rej_{lead.id}", use_container_width=True):
                        lead.estado_accion = "Rechazado"
                        actualizar_lead(lead)
                        st.rerun()

    with tab_gestionados:
        # --- Filtro exclusivo para Historial ---
        filtro_estado = st.radio(
            "Filtrar por estado de resolución:",
            options=["Todos", "Aprobado", "Rechazado"],
            horizontal=True
        )
        st.markdown("---")
        
        # Filtrar por estado gestionado, prioridad y el nuevo radio button
        gestionados = [l for l in leads_ordenados if l.estado_accion != "Pendiente"]
        if filtro_prioridad != "Todas":
            gestionados = [l for l in gestionados if l.prioridad == filtro_prioridad]
        if filtro_estado != "Todos":
            gestionados = [l for l in gestionados if l.estado_accion == filtro_estado]
            
        if not gestionados:
            st.write("Aún no has gestionado ningún lead que coincida con estos filtros.")
            
        for lead in gestionados:
            icono = "✅" if lead.estado_accion == "Aprobado" else "⛔"
            with st.expander(f"{icono} {lead.nombre} - Estado: {lead.estado_accion}"):
                st.write(f"**Acción final guardada:** {lead.accion_propuesta}")
                
                if st.button("🔄 Deshacer y devolver a Pendientes", key=f"undo_{lead.id}"):
                    lead.estado_accion = "Pendiente"
                    actualizar_lead(lead)
                    st.rerun()