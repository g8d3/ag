import os
import subprocess
import requests
import time
from typing import Any, Dict, List, Optional

class OpenRouter:
    def __init__(self, id: str, api_key: str, base_url: str):
        self.id = id
        self.api_key = api_key
        self.base_url = base_url

class ShellTools:
    def execute(self, command: str) -> str:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return result.stdout or "Command executed (no output)"
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

class Agent:
    def __init__(self, model: OpenRouter, tools: List[Any], show_tool_calls: bool = False):
        self.model = model
        self.tools = {tool.__class__.__name__: tool for tool in tools}
        self.show_tool_calls = show_tool_calls

    def _call_api(self, prompt: str) -> Dict:
        full_prompt = (
            f"You are a helpful AI that executes shell commands to assist users. "
            f"For the request: '{prompt}', provide a shell command that works on the user's OS. "
            f"Return the command in the format: [shell]command[/shell]. "
            f"Detect the OS based on common conventions (e.g., 'dir' for Windows, 'ls' for Unix-like). "
            f"Current OS hint: {'Windows' if os.name == 'nt' else 'POSIX'}."
        )
        headers = {
            "Authorization": f"Bearer {self.model.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Shell Command Agent"
        }
        data = {
            "model": self.model.id,  # Use full model ID to avoid splitting issues
            "messages": [{"role": "user", "content": full_prompt}],
            # Avoid parameters that might break non-OpenAI models
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        try:
            response = requests.post(
                f"{self.model.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10  # Increased timeout for stability
            )
            print(f"Model: {self.model.id}, Status: {response.status_code}, Response: {response.text[:200]}...")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            error_msg = f"API call failed for model {self.model.id}: {str(e)}"
            if 'response' in locals():
                error_msg += f"\nStatus Code: {response.status_code}\nResponse Text: {response.text}"
            raise Exception(error_msg)

    def _execute_tools(self, content: str) -> str:
        if "ShellTools" not in self.tools:
            return content
        
        shell_tool = self.tools["ShellTools"]
        start_tag = "[shell]"
        end_tag = "[/shell]"
        if start_tag in content and end_tag in content:
            start_idx = content.index(start_tag) + len(start_tag)
            end_idx = content.index(end_tag)
            cmd = content[start_idx:end_idx].strip()
            result = shell_tool.execute(cmd)
            if self.show_tool_calls:
                return f"**Tool Call:** ShellTools.execute('{cmd}')\n**Result:**\n```\n{result}\n```"
            return result
        return content

    def run(self, prompt: str) -> str:
        api_response = self._call_api(prompt)
        content = api_response.get("choices", [{}])[0].get("message", {}).get("content", prompt)
        return self._execute_tools(content)

    def print_response(self, prompt: str, markdown: bool = True) -> None:
        response = self.run(prompt)
        if markdown:
            print(f"**Prompt:** {prompt}\n**Response:**\n{response}")
        else:
            print(response)

# Usage
api_key = os.getenv("OPENROUTER_API_KEY", "your-api-key-here")
if api_key == "your-api-key-here":
    print("Please set your OPENROUTER_API_KEY environment variable.")
    exit(1)

# Test multiple models
models_to_test = [
    # "openai/gpt-3.5-turbo",
    # "anthropic/claude-3.5-sonnet",
    # "mistralai/mixtral-8x7b-instruct",
    # "meta-llama/llama-3-70b-instruct",
    # "google/gemini-pro-1.5",
    # "google/gemini-flash-1.5-8b",
    "google/gemini-flash-2.0",
    # "qwen/qwen-2.5-7b-instruct",
    # "openrouter/optimus-alpha",
    # "openrouter/quasar-alpha",
    # "liquid/lfm-7b",
    # "deepseek/deepseek-r1-distill-qwen-1.5b"
]

for model_id in models_to_test:
    print(f"\nTesting model: {model_id}")
    agent = Agent(
        model=OpenRouter(
            id=model_id,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        ),
        tools=[ShellTools()],
        show_tool_calls=True
    )
    
    # Measure time elapsed
    start_time = time.time()
    try:
        agent.print_response("Show me the contents of the current directory", markdown=True)
    except Exception as e:
        print(f"Error with {model_id}: {str(e)}")
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"**Time Elapsed for {model_id}:** {elapsed_time:.2f} seconds")
