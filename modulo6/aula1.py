from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    function_tool,
    SQLiteSession,
)

from openai.types.responses import (
    ResponseTextDeltaEvent,
    ResponseTextDoneEvent,
    ResponseOutputItemAddedEvent,
    ResponseFunctionToolCall,
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseFunctionCallArgumentsDoneEvent,
    ResponseCodeInterpreterCallInProgressEvent,
    ResponseCodeInterpreterCallCodeDeltaEvent,
    ResponseCodeInterpreterCallCodeDoneEvent,
    ResponseWebSearchCallInProgressEvent,
    ResponseOutputItemDoneEvent,
    ResponseFunctionWebSearch
)
import os

import asyncio

import subprocess
from subprocess import PIPE

from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')

set_default_openai_api(api_key)

professor_de_geografia = Agent(
    name='Professor de geografia',
    instructions=(
        "Você é um professor de geografia\n"
        "Só responda sobre assunto de geografia, se a pergunta não for de geografia, transfira para um especialista se houver ou responda 'não sei'\n"
    ),
    model='gpt-4.1-mini'
)

professor_de_matematica = Agent(
    name='Professor de matemática',
    instructions=(
        "Você é um professor de matemática\n"
        "Só responda sobre assunto de matemática, se a pergunta não for de matemática, transfira para um especialista se houver ou responda 'não sei'\n"
    ),
    model='gpt-4.1-mini'
)

orquestrador = Agent(
    name='Assistente Pessoal',
    instructions=(
        "Você é um orquestrador\n"
        "Você não responde diretamente ao usuário, sempre pergunte a um agente especialista no assunto\n"
    ),
    model='gpt-4.1-mini'
)

orquestrador.handoffs=[professor_de_geografia, professor_de_matematica]
professor_de_matematica.handoffs=[professor_de_geografia, orquestrador]
professor_de_geografia.handoffs=[orquestrador, professor_de_matematica]

session = SQLiteSession(session_id='chat1', db_path='session.db')

async def main():
    last_agent = orquestrador

    while True:
        user_input = input('User\n> ')
        print('\n')

        result = Runner.run_streamed(starting_agent=last_agent, session=session, input=user_input)

        async for event in result.stream_events():
            with open('events.txt', 'a') as f:
                f.write(f'{event}\n')

            match event.type:
                case 'agent_updated_stream_event':
                    print(f'\033[33m{event.new_agent.name}\033[0m')

                case 'raw_response_event':
                    match event.data:
                        
                        # Texto
                        case ResponseTextDeltaEvent():
                            print(f'\033[33m{event.data.delta}\033[0m', end='', flush=True)
                        case ResponseTextDoneEvent():
                            print('\n')

                        # Argumentos da função
                        case ResponseOutputItemAddedEvent() if isinstance(event.data.item, ResponseFunctionToolCall):
                            print(f'\033[32m{event.data.item.name} -> \033[0m', end='', flush=True)
                        case ResponseFunctionCallArgumentsDeltaEvent():
                            print(f'\033[32m{event.data.delta}\033[0m', end='', flush=True)
                        case ResponseFunctionCallArgumentsDoneEvent():
                            print('\n')

                        # Código do code interpreter
                        case ResponseCodeInterpreterCallInProgressEvent():
                            print(f'\033[31m```python\033[0m')
                        case ResponseCodeInterpreterCallCodeDeltaEvent():
                            print(f'\033[31m{event.data.delta}\033[0m', end='', flush=True)
                        case ResponseCodeInterpreterCallCodeDoneEvent():
                            print(f'\033[31m```\033[0m')
                            print('\n')

                        # Pesquisa na web
                        case ResponseWebSearchCallInProgressEvent():
                            print('\n\033[34mBuscando informações na internet\033[0m', end='', flush=True)
                        case ResponseOutputItemDoneEvent() if isinstance(event.data.item, ResponseFunctionWebSearch):
                            print(f'\033[34m -> "{event.data.item.action.query}\033[0m"\n', end='', flush=True)
                    
                case 'run_item_stream_event':
                    match event.name:
                        case 'tool_output':
                            output = event.item.raw_item['output']
                            print(f'\033[32m{output}\033[0m\n')


        last_agent = result.last_agent

asyncio.run(main())


