from agents import Agent, Runner, set_default_openai_api, function_tool
import requests
import os
from dotenv import load_dotenv

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

agente_clima = Agent(
    name='Assistente climático',
    instructions='Você é um assistente que fornece informações sobre o tempo em uma determinado localização. Responda sempre em português e de maneira formal.',
    tools=[get_weather]
)

result = Runner.run_sync(
    starting_agent=agente_clima,
    input="Como está o clima em Sao Jose dos Campos?"
)

print(result.final_output)