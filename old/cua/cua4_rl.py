import os
import subprocess
import requests
import time
import json
from typing import Any, Dict, List, Optional
import uuid
import random
import numpy as np
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
    def save(self, content: str, filename: str, output_dir: str) -> str:
        try:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            return f"Saved to {filepath}"
        except Exception as e:
            return f"Error saving file: {str(e)}"

    def read(self, filename: str, output_dir: str) -> str:
        try:
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

class Agent:
    def __init__(self, model: OpenRouter, tools: List[Any], show_tool_calls: bool = False):
        self.model = model
        self.tools = {tool.__class__.__name__: tool for tool in tools}
        self.show_tool_calls = show_tool_calls
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

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
            response = self.session.post(
                f"{self.model.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=20
            )
            print(f"Model: {self.model.id}, Status: {response.status_code}, Response: {response.text[:200]}...")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            error_msg = f"API call failed for model {self.model.id}: {str(e)}"
            if 'response' in locals():
                error_msg += f"\nStatus Code: {response.status_code}\nResponse Text: {response.text}"
            raise Exception(error_msg)

    def _execute_tools(self, content: str, output_dir: str) -> str:
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
                    match = re.match(r"^(save|read):(.+?):(.+)$", cmd, re.DOTALL)
                    if match:
                        op, content_or_file, filename = match.groups()
                        if op == "save":
                            cleaned_content = re.sub(r'```python\n|```', '', content_or_file).strip()
                            result = tool.save(cleaned_content, filename.strip(), output_dir)
                        elif op == "read":
                            result = tool.read(content_or_file.strip(), output_dir)
                    else:
                        result = f"Invalid FileTools command: {cmd}"
                else:
                    result = "Unknown tool"
                if self.show_tool_calls:
                    return f"**Tool Call:** {tool_name}.execute('{cmd}')\n**Result:**\n```\n{result}\n```"
                return result
        return content

    def run(self, prompt: str, max_tokens: int = 2000, output_dir: str = ".") -> str:
        api_response = self._call_api(prompt, max_tokens)
        content = api_response.get("choices", [{}])[0].get("message", {}).get("content", prompt)
        return self._execute_tools(content, output_dir)

class EvaluatorAgent:
    def __init__(self, model: OpenRouter):
        self.model = model
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

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
            response = self.session.post(
                f"{self.model.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=20
            )
            response.raise_for_status()
            content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}, Raw response: {content}")
                return {"score": 0, "functionality_feedback": f"Invalid JSON response: {content}", "quality_feedback": ""}
        except requests.RequestException as e:
            print(f"API call failed: {str(e)}, Response: {response.text if 'response' in locals() else 'N/A'}")
            return {"score": 0, "functionality_feedback": f"Evaluation failed: {str(e)}", "quality_feedback": ""}

class RLAlgorithm:
    def __init__(self, name: str):
        self.name = name
        self.q_table = {}
        self.policy = {}

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
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

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
            response = self.session.post(
                f"{self.model.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=20
            )
            response.raise_for_status()
            content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON decode error in RLGenerator: {e}, Raw response: {content}")
                return {"name": "Error", "description": f"Invalid JSON response: {content}", "pseudo_code": ""}
        except requests.RequestException as e:
            print(f"API call failed in RLGenerator: {str(e)}, Response: {response.text if 'response' in locals() else 'N/A'}")
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
        self.output_dir = self._create_output_dir()

    def _create_output_dir(self) -> str:
        n = 1
        while os.path.exists(f"output_{n}"):
            n += 1
        output_dir = f"output_{n}"
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

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
            shell_tools.execute("pytest --version")
        except Exception:
            return "Pytest not installed. Please run 'pip install pytest'."
        try:
            test_file = os.path.join(self.output_dir, "tests.py")
            result = shell_tools.execute(f"pytest {test_file} --tb=short")
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
            print(f"\n--- Iteration {iteration + 1} (Output: {self.output_dir}) ---")
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
                code_output = self.generator.run(prompt, max_tokens=3000, output_dir=self.output_dir)
                print(f"Tool Results:\n{code_output}")
            except Exception as e:
                print(f"Generation failed: {str(e)}")
                self.history.append({
                    "iteration": iteration + 1,
                    "code": "Generation failed",
                    "score": 0,
                    "feedback": f"Generation error: {str(e)}",
                    "rl_algorithm": algo.name
                })
                break
            
            file_tools = self.generator.tools.get("FileTools")
            lib_code = file_tools.read(self.config["library_file"], self.output_dir) if file_tools else "File not found"
            main_code = file_tools.read(self.config["main_file"], self.output_dir) if file_tools else "File not found"
            test_code = file_tools.read(self.config["test_file"], self.output_dir) if file_tools else "File not found"
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
                "code": f"Files saved to {self.output_dir}",
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
            with open(os.path.join(self.output_dir, "simulation_results.json"), "w") as f:
                json.dump(self.history, f, indent=2)
            print(f"Results saved to {self.output_dir}/simulation_results.json")
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
        "Output format (use exact syntax, no extra backticks):\n"
        "[FileTools]save:[library_code]:{library_file}[/FileTools]\n"
        "[FileTools]save:[main_code]:{main_file}[/FileTools]\n"
        "[FileTools]save:[test_code]:{test_file}[/FileTools]"
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
        id="google/gemini-2.0-flash-001",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    ),
    # OpenRouter(
    #     id="anthropic/claude-3.5-sonnet",
    #     api_key=api_key,
    #     base_url="https://openrouter.ai/api/v1"
    # )
]
rl_generator_model = OpenRouter(
    id="google/gemini-2.0-flash-001",
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

# Test FileTools
test_file_content = """
import pytest
import os
from cua4_rl import FileTools

def test_filetools_save():
    ft = FileTools()
    content = "def hello():\\n    return 'world'"
    filename = "test_file.py"
    output_dir = "test_output"
    result = ft.save(content, filename, output_dir)
    assert result == f"Saved to {output_dir}/{filename}"
    with open(os.path.join(output_dir, filename), 'r') as f:
        assert f.read() == content
    os.remove(os.path.join(output_dir, filename))
    os.rmdir(output_dir)

def test_filetools_read():
    ft = FileTools()
    content = "test content"
    filename = "test_read.txt"
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), 'w') as f:
        f.write(content)
    result = ft.read(filename, output_dir)
    assert result == content
    os.remove(os.path.join(output_dir, filename))
    os.rmdir(output_dir)
"""

with open("test_filetools.py", "w") as f:
    f.write(test_file_content)

shell_tools = ShellTools()
try:
    test_result = shell_tools.execute("pytest test_filetools.py --tb=short")
    print(f"FileTools Tests:\n{test_result}")
except Exception:
    print("Pytest not installed for FileTools tests. Please run 'pip install pytest'.")

simulation = RLSimulation(
    generator=generator_agent,
    evaluators=evaluator_agents,
    rl_generator=rl_generator_agent,
    config_file="config.json",
    max_iterations=3
)
simulation.run()