import boto3
import io
from PyPDF2 import PdfReader
import re
from report import generate_report
import os
import json

s3 = boto3.client('s3', region_name='us-east-1')
s3_client = boto3.client('s3')
bucket_name = "pdf-chunks-generated"
output_bucket = 'txt-files-chunks'

def lambda_handler(event, context):
    try: 
        body = json.loads(event['body'])
        pdf_file = body['key']
    except:
        pdf_file = event['key']

    if not pdf_file:
        raise Exception("pdf_file is required")
    
    folder_name = pdf_file.split('_')[0].replace('.pdf', '')
    pdf_response = s3_client.get_object(Bucket=bucket_name, Key=pdf_file)
    file_content = pdf_response['Body'].read()

    pdf_reader = PdfReader(io.BytesIO(file_content))
    total_pages = len(pdf_reader.pages)

    try:
        pdf_text = ""
        for page in range(len(pdf_reader.pages)):
            pdf_text += pdf_reader.getPage(page).extractText()

        try:            
            report = generate_report(pdf_text)
            json_content_after_report = re.findall(r'\{.*?\}', report, re.DOTALL)
            final_output = ""
            final_output += "".join(json_content_after_report) + "\n"
        except:
            json_content_after_report = ""
            
        unique_chunk_identifier = pdf_file.split('/')[-1]
        output_filename = f"{unique_chunk_identifier}.txt"
        new_file_name = f"{folder_name}/{output_filename}"

        s3.put_object(Bucket=output_bucket, Key=new_file_name, Body=final_output.encode('utf-8'))

    except Exception as e:
        print(f"Error processing file {pdf_file}: {str(e)}")
        
    return {
        'body': folder_name
    }