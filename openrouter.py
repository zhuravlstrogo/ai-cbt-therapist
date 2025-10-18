import requests
import json
import os
from typing import Dict, Any, Optional, Tuple

# Get API key and model parameters from config.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPENROUTER_API_KEY, TEMPERATURE, TEMPERATURE_STRUCTURED, TOP_P, TOP_K, MODEL_STRUCTURED


class OpenRouterClient:
    def __init__(self, api_key: str = OPENROUTER_API_KEY):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_structured_response(
        self,
        prompt: str,
        json_schema: Dict[str, Any],
        model: str = MODEL_STRUCTURED,
        temperature: float = TEMPERATURE,
        temperature_structured: float = TEMPERATURE_STRUCTURED,
        top_p: float = TOP_P,
        top_k: Optional[int] = TOP_K,
        system_message: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, int]]:
        """
        Get a structured response from OpenRouter API.
        
        Args:
            prompt: The user prompt
            json_schema: The JSON schema to structure the response
            model: The model to use
            temperature: Temperature for response generation
            temperature_structured: Temperature for structured responses
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            system_message: Optional system message
            
        Returns:
            Tuple containing (structured_response, usage_info)
            where usage_info contains 'prompt_tokens' and 'completion_tokens'
        """
        messages = []
        
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
            
        messages.append({
            "role": "user",
            "content": prompt
        })

        data = {
            "model": model,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": json_schema
            },
            "temperature": temperature_structured,  # Используем temperature_structured для структурированных ответов
            "top_p": top_p,
        }
        
        # Добавляем top_k только если он не None
        if top_k is not None:
            data["top_k"] = top_k

        try:
            response = requests.post(self.base_url, headers=self.headers, json=data, timeout=60)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                except json.JSONDecodeError as e:
                    print(f"JSON decode error in structured response: {e}")
                    print(f"Response content (first 1000 chars): {response.text[:1000]}")
                    print(f"Response content (last 1000 chars): {response.text[-1000:]}")
                    raise Exception(f"Invalid JSON response from API: {str(e)}")
                
                # Extract usage information
                usage_info = {}
                if "usage" in result:
                    usage_info = {
                        "prompt_tokens": result["usage"].get("prompt_tokens", 0),
                        "completion_tokens": result["usage"].get("completion_tokens", 0),
                        "total_tokens": result["usage"].get("total_tokens", 0)
                    }
                else:
                    usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    try:
                        structured_response = json.loads(content)
                        return structured_response, usage_info
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error in message content: {e}")
                        print(f"Message content: {content}")
                        raise Exception(f"Invalid JSON in message content: {str(e)}")
                else:
                    print(f"Unexpected response structure: {result}")
                    raise Exception("Unexpected response structure")
            else:
                print(f"API error - Status: {response.status_code}")
                print(f"Response content: {response.text}")
                raise Exception(f"Error: {response.status_code}\nResponse content: {response.text}")
        except requests.exceptions.Timeout:
            raise Exception("Request timed out after 60 seconds")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def get_simple_response(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = TEMPERATURE,
        top_p: float = TOP_P,
        top_k: Optional[int] = TOP_K,
        max_retries: int = 3
    ) -> Tuple[str, Dict[str, int]]:
        """
        Get a simple text response with token usage information.
        
        Returns:
            Tuple containing (response_text, usage_info)
        """
        import time
        from requests.exceptions import Timeout, RequestException
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
        }
        
        # Добавляем top_k только если он не None
        if top_k is not None:
            data["top_k"] = top_k

        last_exception = None
        
        for attempt in range(max_retries):
            if attempt > 0:
                wait_time = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
                print(f"Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            
            print(f"Making API request to {self.base_url} with model {model}... (attempt {attempt + 1}/{max_retries})")
            
            try:
                response = requests.post(self.base_url, headers=self.headers, json=data, timeout=60)
                print(f"API request completed with status code: {response.status_code}")
                
                if response.status_code == 200:
                    # Check if response is empty or contains only whitespace
                    response_text = response.text.strip()
                    if not response_text:
                        error_msg = "API returned empty response"
                        print(error_msg)
                        last_exception = Exception(error_msg)
                        continue  # Retry
                    
                    # Check if response is only whitespace
                    if response_text.isspace() or len(response_text.strip()) == 0:
                        error_msg = f"API returned response containing only whitespace (length: {len(response.text)})"
                        print(error_msg)
                        last_exception = Exception(error_msg)
                        continue  # Retry
                    
                    try:
                        result = response.json()
                    except json.JSONDecodeError as e:
                        error_msg = f"Invalid JSON response from API: {str(e)}"
                        print(f"JSON decode error: {e}")
                        print(f"Response content (first 1000 chars): {response.text[:1000]}")
                        print(f"Response content (last 1000 chars): {response.text[-1000:]}")
                        print(f"Response headers: {dict(response.headers)}")
                        last_exception = Exception(error_msg)
                        continue  # Retry
                    
                    # Extract usage information
                    usage_info = {}
                    if "usage" in result:
                        usage_info = {
                            "prompt_tokens": result["usage"].get("prompt_tokens", 0),
                            "completion_tokens": result["usage"].get("completion_tokens", 0),
                            "total_tokens": result["usage"].get("total_tokens", 0)
                        }
                    else:
                        usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"].strip()
                        print(f"Successfully received response of length: {len(content)}")
                        return content, usage_info
                    else:
                        error_msg = "Unexpected response structure"
                        print(f"Unexpected response structure: {result}")
                        last_exception = Exception(error_msg)
                        continue  # Retry
                else:
                    error_msg = f"API error - Status: {response.status_code}, Content: {response.text}"
                    print(f"API error - Status: {response.status_code}")
                    print(f"Response content: {response.text}")
                    last_exception = Exception(error_msg)
                    continue  # Retry
                    
            except Timeout:
                error_msg = "Request timed out after 60 seconds"
                print(error_msg)
                last_exception = Exception(error_msg)
                continue  # Retry
            except RequestException as e:
                error_msg = f"Request failed: {str(e)}"
                print(error_msg)
                last_exception = Exception(error_msg)
                continue  # Retry
        
        # If we get here, all retries failed
        print(f"All {max_retries} attempts failed")
        if last_exception:
            raise last_exception
        else:
            raise Exception("All retry attempts failed with unknown error")


# JSON schema for OKVED matching
json_schema = {
    "name": "response",
    "schema": {
        "type": "object",
        "properties": {
            "product": {
                "type": "string",
                "description": "brief description of how a specific product or service sounds in practice"
            },
            "analysis": {
                "type": "string",
                "description": "semantic analysis of the product or service"
            },
            "code": {
                "type": "string",
                "description": "the code is a strictly appropriate format (XX.X / XX.XX / XX.XX.X / XX.XX.XX)"
            }
        },
        "required": ["product", "analysis", "code"],
        "additionalProperties": False
    }
}