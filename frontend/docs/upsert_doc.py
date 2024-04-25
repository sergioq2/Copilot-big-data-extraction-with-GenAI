import streamlit as st
import boto3
import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_endpoint = os.environ.get("API_ENDPOINT_UPSERT", "default_endpoint")
bucket_name = 'demo-extensive-documents'

def upload_pdf():
    s3_client = boto3.client('s3')
    st.title('Upload the document')
    st.markdown("Please upload the document you want to use for countermeasure extraction")

    uploaded_file = st.file_uploader("Choose a file", type="pdf", accept_multiple_files=True)

    if uploaded_file is not None:
        with st.spinner('Loading...'):
            object_name = uploaded_file.name
            file_name = object_name.rsplit('.', 1)[0]
            folder_name = f'{file_name}/{object_name}'
            s3_client.upload_fileobj(uploaded_file, bucket_name, folder_name)

        endpoint = api_endpoint
        headers = {"Content-Type": "application/json"}
        data = {"folder_name": file_name}

        save_button = st.button("Save file")

        if save_button:
            with st.spinner('Saving...'):
                response = requests.post(endpoint, headers=headers, json=data)
                if response.status_code == 200:
                    st.success("El archivo ha sido almacenado correctamente.")
                else:
                    st.error(f"Error al procesar el archivo: {response.text}")

        # Sección informativa sobre el proceso
        st.info("Una vez que el documento se guarda, se procesará para su indexación y fácil recuperación en futuras consultas.")

if __name__ == "__main__":
    upload_pdf()