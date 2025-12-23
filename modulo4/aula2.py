from agents import Agent, Runner, set_default_openai_api, function_tool, RunContextWrapper, SQLiteSession, MaxTurnsExceeded
from openai.types.responses import ResponseTextDeltaEvent
import os
from dotenv import load_dotenv
from dataclasses import dataclass
import asyncio
import subprocess
from subprocess import PIPE
import random

load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')
set_default_openai_api(api_key)

@function_tool
def get_numer():
    return random.randint(1, 5)

agent = Agent(
    name="Agente pessoal",
    model="gpt-4.1-mini",
    tools=[get_numer]
)

session = SQLiteSession(session_id="chat1", db_path="session.db")

async def main():

    user_input = "Chame a tool até que o número seja 4. A cada chamada, mostre o número que foi retornado"
    print("\n")
    
    try:
        result = Runner.run_streamed(starting_agent=agent, input=user_input, session=session, max_turns=10)
        
        print("Assistente: ", end="")
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)
                
    except MaxTurnsExceeded:
        print("Número máximo excedido")

if __name__ == "__main__":
    asyncio.run(main())