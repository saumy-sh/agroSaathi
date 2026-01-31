import base64
import os
from google import genai
from google.genai import types
from config import Config

class LLMService:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            print("WARNING: GEMINI_API_KEY not set in environment variables.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash-lite"

    def generate_response(self, context, disease_info, user_query):
        """
        Generate answer using RAG context and Gemini 2.5 Flash Lite.
        """
        
        search_prompt = f"""
        You are an intelligent agricultural assistant called AgroSaathi.
        
        Context from Knowledge Base:
        {context}
        
        Disease Detected (if any):
        {disease_info}
        
        User Query:
        {user_query}
        
        Based on the context and disease information provided above, provide a helpful, concise, and accurate answer to the farmer's query. 
        If a disease is detected, prioritize remedies for it.
        Keep the answer simple and easy to understand.
        """

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=search_prompt),
                ],
            ),
        ]
        
        # We can enable Google Search grounding if needed, but per prompt we stick to RAG context primarily
        # adding thinking_config=0 as requested
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
        )

        try:
            # We use the stream variable to buffer the whole response for simplicity in this API
            full_response = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                full_response += chunk.text
            
            return full_response
            
        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return "I apologize, but I am unable to process your request at the moment."

llm_service = LLMService()
