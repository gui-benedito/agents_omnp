from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    function_tool,
    SQLiteSession,
)
import os
import asyncio
import subprocess
from subprocess import PIPE
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')

set_default_openai_api(api_key)

class Pessoa(BaseModel):
    nome: str
    idade: int
    email: str
    
agent = Agent(
    name='Assistente pessoal',
    instructions='Você é um assistente pessoal que responde sempre na estrutura da classe Pessoa',
    model='gpt-4.1-mini',
    output_type=Pessoa
)

def main():
    user_input = input('Usuário: ')
    
    result = Runner.run_sync(
        starting_agent=agent,
        input=user_input
    )
    
    print(result.final_output)
    
main()