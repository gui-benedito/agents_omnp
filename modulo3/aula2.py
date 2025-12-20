from agents import Agent, Runner, set_default_openai_api, function_tool, RunContextWrapper, SQLiteSession
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List

load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')
set_default_openai_api(api_key)

@dataclass
class Compra:
    produto: str
    preco: float

@dataclass
class User:
    id: int
    nome: str
    compras: List[Compra]
    
    def get_recent_purchases(self, n: int):
        """
        Método para recuperar as recentes compras do usuário
        """
        
        return self.compras[-n:]

@function_tool
def get_user_purchases(wrapper: RunContextWrapper[User], n: int) -> str:
    """ 
    Função para recuperar comrpas do usuário
    """
    compras: List[Compra] = wrapper.context.get_recent_purchases(n)
    
    lista_de_compras = ', '.join([f"{p.produto} - R${p.preco:.2f}" for p in compras])
    return lista_de_compras

@function_tool
def get_user_context(wrapper: RunContextWrapper[User]) -> str:
    """
    Função para recuperar informações do usuário
    """
    return f"Id: {wrapper.context.id}, nome: {wrapper.context.nome}"
    
agent = Agent(
    name="Agente pessoal",
    instructions=(
        "Você é um agente pessoal que fornece informações de usuários e suas compras"
    ),
    model="gpt-4.1-mini",
    tools=[get_user_context, get_user_purchases]
)

session = SQLiteSession(session_id="chat_1", db_path="session.db")

user = User(
    1, 
    "Guilherme", 
    [
        Compra("Monitor", 500),
        Compra("Mouse", 250),
        Compra("Livro", 78)
    ]
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