import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from docs.upsert_doc import upload_pdf
from docs.maint_manual import upload_manual
from docs.delete_doc import delete_pdf

load_dotenv()

api_endpoint = os.environ.get("API_ENDPOINT", "default_endpoint")
usuario = os.environ.get("USUARIO", "default_usuario")
password_env = os.environ.get("PASSWORD", "default_password")
bucket_name = "maintenance-documentation-rag"

def main():
    st.set_page_config(page_title="AssetBot", layout='wide')
    apply_custom_css()

    # Verificación de inicio de sesión
    if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
        login_page()
    else:
        app_navigation()

def apply_custom_css():
    st.markdown("""
        <style>
            /* Cambiar el color de fondo de la página */
            .stApp {
                background-color: #e6f0ff;
            }

            /* Estilos para el botón de inicio de sesión */
            .css-18e3th9 {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                margin: 10px 0;
            }

            .css-18e3th9:hover {
                background-color: #3866a6;
            }

            /* Personalizar el título y los subtítulos */
            h1 {
                color: #333366;
            }

            h2, h3, h4, h5, h6 {
                color: #555599;
            }
        </style>
    """, unsafe_allow_html=True)

def login_page():
    st.sidebar.image("logo.jpg", use_column_width=True)
    st.sidebar.write("## Inicio de sesión")

    username = st.sidebar.text_input("Usuario")
    password_input = st.sidebar.text_input("Contraseña", type="password")

    if st.sidebar.button("Iniciar sesión"):
        if username == usuario and password_input == password_env:
            st.session_state['authenticated'] = True
            st.experimental_rerun()
        else:
            st.sidebar.error("Usuario o contraseña incorrectos.")

def app_navigation():
    st.sidebar.image("logo.jpg", use_column_width=True)
    st.sidebar.write("## Navegación")
    page = st.sidebar.radio("Ir a:", ['Chat', 'Cargar documento', 'Consultar Manual', 'Eliminar documento'], index=0)

    if page == 'Chat':
        chat_page()
    elif page == 'Cargar documento':
        upload_pdf()
    elif page == 'Consultar Manual':
        upload_manual()
    elif page == 'Eliminar documento':
        delete_pdf()

def chat_page():
    #st.title("AssetBot: Chatbot para mantenimiento y gestión de activos")
    st.markdown("<h1>AssetBot</h1>", unsafe_allow_html=True)
    st.markdown("<h2>Chatbot para mantenimiento y gestión de activos<h2>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        user_question = st.text_input("Haz una pregunta sobre mantenimiento y gestión de activos:", "")
    with col2:
        ask_button = st.button("Obtener respuesta")

    if ask_button and user_question:
        chat_container = st.container()
        with chat_container:
            st.markdown(f"**Tú:** {user_question}")
        with st.spinner("Generando la respuesta..."):
            response = get_response(user_question, True)
            if response:
                with chat_container:
                    st.markdown(response)
            else:
                st.error("Por favor intenta de nuevo.")
    elif ask_button:
        st.warning("Por favor, ingresa una pregunta.")

def get_response(question, verbose):
    endpoint = api_endpoint
    headers = {"Content-Type": "application/json"}
    data = {"question": question, "verbose": verbose}

    try:
        response = requests.post(endpoint, headers=headers, json=data)
        if response.status_code == 200:
            response_json = response.json()
            answer_text = response_json.get('answer', '').replace('\n', '  \n')
            answer_text = answer_text.encode('utf-8').decode('unicode_escape')
            formatted_response = f"**AssetBot:**\n\n{answer_text}\n"
            return formatted_response
        else:
            st.error(f"Falla en generar la respuesta: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Una excepción ha ocurrido: {e}")
        return None

if __name__ == "__main__":
    main()