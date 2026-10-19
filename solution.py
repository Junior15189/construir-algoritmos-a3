import os

import requests
from dotenv import load_dotenv
from folium import Icon, Map, Marker, Popup

BASE_URL = "http://api.olhovivo.sptrans.com.br/v2.1"
TERMOS_BUSCA = ["118Y", "Lapa", "Jabaquara", "Santo Amaro"]

load_dotenv(".env")

s = requests.Session()
res = s.post(f"{BASE_URL}/Login/Autenticar?token={os.getenv('SPTRANS_TOKEN')}")
if res.text.strip().lower() != "true":
    raise SystemExit("Falha na autenticação: verifique SPTRANS_TOKEN no arquivo .env")


def get_json(url):
    """GET que devolve lista/dict; avisa se a API respondeu algo inesperado."""
    r = s.get(url)
    try:
        return r.json()
    except ValueError:
        print(f"  Resposta inesperada ({r.status_code}): {r.text[:200]}")
        return []

linha = paradas = onibus = hora = None
for termo in TERMOS_BUSCA:
    linhas = get_json(f"{BASE_URL}/Linha/Buscar?termosBusca={termo}")
    if not isinstance(linhas, list) or not linhas:
        print(f"'{termo}': nenhuma linha. Resposta: {linhas}")
        continue
    print(f"'{termo}': {len(linhas)} linhas encontradas")

    for candidata in linhas:
        cod = candidata["cl"]
        ps = get_json(f"{BASE_URL}/Parada/BuscarParadasPorLinha?codigoLinha={cod}")
        pos = get_json(f"{BASE_URL}/Posicao/Linha?codigoLinha={cod}")
        if not isinstance(ps, list):
            print(f"  linha {cod}: resposta de paradas inesperada: {ps}")
            continue
        vs = pos.get("vs") or [] if isinstance(pos, dict) else []
        print(f"  linha {cod} ({candidata['lt']}-{candidata['sl']}): {len(ps)} paradas, {len(vs)} ônibus")
        if ps and vs:
            linha, paradas, onibus, hora = candidata, ps, vs, pos.get("hr")
            break
        if ps and linha is None:
            linha, paradas, onibus, hora = candidata, ps, vs, pos.get("hr")
    if paradas and onibus:
        break

if not paradas:
    raise SystemExit(
        "Nenhuma linha com paradas foi encontrada. "
    )

nome_linha = f"{linha['lt']}-{linha['tl']} ({linha['tp']} / {linha['ts']})"
print(f"\nLinha selecionada: {nome_linha} - código {linha['cl']}")
print(f"{len(paradas)} paradas | {len(onibus)} ônibus em circulação (atualizado às {hora})")

m = Map(location=[paradas[0]["py"], paradas[0]["px"]], zoom_start=13)

for p in paradas:
    Marker(
        location=[p["py"], p["px"]],
        popup=Popup(f"{p['np']}<br>{p['ed']}", max_width=250),
        tooltip=p["np"],
        icon=Icon(color="orange", icon="info-sign"),
    ).add_to(m)
for b in onibus:
    Marker(
        location=[b["py"], b["px"]],
        popup=Popup(f"Ônibus {b['p']}<br>Linha {nome_linha}<br>Atualizado: {b['ta']}", max_width=250),
        tooltip=f"Ônibus {b['p']}",
        icon=Icon(color="blue", icon="bus", prefix="fa"),
    ).add_to(m)

m.save("mapa.html")
print("Mapa salvo em mapa.html")
