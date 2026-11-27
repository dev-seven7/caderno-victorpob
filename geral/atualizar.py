# -*- coding: utf-8 -*-
"""Regera geral/dados.json com as demandas do Ogro (issues de dev-seven7/cs-ogro-steaks + status do board S7).

Uso (na raiz do repo caderno-victorpob):  python -I geral/atualizar.py
Precisa do gh logado com scope project. Nao grava segredo: so titulo, numero, estado, datas, status e login de quem e dono.
"""
import json, subprocess, sys, datetime, pathlib

REPO = "dev-seven7/cs-ogro-steaks"
AQUI = pathlib.Path(__file__).resolve().parent
IGNORAR = {35, 42}  # setup da estacao e issue de teste

def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        sys.exit("gh falhou: " + r.stderr.strip())
    return json.loads(r.stdout)

def frente(t):
    t = t.lower()
    regras = [
        ("Cardápio Digital", ["cardápio digital", "databite"]),
        ("Mídia e tracking", ["meta ads", "meta ·", "tracking", "tráfego pago", "pixel", "ga4"]),
        ("Lançamento SG", ["são gonçalo", " sg "]),
        ("Conteúdo", ["calendário", "pauta", "quadros", "rotina social", "reels", "gravação", "conteúdo", "destaques", "estratégia", "plano"]),
        ("Black Friday", ["black"]),
        ("Parcerias e comunidade", ["influenc", "parceiros", "comunidade"]),
        ("Marca e franquia", ["bárbara", "curso", "kit", "protocolo", "brand", "atendimento"]),
    ]
    for nome, chaves in regras:
        if any(c in t for c in chaves):
            return nome
    return "Base e operação"

def main():
    hoje = datetime.date.today()
    issues = gh("issue", "list", "-R", REPO, "--state", "all", "--limit", "300",
                "--json", "number,title,state,assignees,createdAt,updatedAt,closedAt")
    board = gh("project", "item-list", "1", "--owner", "dev-seven7", "--limit", "600", "--format", "json")
    st = {}
    for x in board.get("items", []):
        if "cs-ogro-steaks" in str(x.get("repository", "")):
            st[x.get("content", {}).get("number")] = (x.get("status"), x.get("priority"))
    out = []
    for i in issues:
        n = i["number"]
        if n in IGNORAR:
            continue
        status, prio = st.get(n, (None, None))
        no_board = n in st
        if i["state"] == "CLOSED" or status == "Done":
            sit = "Concluída"
        elif not no_board:
            sit = "Fora do board"
        else:
            sit = {"In progress": "Em andamento", "In review": "Em revisão", "Ready": "Pronta pra começar",
                   "Backlog": "Backlog", "Attention": "Atenção"}.get(status, status or "No board, sem status")
        upd = datetime.date.fromisoformat(i["updatedAt"][:10])
        out.append({
            "n": n, "titulo": i["title"].strip(), "estado": i["state"].lower(), "situacao": sit,
            "status_board": status, "prioridade": prio, "no_board": no_board, "frente": frente(" " + i["title"] + " "),
            "donos": [a["login"] for a in i["assignees"]],
            "criada": i["createdAt"][:10], "atualizada": i["updatedAt"][:10],
            "dias_sem_mov": (hoje - upd).days,
        })
    out.sort(key=lambda d: (d["estado"] != "open", -d["n"]))
    dados = {"gerado_em": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "repo": REPO, "demandas": out}
    (AQUI / "dados.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    abertas = sum(d["estado"] == "open" for d in out)
    print(f"dados.json: {len(out)} demandas, {abertas} abertas, {sum(d['situacao']=='Fora do board' for d in out)} fora do board")

if __name__ == "__main__":
    main()
