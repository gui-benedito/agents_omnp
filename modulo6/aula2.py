from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    SQLiteSession,
    handoff
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

from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')

set_default_openai_api(api_key)

suporte_tecnico = Agent(
    name="Agente de Suporte Tecnico",
    instructions=(
        "Você é um agente especialista em suporte tecnico da empresa. Seu papel é resolver problemas tecnicos, como bugs, duvidas sobre a documentação, e etc...\n"
        "Se a questao não for do seu escopo, faça um handoff para o agente de triagem para que ele possa redirecionar a conversa para o agente correto.\n"
        "Antes de fazer handoff para o agente de triagem, escreva uma mensagem de contexto para explicar a ele o problema que o usuario esta tendo. essa mensagem de contexto deve ser algo como *Contexto: <contexto_da_questao>*\n"
        "A mensagem de contexto deve obrigatóriamente ter as tags, como estar dentro de ** e dentro de <>. Do contrário o usuario verá esta mensagem que é apenas interna"
    ),
    model='gpt-4.1-mini'
)

suporte_cliente = Agent(
    name="Agente de Suporte ao Cliente",
    instructions=(
        "Você é um agente especialista em suporte ao cliente da empresa. Seu papel é ajudar o usuário com problemas gerais da plataforma.\n"
        "Se a questao nao for do seu escopo, faça um handoff para o agente de triagem para que ele possa redirecionar a conversa para o agente correto\n"
        "Antes de fazer handoff para o agente de triagem, escreva uma mensagem de contexto para explicar a ele o problema que o usuario esta tendo. essa mensagem de contexto deve ser algo como *Contexto: <contexto_da_questao>*\n"
        "A mensagem de contexto deve obrigatóriamente ter as tags, como estar dentro de ** e dentro de <>. Do contrário o usuario verá esta mensagem que é apenas interna"
    ),
    model='gpt-4.1-mini'
)

suporte_cobrancas = Agent(
    name="Agente de Cobrancas",
    instructions=(
        "Você é um agente especialista em questoes financeiras e de cobrancas de usuarios da empresa.\n"
        "Ajude o usuario com faturas, pagamentos, reembolsos, alteracao de planos e coisas do tipo\n"
        "Se a questao nao for do seu escopo, faça um handoff para o agente de triagem para que ele possa redirecionar a conversa para o agente correto\n"
        "Antes de fazer handoff para o agente de triagem, escreva uma mensagem de contexto para explicar a ele o problema que o usuario esta tendo. essa mensagem de contexto deve ser algo como *Contexto: <contexto_da_questao>*\n"
        "A mensagem de contexto deve obrigatóriamente ter as tags, como estar dentro de ** e dentro de <>. Do contrário o usuario verá esta mensagem que é apenas interna"
    ),
    model='gpt-4.1-mini'
)

agente_de_triagem = Agent(
    name="Agente de Triagem",
    instructions=(
        "Você é um agente de triagem. Sua tarefa é transferir o comando da interacao para um agente especializado\n"
        "Analise cuidadosamente a soliciatação do cliente e o contexto passado pelo agente, caso tenha\n"
        "Escolha sempre o agente IDEAL para cada tipo de problema.\n"
        "Nunca rode tools simultaneamente. Sempre espere o output de uma tool anterior para rodar a próxima tool\n"
    ),
    model='gpt-4.1-mini',
    handoffs=[
        handoff(
            agent=suporte_tecnico,
            tool_description_override="Transfere para o suporte tecnico. Use ele para: Problemas tecnicos, bugs, erros e ajuda com a documentação",
            tool_name_override="chamar_suporte_tecnico"
        ),
        handoff(
            agent=suporte_cliente,
            tool_description_override="Transfere para o agente de suporte ao cliente. use para duvidas gerais, informações, politicas da empresa, prazos, planos e etc..",
            tool_name_override="chamar_suporte_cliente"
        ),
        handoff(
            agent=suporte_cobrancas,
            tool_description_override="Transfere para o suporte de cobrancas. use para problemas com faturas, pagamentos, cobrancas, reembolsos e coisas do tipo",
            tool_name_override="chamar_suporte_cobrancas"
        )
    ]
)

suporte_tecnico.handoffs = [agente_de_triagem]
suporte_cliente.handoffs = [agente_de_triagem]
suporte_cobrancas.handoffs = [agente_de_triagem]

session = SQLiteSession(session_id='chat1', db_path='session.db')

async def main():
    last_agent = agente_de_triagem

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
                    
                case 'run_item_stream_event':
                    match event.name:
                        case 'tool_output':
                            output = event.item.raw_item['output']
                            print(f'\033[32m{output}\033[0m\n')

        last_agent = result.last_agent

asyncio.run(main())
