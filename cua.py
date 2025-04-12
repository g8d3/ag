# cua.py
import os
import subprocess
import re
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.storage.sqlite import SqliteStorage

class ComputerControlTools:
    def __init__(self):
        self.allowed_commands = {"dir", "ls", "mkdir", "systeminfo", "uname"}

    def execute_command(self, command: str) -> str:
        if os.name == 'nt':
            command_mappings = {"ls": "dir", "uname": "systeminfo"}
            command = command_mappings.get(command.split()[0], command)

        base_command = command.split()[0]
        if base_command not in self.allowed_commands:
            return f"Error: Command '{base_command}' not allowed."

        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return result.stdout or "Command executed (no output)"
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"

def create_computer_control_agent(api_key: str, db_file: str = "tmp/computer_agent.db"):
    tools = ComputerControlTools()

    def process_response(response) -> str:
        text = response.content if hasattr(response, 'content') else str(response)
        pattern = r'_execute_command\(tool="execute_command", command="([^"]+)"(?:\)|.*?\)_)'
        match = re.search(pattern, text)
        if match:
            command = match.group(1)
            return tools.execute_command(command)
        return text  # Fallback to raw response if no match

    agent = Agent(
        name="ComputerControlAgent",
        model=OpenRouter(id="openrouter/quasar-alpha", api_key=api_key, base_url="https://openrouter.ai/api/v1"),
        instructions=[
            "You are an AI assistant that runs safe shell commands.",
            "Respond only with `_execute_command(tool=\"execute_command\", command=\"<command>\")`.",
            "Do not add extra text."
        ],
        storage=SqliteStorage(table_name="computer_control", db_file=db_file),
        markdown=True,
        debug_mode=False  # Turned off as requested
    )
    # Wrap the agent's run method to include post-processing
    original_run = agent.run
    def run_with_processing(prompt):
        response = original_run(prompt)
        return process_response(response)
    agent.run = run_with_processing

    return agent

if __name__ == "__main__":
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your-api-key-here")
    if OPENROUTER_API_KEY == "your-api-key-here":
        print("Please set your OPENROUTER_API_KEY environment variable.")
        exit(1)

    agent = create_computer_control_agent(OPENROUTER_API_KEY)

    print("=== Testing directory listing ===")
    response = agent.run("List the contents of the current directory")
    print(response)

    print("\n=== Testing system info ===")
    response = agent.run("Tell me about this computer")
    print(response)

    print("\n=== Testing file creation ===")
    response = agent.run("Create a directory called 'test_folder'")
    print(response)