WIKIFIER_TEMPLATE = """
You are a Wikipedia editor, and your task is to take a user's prompt and response from an AI assistant and convert it into a Wikipedia article. Do not include any new information when writing the article.

Examples:

User: What is the capital of France?
AI: Paris
Response:
# Capital of France
The user asked the AI assistant for the capital of France, and the assistant responded with the answer: Paris.

User: What is the strongest Pokemon?
AI: As of my last knowledge update in January 2022, Arceus is often considered one of the strongest Pokémon in the Pokémon franchise. Arceus is a Legendary Pokémon known as the "God of Pokémon" and is said to have created the Pokémon universe. Its base stats are generally higher than most other Pokémon.

However, it's important to note that the Pokémon franchise is continually evolving, with new games and generations introducing more powerful Pokémon. Additionally, the concept of the "strongest" Pokémon can vary depending on factors such as individual stats, movesets, and type matchups.

If there have been new Pokémon games or updates since my last knowledge update in January 2022, I recommend checking the latest official Pokémon sources for the most up-to-date information on the strongest Pokémon.
Response:
# The Strongest Pokémon

## Introduction
As of the last knowledge update in January 2022, Arceus stands out as one of the most formidable Pokémon in the expansive Pokémon franchise. This Legendary Pokémon holds the prestigious title of the "God of Pokémon" and is recognized for its pivotal role in the creation of the Pokémon universe.

## Legendary Status
Arceus's legendary status is attributed to its extraordinary abilities and significance within the Pokémon lore. Revered as the "God of Pokémon," it is widely acknowledged for its unparalleled power and influence.

## Base Stats and Superiority
Arceus's base stats surpass those of many other Pokémon, solidifying its reputation as a powerhouse within the Pokémon world. These impressive stats contribute to its standing as one of the strongest Pokémon in the franchise.

## Dynamic Pokémon Franchise
It is crucial to acknowledge the dynamic nature of the Pokémon franchise. Ongoing releases of new games and generations continuously introduce additional powerful Pokémon, altering the landscape of strength and capabilities.

## Factors Influencing Strength
The determination of the "strongest" Pokémon is a nuanced process, considering factors such as individual stats, movesets, and type matchups. The interplay of these elements contributes to the varying assessments of Pokémon strength.

## Staying Informed
For the latest and most accurate information on the strongest Pokémon, especially considering potential new Pokémon games or updates since January 2022, it is highly recommended to consult the latest official Pokémon sources. Staying informed ensures an up-to-date understanding of the evolving hierarchy of Pokémon strength.

User: {prompt}
AI: {response}
Response:
"""

from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI

class WikifierAgent:

    def __init__(self):
        self.template = WIKIFIER_TEMPLATE
        self.llm = ChatOpenAI(temperature=0.4, model_name="gpt-3.5-turbo-16k")
        self.prompt_template = PromptTemplate(
            input_variables=["prompt", "response"],
            template=WIKIFIER_TEMPLATE,
        )
    
    def wikify(self, prompt, response):
        prompt = self.prompt_template.format(
            prompt=prompt, response=response
        )
        res = self.llm.call_as_llm(prompt)
        return res
    
if __name__ == "__main__":
    wikifier_agent = WikifierAgent()
    prompt = "What is the capital of France?"
    response = "Paris"
    res = wikifier_agent.wikify(prompt, response)
    print(res)