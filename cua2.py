import os
import subprocess
import re
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.storage.sqlite import SqliteStorage

# Shared command execution function
def execute_command(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout or "Command executed (no output)"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

# Tool processing function to handle command execution in responses
def process_tool_calls(agent):
    original_run = agent.run
    def run_with_tools(prompt):
        response = original_run(prompt)
        if hasattr(response, 'content'):
            content = response.content
            while "_execute_command" in content:
                cmd_match = re.search(r'_execute_command\(tool="execute_command", command="([^"]+)"\)', content)
                if cmd_match:
                    cmd = cmd_match.group(1)
                    result = execute_command(cmd)
                    content = content.replace(cmd_match.group(0), f"**Executed:** `{cmd}`\n**Result:** `{result}`")
                else:
                    break
            return content
        return str(response)
    agent.run = run_with_tools
    return agent

# Action Agent: Executes commands to achieve tasks
def create_action_agent(api_key: str, db_file: str = "tmp/action_agent.db"):
    agent = Agent(
        name="ActionAgent",
        model=OpenRouter(id="openrouter/quasar-alpha", api_key=api_key, base_url="https://openrouter.ai/api/v1"),
        instructions=[
            "You are an AI that executes shell commands and browser actions to achieve tasks.",
            "If you have questions answer them using commands.",
            "For each command, call `_execute_command(tool=\"execute_command\", command=\"<command>\")`.",
            "Show executed commands and their outcomes in markdown."
        ],
        tools={"execute_command": execute_command},
        storage=SqliteStorage(table_name="action_agent", db_file=db_file),
        markdown=True,
        debug_mode=False
    )
    return process_tool_calls(agent)

# Review Agent: Analyzes results and can execute additional commands
def create_review_agent(api_key: str, db_file: str = "tmp/review_agent.db"):
    agent = Agent(
        name="ReviewAgent",
        model=OpenRouter(id="deepseek/deepseek-chat-v3-0324:free", api_key=api_key, base_url="https://openrouter.ai/api/v1"),
        instructions=[
            "You will be given: 1. goal, 2. commands run, 3. outputs of commands",
            "Determine if goal is achieved",
            "If needed, run additional commands using `_execute_command(tool=\"execute_command\", command=\"<command>\")`"
        ],
        tools={"execute_command": execute_command},
        storage=SqliteStorage(table_name="review_agent", db_file=db_file),
        markdown=True,
        debug_mode=False
    )
    return process_tool_calls(agent)

def run_agents():
    api_key = os.getenv("OPENROUTER_API_KEY", "your-api-key-here")
    if api_key == "your-api-key-here":
        print("Please set your OPENROUTER_API_KEY environment variable.")
        exit(1)

    action_agent = create_action_agent(api_key)
    review_agent = create_review_agent(api_key)

    # Action prompt
    # goal = "install browsh"
    goal = "Show me the contents of the current directory"
    # Execute actions
    print("Running Action Agent...")
    action_result = action_agent.run(goal)
    print("Action Agent Result:")
    print(action_result)

    # Review prompt
    # review_prompt = (
    #     "goal:\n" + goal + "\n"
    #     "commands and outputs:\n"
    #     "```\n" + action_result + "\n```\n"
    # )

    # Review results
    # print("\nRunning Review Agent...")
    # review_result = review_agent.run(review_prompt)
    # print("Review Agent Result:")
    # print(review_result)

if __name__ == "__main__":
    os.makedirs("tmp", exist_ok=True)
    run_agents()