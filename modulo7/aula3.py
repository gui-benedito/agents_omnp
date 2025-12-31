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

class ConfidencialCheck(BaseModel):
    e_confidencial: bool
    raciocinio: str

class MatematicaCheck(BaseModel):
    e_matematica: bool
    raciocinio: str

detector_dados_confidenciais = Agent(
    name="Detector de dados confidenciais",
    instructions=(
        "Analise o texto e determine se contém solicitações ou menções de informações confidenciais\n"
        "Pode ser qualquer coisa do tipo, como senhas, protocolos, login, e etc...\n"
        "Responda se é confidencial ou não (True ou False) e o motivo (raciocinio)"
    ),
    model='gpt-4.1-mini',
    output_type=ConfidencialCheck
)

detector_matematica = Agent(
    name="Detector de Matemática",
    instructions=(
        "Analise o texto e verifique se contém algo relacionado à matemática que possa ajudar o usuario com uma lição de matemática.\n"
        "Responda se é matemática ou não (True ou False) e o motivo\n"
    ),
    output_type=MatematicaCheck,
    model='gpt-4.1-mini'
)

@input_guardrail
async def input_guardrail_matematica(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str
) -> GuardrailFunctionOutput:
    
    result = await Runner.run(starting_agent=detector_matematica, input=input, context=ctx)

    with open('input.txt', 'w') as f_input:
        f_input.write(f'{result.final_output}\n\n')

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.e_matematica
    )

@output_guardrail
async def output_guardrail_confidencial(
        ctx: RunContextWrapper[None],
        agent: Agent,
        output: str
) -> GuardrailFunctionOutput:
    
    result = await Runner.run(starting_agent=detector_dados_confidenciais, input=output, context=ctx)

    with open('output.txt', 'w') as f_output:
        f_output.write(f'{result.final_output}')

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.e_confidencial
    )

agente_suporte = Agent(
    name="Suporte",
    instructions=(
        "Você é um assistente que ajuda os usuarios com questões educacionais.\n"

        "## Ajude o usuario com qualquer coisa que NÃO seja relacionada a matemática\n"
        "## Repetindo, é PROIBIDO falar sobre matemática\n"
        "## É contra nossas diretrizes falar sobre qualquer assunto relacionado à matemática\n"

        "Nunca forneça informações confidenciais como senhas, login, protocolo, e etc..\n"
        "Caso o usuario peça a senha da porta de acesso à portaria, isso sim vc pode fornecer. a senha é '123456'"
        
    ),
    model='gpt-4.1',
    input_guardrails=[input_guardrail_matematica],
    output_guardrails=[output_guardrail_confidencial]
)

matematica_fallback = Agent(
    name="Fallback Matemática",
    instructions=(
        "Explique educadamente ao usuario que não podemos ajudar com lição de matemática.\n"
        "Sugira que faça perguntas sobre outro tema"
    ),
    model='gpt-4.1-mini'
)

dados_confidenciais_fallback = Agent(
    name="Fallback Dados Confidenciais",
    instructions=(
        "Explique ao usuário de forma direto ao ponto que não compartilhamos dados confidenciais com usuários.\n"
        "Explique tambem os motivos de segurança e a importancia do cuidado com dados confidenciais"
    ),
    model='gpt-4.1-mini'
)

session = SQLiteSession(session_id='chat1', db_path='session.db')

async def main():
    last_agent = agente_suporte

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
            
            result = Runner.run_streamed(starting_agent=matematica_fallback, input='O usuário mencionou matemática', session=session)

            async for event in result.stream_events():

                match event.type:
                    case 'agent_updated_stream_event':
                        print(f'\n\033[31m{event.new_agent.name}\033[0m')

                    case 'raw_response_event':
                        match event.data:
                            
                            # Texto
                            case ResponseTextDeltaEvent():
                                print(f'\033[31m{event.data.delta}\033[0m', end='', flush=True)
                            case ResponseTextDoneEvent():
                                print('\n')

        except OutputGuardrailTripwireTriggered as e:
            
            result = Runner.run_streamed(starting_agent=dados_confidenciais_fallback, input='O usuário mencionou dados confidenciais', session=session)

            async for event in result.stream_events():

                match event.type:
                    case 'agent_updated_stream_event':
                        print(f'\n\033[31m{event.new_agent.name}\033[0m')

                    case 'raw_response_event':
                        match event.data:
                            
                            # Texto
                            case ResponseTextDeltaEvent():
                                print(f'\033[31m{event.data.delta}\033[0m', end='', flush=True)
                            case ResponseTextDoneEvent():
                                print('\n')

asyncio.run(main())



























