from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    SQLiteSession,
)

from agents.mcp import MCPServerStdio

from openai.types.responses import (
    ResponseTextDeltaEvent,
    ResponseTextDoneEvent,
    ResponseOutputItemAddedEvent,
    ResponseFunctionToolCall,
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseFunctionCallArgumentsDoneEvent,
)
import os

import asyncio

from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')

set_default_openai_api(api_key)

async def main():
    
    session = SQLiteSession(session_id='chat1', db_path='session.db')

    mcp_server = MCPServerStdio(
        params={
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                os.getcwd()
            ],
            "env": {**os.environ}
        },
        name="Servidor MCP"
    )

    await mcp_server.connect()

    agent = Agent(
        name="Assistente MCP",
        instructions="Você é um assistente pessoal equipado com um servidor MCP chamado server-filesystem",
        model="gpt-5-nano",
        mcp_servers=[mcp_server]
    )

    last_agent = agent
    while True:
        user_input = input('User\n> ')
        print('\n')

        try:

            result = Runner.run_streamed(starting_agent=last_agent, session=session, input=user_input, max_turns=30)

            async for event in result.stream_events():
                # with open('events.txt', 'a') as f:
                #     f.write(f'{event}\n')

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

