from agents import Agent, Runner, set_default_openai_api, function_tool, RunContextWrapper, SQLiteSession
import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')
set_default_openai_api(api_key)

@dataclass
class UserInfo:
    nome: str
    cargo: str

@function_tool
def fetch_user_info(wrapper: RunContextWrapper[UserInfo]) -> str:
    """
    Função para buscar informações do usuário
    """
    return f"nome: {wrapper.context.nome}, cargo: {wrapper.context.cargo}"

@function_tool
def update_user_info(wrapper: RunContextWrapper[UserInfo], nome:str, cargo:str) -> str:
    """
    Função para atualizar informações do usuário
    """
    wrapper.context.nome = nome
    wrapper.context.cargo = cargo
    
    return "Informações atualizadas com sucesso!"

agente_de_suporte = Agent(
    name="Agente de suporte empresarial",
    instructions=(
        "Você é um agente de suporte ao funcionário, fornecendo informações"
    ),
    model="gpt-4.1-mini",
    tools=[fetch_user_info, update_user_info]
)

session = SQLiteSession(session_id="chat_1", db_path="session.db")

user = UserInfo(
    "Guilherme",
    "Desenvolvedor"
)

while True:
    try:
        user_input = input("User: ")
        print("\n")
        
        result = Runner.run_sync(
            starting_agent=agente_de_suporte,
            input=user_input,
            session=session,
            context=user
        )
        
        print(f"Assistant: {result.final_output}")
        print("\n")
    except KeyboardInterrupt:
        break