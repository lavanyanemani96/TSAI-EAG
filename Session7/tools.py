from mcp.server.fastmcp import FastMCP
import math
import sys
import os

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from models import EmailResultInput, EmailResultOutput
from pathlib import Path

import faiss 
import json 
import numpy as np 

from sentence_transformers import SentenceTransformer
import google.generativeai as genai

from dotenv import load_dotenv
load_dotenv('paths.env')


# instantiate an MCP server client
mcp = FastMCP("Legal-Advice")


model_embed = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)  

def mcp_log(level: str, message: str) -> None:
    """Log a message to stderr to avoid interfering with JSON communication"""
    sys.stderr.write(f"{level}: {message}\n")
    sys.stderr.flush()
    
ROOT = Path(__file__).parent.resolve()

def ensure_faiss_ready():
    from pathlib import Path
    index_path = ROOT / "faiss-index-v1" / "faiss_index.index"
    meta_path = ROOT / "faiss-index-v1" / "faiss_metadata.json"
    if not (index_path.exists() and meta_path.exists()):
        mcp_log("INFO", "Index not found — Please create faiss_index...")
    else:
        mcp_log("INFO", "Index already exists. Skipping regeneration.")
    return str(index_path), str(meta_path)

def get_embedding(query: str) -> np.ndarray:
    query_embedding = model_embed.encode([query])
    return np.array(query_embedding).astype('float32')

@mcp.tool()
def email_result(recipient_email:str, answer:str) -> str:
    """Send an email using input.recipient_email and include input.answer as the result."""

    result = answer
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'lavanyanemani96@gmail.com'
    sender_password = os.getenv("GMAIL_APP_PASSWORD")  
    subject = "Agentic AI Result"
    body = f"Automated Agentic AI result: {result}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        mcp_log("INFO", "Email successfully sent")
        return f"Email successfully sent to {recipient_email}"
    except Exception as e:
        mcp_log("INFO", f"Failed to send email: {e}")
        return f"Failed to send email: {e}"

@mcp.tool()
def search_legal_documents(query: str) -> str:
    """Search for relevant content from collection of acts/judgements as legal documents"""
    index_path, meta_path = ensure_faiss_ready()
    mcp_log("SEARCH", f"Query: {query}")
    try:
        index = faiss.read_index(index_path)
        with open(meta_path, "r") as f:
            metadata = json.load(f)
        query_vec = get_embedding(query).reshape(1, -1)
        D, I = index.search(query_vec, k=10)
        results = ["Relevant legal documents:"]
        for idx in I[0]:
            data = metadata[idx]
            results.append(data['text'])
        return " ".join(results) 
    except Exception as e:
        return f"ERROR: Failed to search: {str(e)}"

if __name__ == "__main__":
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  
    else:
        mcp.run(transport="stdio") 
