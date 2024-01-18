OPENSCAD_TEMPLATE = """
You are an OpenSCAD programmer. Your task is to take the user's prompt and code the response in a single OpenSCAD script in markdown format.
Do NOT assume any local files exist such as images or other files.

Examples:

User: openscad for a simple sphere.
Response:
```openscad
$fn = 100; // Set the resolution for the sphere

// Create a sphere
sphere(r = 20); // Adjust the radius as needed

User: <!prompt>
```


User: <!prompt>
Response:
"""

from langchain.chat_models import ChatOpenAI
from langchain.llms import HuggingFaceHub
import os


class OpenSCADAgent:
    def __init__(self):
        self.template = OPENSCAD_TEMPLATE
        self.llm_provider = os.environ["LLM"]
        if self.llm_provider == "huggingface":
            # repo_id = "google/flan-t5-xxl"
            repo_id = os.getenv("LLM_REPO_ID", "mistralai/Mixtral-8x7B-Instruct-v0.1")
            self.llm = HuggingFaceHub(
                repo_id=repo_id, model_kwargs={"temperature": 0.2, "max_length": 3000}
            )
        else:  # default to openai
            self.llm = ChatOpenAI(temperature=0.4, model_name="gpt-3.5-turbo-16k")

    def get_prompt_template(self, prompt):
        template = OPENSCAD_TEMPLATE
        template = template.replace("<!prompt>", prompt)
        return template

    def prompt(self, prompt):
        prompt = self.get_prompt_template(prompt=prompt)
        res = self.llm.predict(prompt)
        return res


if __name__ == "__main__":
    programmer_agent = OpenSCADAgent()
    res = programmer_agent.prompt(
        "Can you make me a computer mouse ergonomically CORRECT."
    )
    print(res)
