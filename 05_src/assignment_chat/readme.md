# Dr. Eval: The Item Developer

## Overview
**Dr. Eval** is an AI system with a conversational interface designed to act as a psychometrician and instructional design assistant. The nature of this chat client is to help educators, instructional designers, and educational psychologists write, critique, and evaluate multiple-choice test items. The bot assumes the distinct personality of a precise, academic, yet encouraging assessment expert. 

This project fulfills the assignment requirements by integrating a chat-based interface that maintains memory throughout the conversation, utilizes three distinct backend services, and enforces strict guardrails. All code is implemented in the `./05_src/assignment_chat` folder.

## Services Provided

This system implements the three required services:

### 1. External API Integration (Content Generation)
*   **Service:** Wikipedia REST API (`/api/rest_v1/page/summary/`). This serves as the service that uses an API as its back end.
*   **Implementation:** When a user asks Dr. Eval to generate an item about a specific topic, the system fetches the introductory summary from Wikipedia. 
*   **Transformation:** The response is not provided verbatim. Instead, the LLM uses the Wikipedia summary as context to generate an original reading comprehension passage, followed by a pedagogically sound multiple-choice question (stem, correct key, and three plausible distractors).

### 2. Semantic Query (Item Critique)
*   **Service:** Local ChromaDB instance with file persistence. 
*   **Dataset:** A custom CSV file read with pandas (`assessment_frameworks.csv`) containing 31 multiple-choice item writing rules by Haladyna and the 6 cognitive dimensions of the Revised Bloom's Taxonomy. 
*   **Implementation:** When a user submits an item for critique, the system resolves the question through a semantic search against the frameworks dataset. It retrieves the most relevant psychometric rules or cognitive levels to provide highly targeted, evidence-based feedback on the user's question.

### 3. Function Calling (Readability Evaluation)
*   **Service:** OpenAI Function Calling (Custom `calculate_readability` tool).
*   **Implementation:** To ensure that test items measure content knowledge rather than reading ability, users can ask the bot to evaluate the reading level of a specific question. The LLM triggers a custom Python function that analyzes the text's complexity (simulated via average word length) and returns a structured classification (e.g., "Medium Reading Level (High School)").

## Guardrails and Limitations

Guardrails have been implemented to restrict system behavior according to the requirements:
*   **Prompt Protection:** The system is explicitly instructed to prevent users from accessing, revealing, or modifying the system prompt directly.
*   **Restricted Topics:** The model is programmed not to respond to questions on restricted topics, specifically: cats or dogs, horoscopes or Zodiac signs, and Taylor Swift. If asked about these, the bot redirects the conversation back to educational measurement.

## Implementation Decisions

*   **Modular Architecture:** The codebase is split into `app.py` (Gradio UI), `main.py` (OpenAI tool execution and ChromaDB setup), and `prompts.py` (System instructions and guardrails). This keeps the code clean and organized.
*   **Metadata Filtering in ChromaDB:** Instead of creating separate databases for Haladyna's rules and Bloom's Taxonomy, both frameworks are stored in a single dataset. The Python backend applies metadata filtering to the ChromaDB query, allowing the bot to search the entire database holistically or filter by a specific framework if the user requests it.
*   **Memory Management:** The chat interface passes the sanitized conversation history back to the OpenAI client with every request, ensuring the bot maintains short-term memory for multi-turn interactions.

## Setup Instructions
1. Ensure your standard course environment is active.
2. Verify that `OPENAI_MODEL` and your OpenAI API keys are set in your `.env` or `.secrets` file.
3. Run `python app.py` to launch the chat interface.