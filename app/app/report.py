from langchain.prompts import ChatPromptTemplate
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader,DirectoryLoader
from langchain.vectorstores import FAISS
import boto3
from langchain.embeddings import BedrockEmbeddings
from langchain.llms import Bedrock
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.chains import LLMChain
from PyPDF2 import PdfReader
import botocore
import time

bedrock_client = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1",
                                       client=bedrock_client)

llm = Bedrock(model_id="anthropic.claude-v2:1", client=bedrock_client, model_kwargs={'max_tokens_to_sample': 40000, 'temperature': 0.3, 'stop_sequences': ['Human:']})

def splitt_document(chunks):
    text_splitter = RecursiveCharacterTextSplitter(
        separators = "\n\n",
        chunk_size = 1500,
        chunk_overlap  = 250,
        length_function = len,
    )
    documents_split = text_splitter.split_text(chunks)
    return documents_split

def get_vectorstore(text_chunks, embedding):
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embedding)
    return vectorstore

def weaknesses_list(vectorstore, llm_model):
    QA_PROMPT = PromptTemplate(
        input_variables=["contexts"],
    template="""
    You are an application security researcher with expertise in software and cloud security, tasked with analyzing technical documents. Your role is to identify specific security weaknesses that are directly related to the technologies and practices mentioned in the document. Focus on extracting security vulnerabilities and weaknesses that are explicitly stated or strongly implied in the context.

    1. Generate a list of weaknesses and security concerns explicitly expressed and contained in the context.
    2. Focus on weaknesses related to security vulnerabilities and risks, such as authentication, authorization, data encryption, network security, and other relevant security measures.
    3. Enumerate the identified security risks and vulnerabilities found in the context in a concise list.
    4. Provide only the names of the vulnerabilities in the output list.
    5. Example of a vulnerability format: 'Inadequate encryption methods'
    6. Ensure that your responses are specific to the information present in the context and directly relevant to the document's technology or practice.

    Contexts:
    {contexts}""",
    )

    qa_chain = LLMChain(llm=llm_model, prompt=QA_PROMPT)
    
    query_ws = "security weaknesses, security concerns, vulnerabilities. Consider aspects such as authentication, authorization, data encryption, network security, and any other relevant security measures"

    context_docs_ws = vectorstore.similarity_search(query_ws, k=10)
    out_ws = qa_chain(
        inputs={
            "query": query_ws,
            "contexts": "\n---\n".join([d.page_content for d in context_docs_ws]),
            }
            )

    weaknesses = out_ws["text"]
    return weaknesses

def extract_context_countermeasures(weaknesses, vectorstore):
    query_cs = "Security countermeasures for vulnerabilities in software and cloud application development, focusing on addressing specific vulnerabilities such as: {weaknesses}. Emphasize practical implementation of mitigation techniques for these vulnerabilities. Include topics on multi-factor authentication, encryption, access control, secure coding practices, and compliance with industry standards. Search for actionable instructions, guidelines, and practices that ensure robust security in addressing these specific weaknesses."
    query_cs = query_cs.format(weaknesses="".join(weaknesses))

    context_docs_cs = vectorstore.similarity_search(query_cs, k=10)
    context = "\n---\n".join([d.page_content for d in context_docs_cs])
    return context, query_cs

def countermeasure_list(context, query_cs, llm_model):
    QA_PROMPT = PromptTemplate(
        input_variables=[context],
    template="""
    You are an experienced application security researcher specializing in software, mobile, cloud, and DevOps security. Your task is to analyze the context and directly extract all countermeasures related to the identified security weaknesses and vulnerabilities. Follow these guidelines:

    1. Extract countermeasures explicitly expressed and contained in the context.
    2. Focus on countermeasures related to security weaknesses and vulnerabilities, such as authentication, authorization, data encryption, network security, and other relevant security measures.
    3. Ensure each countermeasure directly addresses a specific weakness mentioned in the context.
    4. The countermeasures should be practical, relevant to the context, and not include tools or technologies not referenced in the document.
    5. Focus on providing actionable and specific mitigation strategies.
    6. Define a countermeasure as a specific instruction, principle, or practice that mitigates or minimizes weaknesses and vulnerabilities.
    7. Exclude general error handling or good practices unless they are directly related to addressing a specific security weakness or vulnerability.
    8. Provide a detailed description of each countermeasure, including implementation steps and examples, in a JSON structure as shown below:
    open brace 
        "title": "Countermeasure Title",
        "description": "Detailed description of the countermeasure with implementation steps and examples.",
        "target": "Addressed Weakness or Security Problem",
        "context": "Relevant text from input",
        "tags": ["Tag1", "Tag2", "Any other relevant tag from taxonomy_tags list below"],
    close brace
    9. Ensure completeness in each JSON response; all responses need to have the same structure.
    10. Taxonomy_tags: ['Authentication', 'Authorization', 'Access Control', 'Integrity', 'Confidentiality', 'Availability', 'Cryptography', 'Input Validation', 'Security Controls', 'Code Analysis', 'Compliance', 'Security Policies', 'Best Practices']
    11. If no countermeasure is found based on the above criteria, return an empty list.

    Contexts:
    {context}"""
    )
    
    qa_chain = LLMChain(llm=llm_model, prompt=QA_PROMPT)

    out_cs = qa_chain(
         inputs={
              "query": query_cs,
              "context": context,
              }
              )
    countermeasures = out_cs["text"]
    return countermeasures
            
def generate_report(document):
    split_document = splitt_document(document)
    vectorstore = get_vectorstore(split_document, bedrock_embeddings)
    weaknesses = weaknesses_list(vectorstore, llm)
    context, query = extract_context_countermeasures(weaknesses, vectorstore)
    countermeasures_report = countermeasure_list(context, query, llm)
    return countermeasures_report