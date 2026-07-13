import gradio as gr
from main import eval_chat
from dotenv import load_dotenv
import os

from utils.logger import get_logger

_logs = get_logger(__name__)

load_dotenv('.secrets')

chat = gr.ChatInterface(
    fn=eval_chat,
    type="messages",
    title="Dr. Eval - The Item Developer",
    description="Ask me to generate an item, critique an item, or evaluate an item's reading level.",
    examples=[
        {"text": "Generate a test item about the Water Cycle."},
        {"text": "Critique this item using Bloom's Taxonomy: Which of the following is true?"},
        {"text": "Is this item appropriate for 6th grade? 'The mitochondria is the powerhouse of the cell.'"}
    ]
)

if __name__ == "__main__":
    _logs.info('Starting Dr. Eval Chat App...')
    chat.launch()