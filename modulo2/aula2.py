from agents import Agent, Runner, set_default_openai_api, function_tool
import os
from dotenv import load_dotenv
import subprocess
from subprocess import PIPE
import requests

load_dotenv()

key_api = os.environ.get('OPENAI_API_KEY')
set_default_openai_api(key_api)

weather_api_ley = os.environ.get('GET_WEATHER_KEY')

@function_tool
def get_weather(location: str) -> str:
    url = 'http://api.weatherapi.com/v1/current.json'
    
    params = {
        "key": weather_api_ley,
        "q": location,
        "lang": "pt"
    }
    
    try:
        response = requests.get(url=url, params=params)
        response.raise_for_status()
        
        data = response.json()
        temp = data['current']['temp_c']
        condition = data['current']['condition']['text']
        
        return f'{location} - temperatura em celsius: {temp}, condição: {condition}'
    except:
        f'Erro ao pesquisar clima.'
        
@function_tool
def terminal_command(arg: str):
    return subprocess.run(arg, shell=True, stdin=PIPE, stdout=PIPE)

agente = Agent(
    name="Assistente pessoal",
    model="gpt-4.1-mini",
    tools=[get_weather, terminal_command]
)

messages = [
    {"role": "system", "content": "Você é um assistente pessoal, que utiliza sistema windows. Responda sempre em portugês e de maniera formal."} 
]

while True:
    user_input = input("User: ")
    print("\n")
    
    messages.append({"role": "user", "content": user_input})
    
    result = Runner.run_sync(
        starting_agent=agente,
        input=messages
    )
    print(f"Assistant: {result.final_output}")
    print("\n")
    
    messages.append({"role": "assistant", "content": result.final_output})
    