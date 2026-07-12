import streamlit as st

# Configuración global de la ventana
st.set_page_config(page_title="ATLAS Financial AI", page_icon="🏛️", layout="centered")

# Configuración de navegación del ecosistema completo Track 1
pg = st.navigation([
    st.Page(
        "hu1_calificacion_leads/streamlit_app.py", 
        title="ATLAS: Captación y Calificación", 
        icon="🤖", 
        url_path="captacion"
    ),
    st.Page(
        "hu2_tutor_financiero/streamlit_app.py", 
        title="ATLAS: Tutor Financiero", 
        icon="🎓", 
        url_path="tutor"
    ),
    st.Page(
        "hu3_seguimiento_comercial/app.py", 
        title="ATLAS: Panel de Control Comercial", 
        icon="💼", 
        url_path="dashboard"
    )
])

st.sidebar.markdown("### 🏛️ ATLAS Financial AI")
st.sidebar.markdown("---")
pg.run()