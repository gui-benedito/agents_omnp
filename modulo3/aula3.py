from agents import Agent, Runner, set_default_openai_api, function_tool, RunContextWrapper, SQLiteSession
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List

load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')
set_default_openai_api(api_key)

@dataclass
class User:
    id: int
    name: str
    is_new_user: bool
    
def dynamic_user_instructions(wrapper: RunContextWrapper[User], agent: Agent[User]):
    """
    Função para buscar isntruções dinâmicas
    """
    
    is_new = wrapper.context.is_new_user
    
    if is_new:
        return(
            "Você é um assistente pessoal"
            f"O usuário {wrapper.context.name} é novo no sistema, responda sempre de maneira calma, detalhada e educada"
        )
    else:
        return(
            "Você é um assistente pessoal"
            f"O usuário {wrapper.context.name} é antigo no sistema, responda de maneira direta e sem enrolação"
        )
        
@function_tool
def get_user_context(wrapper: RunContextWrapper[User]) -> str:
    """
    Função para recuperar informações do usuário
    """
    return f"Id: {wrapper.context.id}, nome: {wrapper.context.nome}"
        
agent = Agent(
    name="Agente pessoal",
    instructions=dynamic_user_instructions,
    model="gpt-4.1-mini",
    tools=[get_user_context]
)

session = SQLiteSession(session_id="chat_1", db_path="session.db")

user = User(
    1, 
    "Guilherme", 
    False
)

while True:
    try:
        user_input = input("User: ")
        print("\n")
        
        result = Runner.run_sync(
            starting_agent=agent,
            input=user_input,
            session=session,
            context=user
        )
        
        print(f"Assistant: {result.final_output}")
        print("\n")
    except KeyboardInterrupt:
        break