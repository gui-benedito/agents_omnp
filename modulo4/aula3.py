from agents import Agent, Runner, set_default_openai_api, function_tool, SQLiteSession
from openai.types.responses import ResponseTextDeltaEvent
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
    ),
    model='gpt-4.1-mini',
    tools=[local_shell]
)

session = SQLiteSession(session_id='chat1', db_path='session.db')

async def main():
    
    last_agent = assistente_pessoal

    while True:

        user_input = input('User\n> ')
        print('\n')

        result = Runner.run_streamed(starting_agent=last_agent, session=session, input=user_input)

        async for event in result.stream_events():
            if event.type == 'raw_response_event' and isinstance(event.data, ResponseTextDeltaEvent):
                    print(f'\033[33m{event.data.delta}\033[0m', end='', flush=True)

            if event.type == 'agent_updated_stream_event':
                print(f'\033[33m{event.new_agent.name}\033[0m')

            if event.type == 'run_item_stream_event':
                match event.name:
                    case 'tool_called':
                        tool_call = event.item.raw_item
                        print(f'\n\033[32m{tool_call.name} -> {tool_call.arguments}\033[0m')
                    
                    case 'tool_output':
                        raw_tem = event.item.raw_item
                        output = raw_tem["output"]
                        print(f'\033[32m{output}\033[0m\n')

                    case 'handoff_request':
                        pass

                    case 'handoff_ocurred':
                        pass


        print('\n')

        last_agent = result.last_agent

asyncio.run(main())


