
import requests
from langchain_core.tools import tool

URL_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
URL_PREVISAO = "https://api.open-meteo.com/v1/forecast"


@tool
def previsao_do_tempo(entrada: str) -> str:
    """Consulta a previsão do tempo hora a hora de uma cidade em uma data.
    Entrada: cidade e data separadas por ponto e vírgula, no formato
    "Cidade; AAAA-MM-DD". Exemplo: "Rio de Janeiro; 2026-11-25".
    Retorna temperatura, sensação térmica, umidade e chance de chuva de cada hora.
    Só funciona para hoje e para os próximos 15 dias."""
    if ";" not in entrada:
        return 'Entrada inválida. Use o formato "Cidade; AAAA-MM-DD".'
    cidade, data = [parte.strip() for parte in entrada.split(";", 1)]

    try:
        # 1. Descobre a latitude e a longitude da cidade
        resposta = requests.get(
            URL_GEOCODING,
            params={"name": cidade, "count": 1, "language": "pt"},
            timeout=10,
        )
        resultados = resposta.json().get("results")
        if not resultados:
            return f"Cidade '{cidade}' não encontrada. Confira o nome e tente de novo."
        local = resultados[0]

        # 2. Busca a previsão hora a hora para a data pedida
        resposta = requests.get(
            URL_PREVISAO,
            params={
                "latitude": local["latitude"],
                "longitude": local["longitude"],
                "hourly": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation_probability",
                "timezone": "auto",
                "start_date": data,
                "end_date": data,
            },
            timeout=10,
        )
        previsao = resposta.json()
    except requests.exceptions.RequestException as erro:
        return f"Não foi possível consultar a previsão agora. Erro de conexão: {erro}"

    # A API responde com {"error": true, "reason": "..."} quando a data é inválida
    if previsao.get("error"):
        return f"A API de previsão recusou a consulta: {previsao['reason']}"

    horas = previsao["hourly"]
    linhas = [f"Previsão para {local['name']} ({local.get('admin1', '')}, {local.get('country', '')}) em {data}:"]
    for i, horario in enumerate(horas["time"]):
        linhas.append(
            f"{horario[11:16]}: {horas['temperature_2m'][i]}°C "
            f"(sensação {horas['apparent_temperature'][i]}°C), "
            f"umidade {horas['relative_humidity_2m'][i]}%, "
            f"chuva {horas['precipitation_probability'][i]}%"
        )
    return "\n".join(linhas)


def texto_para_segundos(tempo):
    """Converte "h:mm:ss" ou "mm:ss" em segundos."""
    partes = [int(parte) for parte in tempo.split(":")]
    if len(partes) == 3:
        return partes[0] * 3600 + partes[1] * 60 + partes[2]
    if len(partes) == 2:
        return partes[0] * 60 + partes[1]
    raise ValueError(f"tempo '{tempo}' fora do formato")


def segundos_para_texto(segundos):
    """Converte segundos em "h:mm:ss"."""
    segundos = round(segundos)
    return f"{segundos // 3600}:{segundos % 3600 // 60:02d}:{segundos % 60:02d}"


@tool
def calcular_pace(entrada: str) -> str:
    """Faz contas de corrida com distância, tempo e pace.
    Entrada: distância em km e tempo ou pace, separados por ponto e vírgula.
    - Para descobrir o pace, informe o tempo total em h:mm:ss. Exemplo: "42.195; 3:45:00".
    - Para descobrir o tempo total, informe o pace em m:ss/km. Exemplo: "25; 5:30/km".
    Use 42.195 para maratona, 21.0975 para meia maratona, 10 para 10 km e 5 para 5 km."""
    try:
        distancia_texto, tempo_texto = [parte.strip() for parte in entrada.split(";")]
        distancia = float(distancia_texto.replace(",", "."))
        if distancia <= 0:
            return "A distância precisa ser maior que zero."

        if tempo_texto.endswith("/km"):
            # Pace informado: calcula o tempo total
            pace = texto_para_segundos(tempo_texto.replace("/km", "").strip())
            tempo_total = pace * distancia
        else:
            # Tempo total informado: calcula o pace
            tempo_total = texto_para_segundos(tempo_texto)
            pace = tempo_total / distancia
    except ValueError:
        return (
            'Entrada inválida. Use "distância; h:mm:ss" para calcular o pace '
            'ou "distância; m:ss/km" para calcular o tempo total.'
        )

    pace = round(pace)
    pace_texto = f"{pace // 60}:{pace % 60:02d}"
    return (
        f"Distância: {distancia} km | Tempo total: {segundos_para_texto(tempo_total)} | "
        f"Pace: {pace_texto}/km"
    )