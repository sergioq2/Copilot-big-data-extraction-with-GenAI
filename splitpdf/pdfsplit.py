import boto3
import os
import io
from PyPDF2 import PdfReader, PdfWriter
import json

s3 = boto3.client('s3')
source_bucket = 'demo-extensive-documents'  

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        folder_name = body['folder_name'] 
    except:
        folder_name = event['folder_name']

    if not folder_name:
        return {
            'statusCode': 400,
            'body': 'No folder name provided'
        }

    if not folder_name.endswith('/'):
        folder_name += '/'
    response = s3.list_objects_v2(Bucket=source_bucket, Prefix=folder_name)
    if 'Contents' not in response:
        return {
            'statusCode': 404,
            'body': f"No files found in the folder: {folder_name}"
        }

    output_bucket = "pdf-chunks-generated"

    generated_chunks = []

    for item in response['Contents']:
        file_key = item['Key']

        if not file_key.lower().endswith('.pdf') or item['Size'] == 0:
            continue
        pdf_response = s3.get_object(Bucket=source_bucket, Key=file_key)
        file_content = pdf_response['Body'].read()
        pdf_reader = PdfReader(io.BytesIO(file_content))

        total_pages = len(pdf_reader.pages)
        chunk_size = 50

        _, file_name = os.path.split(file_key)

        for start_page in range(0, total_pages, chunk_size):
            end_page = min(start_page + chunk_size, total_pages)
            pdf_writer = PdfWriter()

            for page_number in range(start_page, end_page):
                pdf_writer.add_page(pdf_reader.pages[page_number])

            output_stream = io.BytesIO()
            pdf_writer.write(output_stream)

            new_file_name = f"{file_name}_chunk_{start_page // chunk_size}.pdf"
            generated_chunks.append(new_file_name)

            s3.put_object(Bucket=output_bucket, Key=new_file_name, Body=output_stream.getvalue())

    return {
        'statusCode': 200,
        'body': generated_chunks
    }


