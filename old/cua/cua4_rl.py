import os
import subprocess
import requests
import time
import json
from typing import Any, Dict, List, Optional
import uuid
import random
import numpy as np

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

class FileTools:
    def save(self, content: str, filename: str) -> str:
        try:
            with open(filename, 'w') as f:
                f.write(content)
            return f"Saved to {filename}"
        except Exception as e:
            return f"Error saving file: {str(e)}"

    def read(self, filename: str) -> str:
        try:
            with open(filename, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

class Agent:
    def __init__(self, model: OpenRouter, tools: List[Any], show_tool_calls: bool = False):
        self.model = model
        self.tools = {tool.__class__.__name__: tool for tool in tools}
        self.show_tool_calls = show_tool_calls

    def _call_api(self, prompt: str, max_tokens: int = 2000) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.model.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Code Generation Agent"
        }
        data = {
            "model": self.model.id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                f"{self.model.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=15
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
        for tool_name, tool in self.tools.items():
            start_tag = f"[{tool_name}]"
            end_tag = f"[/{tool_name}]"
            if start_tag in content and end_tag in content:
                start_idx = content.index(start_tag) + len(start_tag)
                end_idx = content.index(end_tag)
                cmd = content[start_idx:end_idx].strip()
                if tool_name == "ShellTools":
                    result = tool.execute(cmd)
                elif tool_name == "FileTools":
                    parts = cmd.split(":")
                    if parts[0] == "save" and len(parts) == 3:
                        result = tool.save(parts[1], parts[2])
                    elif parts[0] == "read" and len(parts) == 2:
                        result = tool.read(parts[1])
                    else:
                        result = "Invalid FileTools command"
                else:
                    result = "Unknown tool"
                if self.show_tool_calls:
                    return f"**Tool Call:** {tool_name}.execute('{cmd}')\n**Result:**\n```\n{result}\n```"
                return result
        return content

    def run(self, prompt: str, max_tokens: int = 2000) -> str:
        api_response = self._call_api(prompt, max_tokens)
        content = api_response.get("choices", [{}])[0].get("message", {}).get("content", prompt)
        return self._execute_tools(content)

class EvaluatorAgent:
    def __init__(self, model: OpenRouter):
        self.model = model

    def evaluate_code(self, code: str, project_type: str, project_description: str, test_results: str) -> Dict:
        prompt = (
            f"You are an expert code reviewer. Evaluate the following code for a {project_type} project ({project_description}):\n\n"
            f"```python\n{code}\n```\n\n"
            f"Test Results:\n{test_results}\n\n"
            f"Score it from 0 to 100 based on:\n"
            f"1. **Functionality (50%):** Does it meet the requirements? Weight test pass rate heavily.\n"
            f"2. **Code Quality (50%):** Is it modular, follows DRY and CoC principles, and uses a reusable library?\n\n"
            f"Return a JSON object with: score (int), functionality_feedback (str), quality_feedback (str)."
        )
        headers = {
            "Authorization": f"Bearer {self.model.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Code Evaluator"
        }
        data = {
            "model": self.model.id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(
                f"{self.model.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
            return json.loads(content)
        except Exception as e:
            return {"score": 0, "functionality_feedback": f"Evaluation failed: {str(e)}", "quality_feedback": ""}

class RLAlgorithm:
    def __init__(self, name: str):
        self.name = name
        self.q_table = {}  # For Q-Learning/SARSA
        self.policy = {}   # For PPO

    def update(self, state: str, action: str, reward: float, next_state: str, next_action: Optional[str] = None) -> str:
        raise NotImplementedError

    def get_action(self, state: str) -> str:
        raise NotImplementedError

class QLearning(RLAlgorithm):
    def __init__(self, alpha: float = 0.1, gamma: float = 0.9, epsilon: float = 0.1):
        super().__init__("Q-Learning")
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

    def update(self, state: str, action: str, reward: float, next_state: str, next_action: Optional[str] = None) -> str:
        self.q_table.setdefault(state, {})
        self.q_table[state].setdefault(action, 0.0)
        next_q = max(self.q_table.get(next_state, {}).values(), default=0.0)
        self.q_table[state][action] += self.alpha * (reward + self.gamma * next_q - self.q_table[state][action])
        return action

    def get_action(self, state: str) -> str:
        if random.random() < self.epsilon:
            return random.choice(["improve_modularity", "add_features", "fix_bugs"])
        self.q_table.setdefault(state, {})
        if not self.q_table[state]:
            return random.choice(["improve_modularity", "add_features", "fix_bugs"])
        return max(self.q_table[state].items(), key=lambda x: x[1])[0]

class SARSA(RLAlgorithm):
    def __init__(self, alpha: float = 0.1, gamma: float = 0.9, epsilon: float = 0.1):
        super().__init__("SARSA")
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

    def update(self, state: str, action: str, reward: float, next_state: str, next_action: Optional[str] = None) -> str:
        if next_action is None:
            next_action = self.get_action(next_state)
        self.q_table.setdefault(state, {})
        self.q_table[state].setdefault(action, 0.0)
        self.q_table.setdefault(next_state, {})
        self.q_table[next_state].setdefault(next_action, 0.0)
        self.q_table[state][action] += self.alpha * (reward + self.gamma * self.q_table[next_state][next_action] - self.q_table[state][action])
        return next_action

    def get_action(self, state: str) -> str:
        if random.random() < self.epsilon:
            return random.choice(["improve_modularity", "add_features", "fix_bugs"])
        self.q_table.setdefault(state, {})
        if not self.q_table[state]:
            return random.choice(["improve_modularity", "add_features", "fix_bugs"])
        return max(self.q_table[state].items(), key=lambda x: x[1])[0]

class PPO(RLAlgorithm):
    def __init__(self, clip_ratio: float = 0.2):
        super().__init__("PPO")
        self.clip_ratio = clip_ratio

    def update(self, state: str, action: str, reward: float, next_state: str, next_action: Optional[str] = None) -> str:
        self.policy.setdefault(state, {})
        self.policy[state].setdefault(action, 1.0 / 3)
        old_prob = self.policy[state][action]
        new_prob = min(max(old_prob + reward * 0.1, old_prob * (1 - self.clip_ratio)), old_prob * (1 + self.clip_ratio))
        self.policy[state][action] = new_prob
        total = sum(self.policy[state].values())
        for a in self.policy[state]:
            self.policy[state][a] /= total
        return action

    def get_action(self, state: str) -> str:
        self.policy.setdefault(state, {})
        if not self.policy[state]:
            self.policy[state] = {"improve_modularity": 1/3, "add_features": 1/3, "fix_bugs": 1/3}
        actions, probs = zip(*self.policy[state].items())
        return np.random.choice(actions, p=probs)

class MetaAgent:
    def __init__(self, algorithms: List[RLAlgorithm]):
        self.algorithms = algorithms
        self.scores = {alg.name: [] for alg in algorithms}
        self.current_algo = algorithms[0]

    def select_algorithm(self) -> RLAlgorithm:
        if not any(self.scores.values()):
            return self.current_algo
        avg_scores = {name: np.mean(scores) if scores else 0 for name, scores in self.scores.items()}
        self.current_algo = max(avg_scores.items(), key=lambda x: x[1])[0]
        return next(alg for alg in self.algorithms if alg.name == self.current_algo)

    def update_score(self, algo_name: str, score: float):
        self.scores[algo_name].append(score)

class RLGeneratorAgent:
    def __init__(self, model: OpenRouter):
        self.model = model

    def generate_algorithm(self, existing_algorithms: List[str]) -> Dict:
        prompt = (
            f"You are an RL expert. Propose a new RL algorithm by combining or modifying existing ones ({', '.join(existing_algorithms)}).\n"
            f"Return a JSON object with: name (str), description (str), pseudo_code (str)."
        )
        headers = {
            "Authorization": f"Bearer {self.model.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "RL Algorithm Generator"
        }
        data = {
            "model": self.model.id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                f"{self.model.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
            return json.loads(content)
        except Exception as e:
            return {"name": "Error", "description": f"Generation failed: {str(e)}", "pseudo_code": ""}

class RLSimulation:
    def __init__(self, generator: Agent, evaluators: List[EvaluatorAgent], rl_generator: RLGeneratorAgent, config_file: str, max_iterations: int = 3):
        self.generator = generator
        self.evaluators = evaluators
        self.rl_generator = rl_generator
        self.max_iterations = max_iterations
        self.history = []
        self.config = self._load_config(config_file)
        self.algorithms = [
            QLearning(),
            SARSA(),
            PPO()
        ]
        self.meta_agent = MetaAgent(self.algorithms)
        self.state = "initial"

    def _load_config(self, config_file: str) -> Dict:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if config.get("rl_algorithm") == "dynamic":
                    config["rl_algorithm"] = None
                return config
        except Exception as e:
            raise Exception(f"Failed to load config: {str(e)}")

    def _run_tests(self) -> str:
        shell_tools = self.generator.tools.get("ShellTools")
        if not shell_tools:
            return "ShellTools not available"
        try:
            result = shell_tools.execute("pytest tests.py --tb=short")
            return result
        except Exception as e:
            return f"Test execution failed: {str(e)}"

    def run(self):
        project_type = self.config["project_type"]
        project_description = self.config["project_description"]
        prompt_template = self.config["prompt_template"]
        rl_algorithm = self.config.get("rl_algorithm")
        feedback = ""
        
        for iteration in range(self.max_iterations):
            print(f"\n--- Iteration {iteration + 1} ---")
            if rl_algorithm is None:
                algo = self.meta_agent.select_algorithm()
            else:
                algo = next((alg for alg in self.algorithms if alg.name == rl_algorithm), self.algorithms[0])
            print(f"Using RL Algorithm: {algo.name}")

            action = algo.get_action(self.state)
            prompt = prompt_template.format(
                project_type=project_type,
                project_description=project_description,
                feedback=feedback,
                action=action,
                library_file=self.config["library_file"],
                main_file=self.config["main_file"],
                test_file=self.config["test_file"]
            )
            start_time = time.time()
            try:
                code_output = self.generator.run(prompt, max_tokens=3000)
                print(f"Generated Code:\n{code_output}")
            except Exception as e:
                print(f"Generation failed: {str(e)}")
                break
            
            file_tools = self.generator.tools.get("FileTools")
            lib_code = file_tools.read(self.config["library_file"]) if file_tools else "File not found"
            main_code = file_tools.read(self.config["main_file"]) if file_tools else "File not found"
            test_code = file_tools.read(self.config["test_file"]) if file_tools else "File not found"
            combined_code = f"# {self.config['library_file']}\n{lib_code}\n\n# {self.config['main_file']}\n{main_code}\n\n# {self.config['test_file']}\n{test_code}"

            test_results = self._run_tests()
            print(f"Test Results:\n{test_results}")

            scores = []
            for i, evaluator in enumerate(self.evaluators):
                eval_result = evaluator.evaluate_code(combined_code, project_type, project_description, test_results)
                scores.append(eval_result.get("score", 0))
                print(f"Evaluator {i + 1} (Model: {evaluator.model.id}):")
                print(f"Score: {eval_result.get('score', 0)}")
                print(f"Functionality Feedback: {eval_result.get('functionality_feedback', 'N/A')}")
                print(f"Quality Feedback: {eval_result.get('quality_feedback', 'N/A')}\n")
            
            avg_score = sum(scores) / len(scores) if scores else 0
            self.meta_agent.update_score(algo.name, avg_score)
            
            next_state = f"score_{int(avg_score)}"
            next_action = algo.get_action(next_state)
            if algo.name == "SARSA":
                algo.update(self.state, action, avg_score / 100, next_state, next_action)
            else:
                algo.update(self.state, action, avg_score / 100, next_state)
            self.state = next_state

            feedback = "\n".join([
                f"Evaluator {i + 1}: {result.get('functionality_feedback', '')} {result.get('quality_feedback', '')}"
                for i, result in enumerate([evaluator.evaluate_code(combined_code, project_type, project_description, test_results) for evaluator in self.evaluators])
            ])
            self.history.append({
                "iteration": iteration + 1,
                "code": combined_code,
                "score": avg_score,
                "feedback": feedback,
                "rl_algorithm": algo.name
            })
            
            if iteration == 0 and random.random() < 0.3:
                new_algo = self.rl_generator.generate_algorithm([alg.name for alg in self.algorithms])
                print(f"Generated New RL Algorithm: {new_algo.get('name')}")
                self.history[-1]["new_algorithm"] = new_algo

            end_time = time.time()
            print(f"**Time Elapsed for Iteration {iteration + 1}:** {end_time - start_time:.2f} seconds")
            
            if avg_score >= 90:
                print("High score achieved, stopping early.")
                break

        try:
            with open("simulation_results.json", "w") as f:
                json.dump(self.history, f, indent=2)
            print("Results saved to simulation_results.json")
        except Exception as e:
            print(f"Failed to save results: {str(e)}")

# Config file for prompts
config_content = {
    "project_type": "Directory Site Generator",
    "project_description": "An AI-powered directory site that aggregates data from multiple sources (e.g., web scraping, APIs, or files) and displays it in a web interface",
    "prompt_template": (
        "You are a coding agent building a {project_type} application ({project_description}).\n"
        "1. Evaluate whether to use existing libraries (e.g., requests, beautifulsoup4, Flask) or implement custom logic for data scraping, API calls, and web serving. Justify your choice in comments.\n"
        "2. Create a reusable Python library with utility functions (e.g., for data scraping or API calls).\n"
        "3. Write a main script that uses this library to implement a basic feature (e.g., fetch and display directory data).\n"
        "4. Generate pytest tests to validate the library and main script functionality.\n"
        "5. Follow DRY and CoC principles, keeping code modular and concise.\n"
        "6. Focus on this action: {action}.\n"
        "7. Save the library to '{library_file}', the main script to '{main_file}', and tests to '{test_file}' using FileTools.\n"
        "Previous feedback (apply if provided):\n{feedback}\n\n"
        "Output format:\n"
        "[FileTools]save:```python\n# {library_file}\n<library_code>\n```:{library_file}[/FileTools]\n"
        "[FileTools]save:```python\n# {main_file}\n<main_code>\n```:{main_file}[/FileTools]\n"
        "[FileTools]save:```python\n# {test_file}\n<test_code>\n```:{test_file}[/FileTools]"
    ),
    "library_file": "data_utils.py",
    "main_file": "app.py",
    "test_file": "tests.py",
    "rl_algorithm": "dynamic"
}

# Save config file
with open("config.json", "w") as f:
    json.dump(config_content, f, indent=2)

# Usage
api_key = os.getenv("OPENROUTER_API_KEY", "your-api-key-here")
if api_key == "your-api-key-here":
    print("Please set your OPENROUTER_API_KEY environment variable.")
    exit(1)

generator_model = OpenRouter(
    id="google/gemini-2.0-flash-001",
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)
evaluator_models = [
    OpenRouter(
        id="google/gemini-pro-1.5",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    ),
    OpenRouter(
        id="anthropic/claude-3.5-sonnet",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
]
rl_generator_model = OpenRouter(
    id="google/gemini-pro-1.5",
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

generator_agent = Agent(
    model=generator_model,
    tools=[ShellTools(), FileTools()],
    show_tool_calls=True
)
evaluator_agents = [EvaluatorAgent(model) for model in evaluator_models]
rl_generator_agent = RLGeneratorAgent(rl_generator_model)

# Test RL algorithms
test_file_content = """
import pytest
from cua4_rl import QLearning, SARSA, PPO

def test_qlearning_update():
    algo = QLearning()
    state = "initial"
    action = "improve_modularity"
    reward = 0.8
    next_state = "score_80"
    algo.update(state, action, reward, next_state)
    assert algo.q_table[state][action] > 0

def test_sarsa_update():
    algo = SARSA()
    state = "initial"
    action = "add_features"
    reward = 0.7
    next_state = "score_70"
    next_action = "fix_bugs"
    algo.update(state, action, reward, next_state, next_action)
    assert algo.q_table[state][action] > 0

def test_ppo_update():
    algo = PPO()
    state = "initial"
    action = "fix_bugs"
    reward = 0.9
    next_state = "score_90"
    algo.update(state, action, reward, next_state)
    assert algo.policy[state][action] > 0.33
"""

with open("test_rl_algorithms.py", "w") as f:
    f.write(test_file_content)

shell_tools = ShellTools()
test_result = shell_tools.execute("pytest test_rl_algorithms.py --tb=short")
print(f"RL Algorithm Tests:\n{test_result}")

simulation = RLSimulation(
    generator=generator_agent,
    evaluators=evaluator_agents,
    rl_generator=rl_generator_agent,
    config_file="config.json",
    max_iterations=3
)
simulation.run()