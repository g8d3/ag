import os
from dotenv import load_dotenv
import subprocess
import google.generativeai as genai
from google.adk.agents import Agent
from google.adk.tools import built_in_code_execution

# Load environment variables from .env file
load_dotenv()

# --- Configuration --- #
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Ensure API key is loaded
if not GEMINI_API_KEY:
    raise ValueError("Gemini API key is missing in the .env file.")

# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.0-flash')
print("Gemini 2.0 Flash model initialized successfully.")

# Define the ShellCommandExecutor tool
shell_tool = built_in_code_execution

# Create the ADK agent
agent = Agent(
    name="ShellExecutingAgent",
    model="gemini-2.0-flash", # Or any other suitable Gemini model
    tools=[shell_tool],
    instruction="You are an agent that can execute shell commands. The user will provide natural language commands, and you should use the built_in_code_execution tool to execute them directly. Do not add any extra text or explanation. If the user says exit, then you should say exiting and terminate.",
    description="An agent for executing shell commands from natural language."
)

def agent_loop():
    """Main loop for the agent."""
    print("\n--- ADK Agent Loop Started ---")
    while True:
        user_input = input("Enter natural language command (or 'exit'): ").strip()

        if user_input.lower() == "exit":
            print("Exiting agent loop.")
            break
        elif user_input:
            print(f"Executing: '{user_input}'...")
            response = agent.run(user_input)
            print(f"Shell Output: {response}")
        else:
            print("Please enter a command or 'exit'.")

if __name__ == "__main__":
    agent_loop()
