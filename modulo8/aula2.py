from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    SQLiteSession,
    ModelSettings
)

from agents.mcp import MCPServerStdio

from openai.types.responses import (
    ResponseTextDeltaEvent,
    ResponseTextDoneEvent,
    ResponseOutputItemAddedEvent,
    ResponseFunctionToolCall,
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseFunctionCallArgumentsDoneEvent,
    ResponseReasoningSummaryPartAddedEvent,
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseReasoningSummaryPartDoneEvent
)
import os

import asyncio

from openai.types.shared import Reasoning


from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')

set_default_openai_api(api_key)

class Colors:
    AGENT_TEXT = "\033[37m"
    AGENT_NAME = "\033[90m"
    AGENT_REASONING = "\033[90m"
    FUNCTION_CALL = "\033[33m"
    SHELL_OUTPUT = "\033[32m"
    CODE_BLOCK = "\033[90m"
    CODE_CONTENT = "\033[36m"
    WEB_SEARCH = "\033[34m"
    DIM = "\033[2m"
    RESET = "\033[0m"

async def main():
    session = SQLiteSession(session_id='chat1', db_path='session.db')

    server = MCPServerStdio(
        params={
            "command": "python",
            "args": ["Módulo 8/aula2_servidor_mcp.py"],
            "env": os.environ

        }
    )

    await server.connect()

    agent = Agent(
        name="Assistente Pessoal MCP",
        instructions="Você é um assistente pessoal equipado com um servidor MCP chamado 'Servidor MCP OM'",
        mcp_servers=[server],
        model='gpt-5-nano',
        model_settings=ModelSettings(
            reasoning=Reasoning(
                effort='high',
                summary='detailed'
            )
        )
    )

    last_agent = agent

    while True:
        user_input = input('User\n> ')
        print('\n')

        try:

            result = Runner.run_streamed(starting_agent=last_agent, session=session, input=user_input, max_turns=30)

            async for event in result.stream_events():

                match event.type:
                    case 'agent_updated_stream_event':
                        print(f'{Colors.AGENT_NAME}{event.new_agent.name}{Colors.RESET}')

                    case 'raw_response_event':
                        match event.data:

                            # Raciocinio
                            case ResponseReasoningSummaryPartAddedEvent():
                                print(f'{Colors.AGENT_REASONING}```thinking{Colors.RESET}')
                            case ResponseReasoningSummaryTextDeltaEvent():
                                print(f'{Colors.AGENT_REASONING}{event.data.delta}{Colors.RESET}', end='', flush=True)
                            case ResponseReasoningSummaryPartDoneEvent():
                                print(f'\n{Colors.AGENT_REASONING}```{Colors.RESET}\n')
                            
                            # Texto
                            case ResponseTextDeltaEvent():
                                print(f'{Colors.AGENT_TEXT}{event.data.delta}{Colors.RESET}', end='', flush=True)
                            case ResponseTextDoneEvent():
                                print('\n')

                            # Argumentos da função
                            case ResponseOutputItemAddedEvent() if isinstance(event.data.item, ResponseFunctionToolCall):
                                print(f'\033[32m{event.data.item.name} -> \033[0m', end='', flush=True)
                            case ResponseFunctionCallArgumentsDeltaEvent():
                                print(f'\033[32m{event.data.delta}\033[0m', end='', flush=True)
                            case ResponseFunctionCallArgumentsDoneEvent():
                                print('\n')

                    case 'run_item_stream_event':
                        match event.name:
                            case 'tool_output':
                                output = event.item.raw_item['output']
                                print(f'\033[32m{output}\033[0m\n')

            last_agent = result.last_agent
            await asyncio.sleep(2)

        except: 
            pass




asyncio.run(main())