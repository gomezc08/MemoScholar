import os
from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI
from dotenv import load_dotenv
import json

def run_request(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    tool_registry: Dict[str, Any],
    model: str = "gpt-4o-mini",
    temperature: float = 0.1,
    max_tokens: int = 4000,
) -> Dict[str, Any]:
    
    # Get API key from environment
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    try:
        # Make the API call - recieve back a response on the type of tool(s) to use.
        tool_call_choices = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice="auto"
        )
        
        # Extract the tool call choices.
        tool_calls = tool_call_choices.choices[0].message
        
        # Add the tool call choices to the messages.
        messages.append({"role": "assistant", "content": tool_calls.content, "tool_calls": tool_calls.tool_calls})

        # Execute each tool call.
        for tool_call in tool_calls.tool_calls:
            # Get the tool call information.
            tool_name = tool_call.function.name
            args_json = tool_call.function.arguments or "{}"
            executor = tool_registry.get(tool_name)

            # Execute the tool call.
            if executor:
                try:
                    args = json.loads(args_json)
                    tool_result = executor(**args)
                except Exception as e:
                    tool_result = f"Error executing tool {tool_name}: {str(e)}"
            
            # Add the tool call result to the messages.
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": str(tool_result)
            })    

        # Return the messages.
        return messages
        
    except openai.APIError as e:
        return {
            "success": False,
            "error": f"OpenAI API error: {str(e)}",
            "error_type": "api_error"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "general_error"
        }