from agno.agent import Agent
from agno.tools.shell import ShellTools
from agno.models.openrouter import OpenRouter
import os
import time
api_key = os.getenv("OPENROUTER_API_KEY", "your-api-key-here")

models_to_test = [
    # "openai/gpt-3.5-turbo",
    # "anthropic/claude-3.5-sonnet",
    # "mistralai/mixtral-8x7b-instruct",
    # "meta-llama/llama-3-70b-instruct",
    # "google/gemini-pro-1.5",
    # "google/gemini-flash-1.5-8b",
    # "qwen/qwen-2.5-7b-instruct",
    "openrouter/optimus-alpha",
    # "liquid/lfm-7b",
]

model_id=models_to_test[0]

agent = Agent(model=OpenRouter(id=model_id,
                               api_key=api_key,
                               base_url="https://openrouter.ai/api/v1"),
              tools=[ShellTools()], show_tool_calls=True, debug_mode=True)

start_time = time.time()
agent.print_response("Show me the contents of the current directory", markdown=True)
end_time = time.time()
elapsed_time = end_time - start_time
print(f"**Time Elapsed for {model_id}:** {elapsed_time:.2f} seconds")
