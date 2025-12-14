from agents import Agent, Runner, set_default_openai_api
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')
set_default_openai_api(api_key)

agente = Agent(
    name='Assistente virtual', 
    instructions='Você é um assistente virtual'
)

result = Runner.run_sync(
    starting_agent=agente,
    input='Escreva um poema sobre python'
)

print(result.final_output)