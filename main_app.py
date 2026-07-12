import streamlit as st

# Configuración global de la ventana
st.set_page_config(page_title="ATLAS Financial AI", page_icon="🏛️", layout="centered")

# Configuración de navegación del ecosistema completo Track 1
pg = st.navigation([
    # st.Page("hu1_calificacion_leads/app_calificacion.py", title="ATLAS: Captación y Calificación", icon="🤖"),
    # Aquí se acoplará el archivo de tu compañero cuando termine la HU2:
    st.Page("agente_ia_hu2/agent_tutor.py", title="ATLAS: Tutor Financiero", icon="🎓"),
     st.Page("hu3_seguimiento_comercial/app.py", title="ATLAS: Panel de Control Comercial", icon="💼")
])

st.sidebar.markdown("### 🏛️ ATLAS Financial AI")
st.sidebar.markdown("---")
pg.run()