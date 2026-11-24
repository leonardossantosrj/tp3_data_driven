
import streamlit as st

from agente import criar_agente

st.set_page_config(page_title="Assistente de Treino de Corrida", page_icon="🏃")
st.title("🏃 Assistente de Treino de Corrida")
st.write("Pergunte sobre o clima para o seu treino e sobre pace e tempo de prova.")

with st.sidebar:
    st.subheader("Exemplos de perguntas")
    st.markdown(
        "- Como vai estar o tempo amanhã de manhã no Rio de Janeiro?\n"
        "- Quero fazer a maratona em 3h45. Qual pace preciso manter?\n"
        "- E se for em 4 horas?\n"
        "- Sábado tenho um longão de 25 km em São Paulo a 5:30/km. "
        "Que horário começar para pegar menos calor?"
    )
    if st.button("Nova conversa"):
        st.session_state.clear()  # apaga o histórico e a memória do agente
        st.rerun()

# O agente (com a memória dele) é criado uma vez por sessão e guardado no session_state
if "agente" not in st.session_state:
    try:
        st.session_state.agente = criar_agente()
    except ValueError as erro:
        st.error(str(erro))
        st.stop()
    st.session_state.mensagens = []


def mostrar_passos(passos):
    """Mostra o raciocínio ReAct do agente: cada ação e o que ele observou."""
    with st.expander("Como o agente pensou"):
        for acao, observacao in passos:
            st.markdown(f"**Ação:** `{acao.tool}` com a entrada `{acao.tool_input}`")
            st.text(observacao)


# Mostra o histórico da conversa
for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["papel"]):
        st.write(mensagem["texto"])
        if mensagem.get("passos"):
            mostrar_passos(mensagem["passos"])

pergunta = st.chat_input("Digite sua pergunta")
if pergunta:
    with st.chat_message("user"):
        st.write(pergunta)
    st.session_state.mensagens.append({"papel": "user", "texto": pergunta})

    with st.chat_message("assistant"):
        try:
            with st.spinner("Pensando..."):
                resultado = st.session_state.agente.invoke({"input": pergunta})
        except Exception as erro:
            st.error(f"Não foi possível obter a resposta do modelo. Detalhe: {erro}")
            st.stop()
        st.write(resultado["output"])
        passos = resultado["intermediate_steps"]
        if passos:
            mostrar_passos(passos)

    st.session_state.mensagens.append({"papel": "assistant", "texto": resultado["output"], "passos": passos})