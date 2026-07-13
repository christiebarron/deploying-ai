from openai import OpenAI
from dotenv import load_dotenv
from prompts import return_instructions_root
import json
import requests
import chromadb
import pandas as pd
from utils.logger import get_logger
import os

_logs = get_logger(__name__)

load_dotenv(".env")
load_dotenv(".secrets")

client = OpenAI()
open_ai_model = os.getenv("OPENAI_MODEL", "gpt-4")

# ==========================================
# CHROMADB SETUP (Service 2)
# ==========================================
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="assessment_frameworks")

if collection.count() == 0:
    # Ensure assessment_frameworks.csv is in the root folder
    if os.path.exists("assessment_frameworks.csv"):
        df = pd.read_csv("assessment_frameworks.csv")
        documents = df['Rule_or_Concept'].astype(str) + " - " + df['Rationale'].astype(str)
        ids = [f"item_{i}" for i in range(len(df))]
        metadatas = [{"framework": row['Framework'].lower(), "category": row['Category']} for _, row in df.iterrows()]
        collection.add(documents=documents.tolist(), metadatas=metadatas, ids=ids)

# ==========================================
# TOOL DEFINITIONS[cite: 4]
# ==========================================
tools = [
    {
        "type": "function",
        "name": "get_wikipedia_summary",
        "description": "Fetches a summary from Wikipedia to be used as context for generating a test item.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The subject matter topic for the test item (e.g., Photosynthesis, The Water Cycle).",
                }
            },
            "required": ["topic"],
            "additionalProperties": False
        },
    },
    {
        "type": "function",
        "name": "critique_item",
        "description": "Retrieves educational assessment frameworks (like Bloom's Taxonomy or Haladyna's rules) to critique a test item.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "item_text": {
                    "type": "string",
                    "description": "The multiple-choice item provided by the user.",
                },
                "framework": {
                    "type": "string",
                    "description": "The specific framework to use. Accepted values are: 'bloom', 'haladyna', or 'all'.",
                    "default": "all"
                }
            },
            "required": ["item_text", "framework"],
            "additionalProperties": False
        },
    },
    {
        "type": "function",
        "name": "calculate_readability",
        "description": "Calculates the estimated reading level of a given test item.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text of the test item to evaluate.",
                }
            },
            "required": ["text"],
            "additionalProperties": False
        },
    }
]

# ==========================================
# TOOL EXECUTION FUNCTIONS[cite: 4]
# ==========================================
def execute_wikipedia_summary(topic: str) -> str:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        return data.get('extract', 'No summary found.')
    return "Error fetching topic."

def execute_critique_item(item_text: str, framework: str = "all") -> str:
    filter_dict = None
    if framework.lower() in ["bloom", "haladyna"]:
        filter_dict = {"framework": framework.lower()}
    
    if filter_dict:
        results = collection.query(query_texts=[item_text], n_results=3, where=filter_dict)
    else:
        results = collection.query(query_texts=[item_text], n_results=3)
        
    if results and results['documents']:
        return " ".join(results['documents'][0])
    return "No specific rules found for this query."

def execute_calculate_readability(text: str) -> str:
    words = text.split()
    avg_word_length = sum(len(word) for word in words) / max(1, len(words))
    if avg_word_length > 6:
        return "High Reading Level (College/Advanced)"
    elif avg_word_length > 4.5:
        return "Medium Reading Level (High School)"
    else:
        return "Low Reading Level (Elementary/Middle School)"

def sanitize_history(history: list[dict]) -> list[dict]:
    clean_history = []
    for msg in history:
        clean_history.append({
            "role": msg.get("role"),
            "content": msg.get("content")
        })
    return clean_history

# ==========================================
# MAIN CHAT FUNCTION[cite: 4]
# ==========================================
def eval_chat(message: str, history: list[dict] = []) -> str:
    _logs.info(f'User message: {message}')
    
    instructions = return_instructions_root()
    
    user_msg = {
        "role": "user",
        "content": message
    }
    
    conversation_input = sanitize_history(history) + [user_msg]
    
    response = client.responses.create(
        model=open_ai_model,  
        instructions=instructions,
        input=conversation_input,
        tools=tools,
    )
    
    conversation_input += response.output

    # Handle function calls if any[cite: 4]
    for item in response.output:
        if item.type == "function_call":
            args = json.loads(item.arguments)
            _logs.info(f'Function call args: {args}')
            
            # Route to the correct function
            if item.name == "get_wikipedia_summary":
                tool_result = execute_wikipedia_summary(**args)
            elif item.name == "critique_item":
                tool_result = execute_critique_item(**args)
            elif item.name == "calculate_readability":
                tool_result = execute_calculate_readability(**args)
            else:
                tool_result = "Tool not found."
            
            func_call_output = {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps({
                    "result": tool_result
                })
            }
            
            _logs.debug(f"Function call output: {func_call_output}")

            conversation_input = conversation_input + [func_call_output]
            
            # Make second API call with function result[cite: 4]
            response = client.responses.create(
                model=open_ai_model,
                instructions=instructions,
                tools=tools,
                input=conversation_input
            )
            break
            
    return response.output_text