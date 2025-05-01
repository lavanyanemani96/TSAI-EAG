# Legal QnA

Imagine you're in some legal trouble, or just curious. The legal landscape is hard to parse. Enter this Legal QnA based on RAG. Ask any legal question and get your answers emailed to you privately. 

## Features
- **Legal RAG**: Answer legal questions using real acts/judgements from the Union Act of India. 
- **Email results**: Get your answers emailed to you privately!

## File Structure
- `action.py` — Executes functions. 
- `agent.py` — Agent interface
- `decision.py` — LLM decides which functions to call / what steps to take!
- `memory.py` — Keep track of old interactions. 
- `models.py` — Pydantic models for ensuring the right argumnet types are passed.  
- `perception.py` — LLM first analyzes what it needs to do!
- `tools.py` — Define all MCP tools accessible to the Agent. 
- `README.md` — This documentation

## Usage
- Run the agent 
'''
python agent.py
'''
- Enter your query and email when prompted. 
- Edit paths.env with GEMINI_API_KEY (required for LLM access) and GMAIL_APP_PASSWORD (required to email answers)

## Documnets 
This work is partially private as I'm adding a large corpus of data and building a holistic Legal QnA tool. Example document is provided as: 
```
├── documents-v1
│   ├── content
│   │   └── 1074_170197905.txt 
│   └── metadata
│       └── 1074_170197905.json 
├── faiss-index-v1
│   ├── faiss_index.index
│   ├── faiss_metadata.json
│   └── info.txt
```

