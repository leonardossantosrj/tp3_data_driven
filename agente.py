
import os
from datetime import date

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from ferramentas import calcular_pace, previsao_do_tempo

load_dotenv()  # lê a chave GOOGLE_API_KEY do arquivo .env

MODELO = "gemini-3.8-flash"
FERRAMENTAS = [previsao_do_tempo, calcular_pace]
DIAS_DA_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]

# Prompt no formato ReAct: o agente alterna entre Thought (raciocinar),
# Action (usar uma ferramenta) e Observation (ler o resultado) até chegar à resposta.
# As palavras-chave ficam em inglês porque é o que o LangChain procura no texto do modelo.
MODELO_PROMPT = """Você é um assistente de treino de corrida para corredores amadores no Brasil.
Ajude a planejar treinos e provas: melhor horário pelo clima, pace e tempo de prova.
Responda sempre em português, de forma curta e prática.
Para contas de pace e tempo, use sempre a ferramenta calcular_pace, nunca faça as contas de cabeça.
Hoje é {data_hoje}. Use essa data para converter "amanhã", "sábado" etc. em AAAA-MM-DD.

Você tem acesso às seguintes ferramentas:

{tools}

Use exatamente este formato:

Question: a pergunta do usuário
Thought: pense no que fazer
Action: a ferramenta a usar, uma de [{tool_names}]
Action Input: a entrada da ferramenta
Observation: o resultado da ferramenta
... (Thought/Action/Action Input/Observation podem se repetir)
Thought: agora sei a resposta final
Final Answer: a resposta final para o usuário

Se a pergunta não precisar de ferramenta, vá direto para Final Answer.

Histórico da conversa:
{chat_history}

Question: {input}
Thought:{agent_scratchpad}"""


def criar_agente():
    """Monta o agente com memória. Dá erro claro se a chave do Gemini não estiver configurada."""
    chave = os.getenv("GOOGLE_API_KEY")
    if not chave:
        raise ValueError(
            "Chave do Gemini não encontrada. Crie o arquivo .env com GOOGLE_API_KEY=sua-chave "
            "(veja o .env.example)."
        )

    llm = ChatGoogleGenerativeAI(model=MODELO, api_key=chave)

    hoje = date.today()
    prompt = PromptTemplate.from_template(MODELO_PROMPT).partial(
        data_hoje=f"{DIAS_DA_SEMANA[hoje.weekday()]}, {hoje.isoformat()}"
    )
    agente = create_react_agent(llm, FERRAMENTAS, prompt)

    # Memória conversacional: guarda perguntas e respostas e as coloca em {chat_history}
    memoria = ConversationBufferMemory(memory_key="chat_history", input_key="input", output_key="output")

    return AgentExecutor(
        agent=agente,
        tools=FERRAMENTAS,
        memory=memoria,
        verbose=True,  # mostra o Thought/Action/Observation no terminal
        handle_parsing_errors=True,  # se o modelo sair do formato, pede para ele corrigir
        max_iterations=6,  # evita que o agente fique em loop
        return_intermediate_steps=True,  # devolve os passos para a interface mostrar
    )