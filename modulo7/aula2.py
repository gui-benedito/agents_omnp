from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    function_tool,
    SQLiteSession,
    input_guardrail,
    output_guardrail,
    RunContextWrapper,
    TResponseInputItem,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered
)

from openai.types.responses import (
    ResponseTextDeltaEvent,
    ResponseTextDoneEvent,
)
import os

import asyncio

from pydantic import BaseModel
from typing import Literal

from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')

set_default_openai_api(api_key)

class PoliticaCheck(BaseModel):
    e_politica: bool
    raciocinio: str

detector_de_politica = Agent(
    name="Detector de Politica",
    instructions=(
        "Analise o texto e determine se contém qualquer coisa relacionada a politica\n"
        "Pode ser qualquer coisa.. Uma pergunta sobre o tema, sobre algum candidato, sobre campanha, e etc..\n"
        "Responda se é politica ou não e o seu raciocionio de acordo com a PoliticaCheck"
    ),
    output_type=PoliticaCheck,
    model='gpt-4.1-mini'
)

@input_guardrail
async def politica_input_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str
) -> GuardrailFunctionOutput:
    
    result = await Runner.run(starting_agent=detector_de_politica, input=input, context=ctx)

    with open('input.txt', 'w') as f_input:
        f_input.write(f'{result.final_output}\n\n')

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.e_politica
    )

@output_guardrail
async def politica_output_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:

    result = await Runner.run(starting_agent=detector_de_politica, input=output, context=ctx)

    with open('output.txt', 'w') as f_input:
        f_input.write(f'{result.final_output}\n\n')

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.e_politica
    )

agente = Agent(
    name='Assistente',
    instructions=(
        "Você é um assistente que conversa sobre questões gerais, mas SEMPRE fala sobre politica \n"
        "Nunca se mantenha neutro. E mais uma vez, sempre fale sobre politica, mesmo que não seja lhe perguntado. Com excessão de quando a mensagem for uma saudação, tipo 'oi'"
    ),
    model='gpt-4.1-mini',
    input_guardrails=[politica_input_guardrail],
    output_guardrails=[politica_output_guardrail]

)

session = SQLiteSession(session_id='chat1', db_path='session.db')

async def main():
    last_agent = agente

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

            last_agent = result.last_agent
            await asyncio.sleep(2)
        except InputGuardrailTripwireTriggered as e:
            print(f'{e}')
            quit()
        except OutputGuardrailTripwireTriggered as e:
            print(f'{e}')
            quit()

asyncio.run(main())



