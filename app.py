import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import matplotlib.pyplot as plt # Importamos matplotlib

# 1. Configuración de la App
st.set_page_config(page_title="TalentScout AI", page_icon="👔", layout="wide")

# 2. Configuración de Gemini
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    st.success("✅ La API Key fue detectada y configurada.")
else:
    st.error("❌ ERROR: No se encontró la variable GOOGLE_API_KEY en los Secrets de Streamlit.")
    st.stop() # Detiene la ejecución si no hay llave
# 3. Definir Personalidad
info_empresa = """
INFORMACIÓN PARA CANDIDATOS:
- Nuestra empresa se llama 'TechInnovate'.
- Vacante actual: Desarrollador Python. Sueldo: 30k-40k MXN. 
- Beneficios: Seguro médico, 100% remoto, fondo de ahorro.
- Proceso: 1. Entrevista técnica, 2. Entrevista con RH, 3. Oferta.
- Ubicación: Ciudad de México (aunque operamos remoto).
"""

instruccion_del_sistema = f"""
Eres "TalentScout AI". Tienes dos funciones:
1. INTERNO (Reclutador): Analizar CVs que te pasen.
2. EXTERNO (Candidato): Responder dudas sobre la empresa usando esta información:
{info_empresa}

Si un candidato pregunta algo que NO está en la información anterior, dile amablemente 
que consultarás con el equipo de RH y que deje su correo.
Tono: Muy amable, servicial y profesional.
"""

if "model" not in st.session_state:
    st.session_state.model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=instruccion_del_sistema
    )

if "chat" not in st.session_state:
    st.session_state.chat = st.session_state.model.start_chat(history=[])

# Función para crear la gráfica de barras
def crear_grafica_puntuacion(puntuacion):
    # Validar que la puntuación sea un número real
    try:
        puntuacion = float(puntuacion)
    except:
        puntuacion = 0
    fig, ax = plt.subplots(figsize=(8, 1.2))
    # Color dinámico: Rojo si es bajo, Verde si es alto
    color = 'green' if puntuacion >= 7 else 'orange' if puntuacion >= 5 else 'red'
    
    ax.barh(["Puntuación"], [puntuacion], color=color)
    ax.set_xlim(0, 10)
    ax.set_xticks(range(11))
    st.pyplot(fig)
# --- INTERFAZ LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("📁 Gestión de Candidatos")
    archivo = st.file_uploader("Sube el CV en PDF", type=["pdf"])
    
    if archivo:
        try:
            lector = PdfReader(archivo)
            texto_cv = "".join([pagina.extract_text() for pagina in lector.pages])
            st.success("✅ PDF procesado con éxito")
            
            if st.button("🔍 Analizar y Calificar"):
                # Modificamos el prompt para que la puntuación sea más fácil de extraer
                prompt_evaluacion = f"""
                Analiza el siguiente CV y genera una evaluación técnica detallada:
                ###PUNTUACION: (Número entero del 1 al 10)###
                - Puntos fuertes: 
                - Áreas de mejora:
                - Veredicto final:
                
                CV: {texto_cv}
                """
                with st.spinner("IA evaluando candidato..."):
                    respuesta_eval = st.session_state.chat.send_message(prompt_evaluacion)
                    st.session_state.ultima_evaluacion = respuesta_eval.text
                    # Guardamos el nombre del archivo para el reporte
                    st.session_state.nombre_candidato = archivo.name
                st.rerun()
        except Exception as e:
            st.error(f"Error al leer PDF: {e}")

# --- INTERFAZ DE CHAT PRINCIPAL ---
st.title("👔 TalentScout AI")
st.caption("Asistente inteligente para Reclutamiento y Selección")

# MOSTRAR EVALUACIÓN DESTACADA Y GRÁFICA
if "ultima_evaluacion" in st.session_state:
    with st.expander("📊 RESULTADO DE LA EVALUACIÓN", expanded=True):
        st.markdown(st.session_state.ultima_evaluacion)
        
        # Intentar extraer la puntuación para la gráfica
        try:
            inicio_puntuacion = st.session_state.ultima_evaluacion.find("###PUNTUACION:") + len("###PUNTUACION:")
            fin_puntuacion = st.session_state.ultima_evaluacion.find("###", inicio_puntuacion)
            puntuacion = int(st.session_state.ultima_evaluacion[inicio_puntuacion:fin_puntuacion].strip())
            
            # Crear y mostrar la gráfica
            st.subheader(f"Visualización de la Puntuación: {puntuacion}/10")
            crear_grafica_puntuacion(puntuacion)
        except Exception:
            st.warning("No se pudo extraer la puntuación numérica para la gráfica.")
        
        col1, col2 = st.columns(2)
        with col1:
            # BOTÓN PARA DESCARGAR EL REPORTE
            reporte_texto = f"REPORTE DE EVALUACIÓN - {st.session_state.nombre_candidato}\n"
            reporte_texto += "="*40 + "\n"
            reporte_texto += st.session_state.ultima_evaluacion
            
            st.download_button(
                label="📥 Descargar Evaluación (.txt)",
                data=reporte_texto,
                file_name=f"Evaluacion_{st.session_state.nombre_candidato}.txt",
                mime="text/plain"
            )
        with col2:
            if st.button("🗑️ Limpiar Evaluación"):
                del st.session_state.ultima_evaluacion
                st.rerun()

st.divider()

# Mostrar historial de chat (filtrado)
for mensaje in st.session_state.chat.history:
    role = "user" if mensaje.role == "user" else "assistant"
    contenido = mensaje.parts[0].text
    if "Analiza el siguiente CV" in contenido or "Analiza el CV detalladamente" in contenido:
        continue
    with st.chat_message(role):
        st.markdown(contenido)

# Entrada de usuario
if prompt := st.chat_input("Pregunta sobre la vacante o el proceso..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        respuesta = st.session_state.chat.send_message(prompt)
        st.markdown(respuesta.text)
