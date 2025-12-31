from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    function_tool,
    SQLiteSession,
    input_guardrail,
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
    InputGuardrailTripwireTriggered
)

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

from pydantic import BaseModel
from typing import Literal, List

from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')

set_default_openai_api(api_key)

class AnaliseInputGuardrail(BaseModel):
    e_matematica: bool
    raciocinio: str
    
detector_de_matematica = Agent(
    name='Detector de matemática',
    instructions=(
        'Você é um guardrail que analise se o texto contém matemática\n'
        'Verifique se o texto contém números, euqações, cálculos ou perguntas sobre "matemática"\n'
        'Responda sempre se o conteúdo é sobre matemática (e_matematica True ou False) e o motivo (raciocinio)'
    ),
    model='gpt-4.1-mini',
    output_type=AnaliseInputGuardrail
)

@input_guardrail
async def guardrail_matematica(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | List[TResponseInputItem]
) -> GuardrailFunctionOutput:
    
    result = await Runner.run(starting_agent=detector_de_matematica, input=input, context=ctx.context)
    
    analise_matematica: AnaliseInputGuardrail = result.final_output
    
    return GuardrailFunctionOutput(
        output_info=analise_matematica,
        tripwire_triggered=analise_matematica.e_matematica
    )
    
detector_de_historia = Agent(
    name='Professor de história',
    instructions=(
        'Você é um professor de história que ajuda com perguntas somente sobre história\n'
        'Se for sobre outro assunto, dica "não sei"\n'
        'Responda de forma amigável e útil sobre diversos tópicos históricos'
    ),
    model='gpt-4.1-mini',
    input_guardrails=[guardrail_matematica]
)

session = SQLiteSession(session_id='chat1', db_path='session.db')

async def main():
    last_agent = detector_de_historia

    while True:
        user_input = input('User\n> ')
        print('\n')

        try:
            result = Runner.run_streamed(starting_agent=last_agent, session=session, input=user_input)

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
            
        except InputGuardrailTripwireTriggered:
            print('Matemática detectada!')

asyncio.run(main())
