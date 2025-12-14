from agents import Agent, Runner, set_default_openai_api, function_tool
import os
from dotenv import load_dotenv
import random

load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')
set_default_openai_api(api_key)

@function_tool
def get_weather(location: str) -> str:
    conditions = ['nublado', 'ensolarado', 'chuvoso']
    return f'{location} está {random.choice(conditions)}'

agente = Agent(
    name='Assistente de clima',
    instructions='Você é um assistente que ajuda informando as condições climáticas. Responda sempre em português e de maneira informal.',
    tools=[get_weather]
)

result = Runner.run_sync(
    starting_agent=agente,
    input='Como está o clima em São José dos Campos?'
)

print(result.final_output)