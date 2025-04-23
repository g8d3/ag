from google.adk.agents import Agent
from google.adk.tools import built_in_code_execution
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration --- #
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Ensure API key is loaded
if not GEMINI_API_KEY:
    raise ValueError("Gemini API key is missing in the .env file.")
import google.generativeai as genai
# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)
genai_model = genai.GenerativeModel('gemini-2.0-flash')
print("Gemini 2.0 Flash model initialized successfully.")

# Define the agent as root_agent
root_agent = Agent(
    name="ShellExecutingAgent",
    model="gemini-2.0-flash",
    tools=[built_in_code_execution],
    instruction="You are an agent that can execute shell commands. The user will provide natural language commands, and you should use the built_in_code_execution tool to execute them directly. Do not add any extra text or explanation. If the user says exit, then you should say exiting and terminate.",
    description="An agent for executing shell commands from natural language."
)