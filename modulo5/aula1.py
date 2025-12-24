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

exec_dir = os.path.dirname(os.path.abspath(__file__))

shell_process = subprocess.Popen(
    ["bash"],
    stdin=PIPE,
    stdout=PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    cwd=exec_dir
)

@function_tool
def local_shell(arg: str) -> str:
    """
    Gera comandos no terminal e mostra as saídas
    """
    sentinel = '__END_OF_COMMAND__'

    shell_process.stdin.write(arg + f'; echo {sentinel}\n')
    shell_process.stdin.flush()

    output = ''
    while True:
        line = shell_process.stdout.readline()

        if sentinel in line:
            break

        output += line

    return output.strip()[:2000]

assistente_pessoal = Agent(
    name='Assistente Pessoal',
    instructions=(
        "Responda de forma concisa.\n"
        "Nunca use tools simultanemente, sempre espere o output da tool anterior para rodar a próxima tool.\n"
        "Responda SEMPRE em português do Brasil de forma formal.\n"
        "Você pode usar a tool local_shell para executar comandos no terminal.\n"
        "Você deve ter autonomia para saber quando e como executar cada comando\n"
        "Por exemplo, se o usuario perguntar 'em que diretorio estamos?' você deve saber que o certo seria rodar um 'pwd'\n"
        "E se um usuário pergunta o que tem disponivel no diretorio, você deve saber que o certo seria rodar um 'ls', e etc..\n"
        "Caso seja necessário fazer qualquer conta matematica, utilize a tool do CodeInterpreterTool\n"
        "Caso precise encriptar algo, também utilize o CodeInterpreterTool\n"
        "Sempre que for pesquisar algo na internet, me dê um breve texto do que você vai pesquisar."
    ),
    model='gpt-4.1-mini',
    tools=[
        local_shell
    ]
)

session = SQLiteSession(session_id='chat1', db_path='session.db')

async def main():
    last_agent = assistente_pessoal

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


