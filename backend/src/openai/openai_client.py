import os
from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI
from dotenv import load_dotenv
import json
from ..utils.logging_config import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

def run_request(
    prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.1,
    max_tokens: int = 4000,
    system_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Make a request to OpenAI API to generate a JSON schema.
    
    Args:
        prompt (str): The main prompt containing the UIA listener data
        model (str): OpenAI model to use (default: gpt-4o-mini)
        temperature (float): Creativity level (0.0 = focused, 1.0 = creative)
        max_tokens (int): Maximum tokens for the response
        system_message (str, optional): Additional system instructions
    
    Returns:
        Dict[str, Any]: OpenAI API response
        
    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set
        Exception: For other API errors
    """
    
    # Get API key from environment
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Prepare messages
    messages = []
    
    # Add system message if provided
    if system_message:
        messages.append({
            "role": "system",
            "content": system_message
        })
    
    # Add user message with the prompt
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    try:
        # Make the API call
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract the response content
        content = response.choices[0].message.content
        logger.info(f"OpenAI API call successful. Tokens used: {response.usage.total_tokens}")
        
        return {
            "success": True,
            "content": content,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
    except openai.APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return {
            "success": False,
            "error": f"OpenAI API error: {str(e)}",
            "error_type": "api_error"
        }
    except Exception as e:
        logger.error(f"Unexpected error in OpenAI call: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "general_error"
        }