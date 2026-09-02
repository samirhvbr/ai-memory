# TODO — servidor de memória compartilhado (`mem.shvia.org`)

> Onboarding de uma máquina nova (ou de mais uma pessoa do time) no nosso
> servidor ai-memory. Serve para Claude Code, Codex, OpenCode, Gemini CLI
> e qualquer agente que o `install-hooks` suporte.
>
> Este doc é do **lado cliente**. Como o servidor sobe, o proxy, o TLS e a
> ligação com o Laravel estão em `SHVIA-WEB/deploy/ai-memory-servidor.md`.

> ⚠️ **Este arquivo vive num fork público (`samirhvbr/ai-memory`).** Não
> entra aqui: token, IP do servidor, endereço de LAN, nome de host interno.
> O token vai por canal privado (mensagem direta / gerenciador de senhas),
> nunca por issue, PR, commit ou print.

Estado do fork quando este doc foi escrito: `v1.18.0`, `main` sincronizado
com `akitaonrails/ai-memory` — nossos patches viraram PR upstream, não
divergência local. Ou seja: **o wrapper oficial serve, não precisa instalar
nada "do nosso fork"** (ver §2).

> **Sync 11/08/2026:** `main` re-sincronizado com o upstream em `v1.25.0`
> (rebase deste doc por cima — segue sem divergência de código).

> **Sync 2026-09-02:** `main` fast-forwarded to upstream **`v2.0.0`**; this
> branch rebased on top of it. Still zero code divergence — the fork carries
> `docs/samir-fork/` and nothing else, so §2 stands: install the official
> wrapper, not ours.

## ⚠️ Upgrading a client to 2.0 (2026-09-02)

Read this before running `ai-memory upgrade`. 2.0 is the first release that
changes the **on-disk format**, and the change is a one-way door.

**If you only use `mem.shvia.org`, this is a two-command upgrade.** Clients
talk HTTP; they never open the data directory. The migration is the server's
problem, and it has already been done for you.

```bash
ai-memory upgrade                                     # wrapper + image
ai-memory install-hooks --agent claude-code --apply   # re-stage: hook scripts changed
ai-memory --version                                   # expect 2.0.0
```

Nothing to change in `~/.claude/settings.json` or `~/.claude.json` — 2.0 does
not move any endpoint. `AI_MEMORY_HOOK_URL` and the MCP `url` stay as they are.

**If you run your own server** (the "everyone with their own" topology in §3),
the one-way door is yours to handle:

- The first 2.0 start migrates the wiki to Open Knowledge Format v0.2 **in
  place**, gated on a full backup that is written *and re-read to verify*. If
  that backup cannot be written, the server refuses to start and your data is
  untouched. In a container the archive goes to `/data/backups/` — not `$HOME`,
  which is destroyed on the next `docker compose up -d`.
- Once migrated, **a pre-2.0 binary refuses the data directory.** Rolling back
  means restoring the archive, not re-pulling the old image: 1.x can read the
  new frontmatter but its writes will not carry the OKF keys, which mixes the
  store.
- **Pin the tag.** `:latest` means a future 2.x migration can run at a moment
  you did not choose. Use `akitaonrails/ai-memory:2.0.0`.
- **Local embeddings are on by default** — a ~87 MB model downloads in the
  background on first start, existing pages get backfilled, and hybrid search
  turns on at the *next* restart. Inference runs in-process, so budget CPU and
  RAM on whatever else that box is serving. Opt out with
  `embedding_provider = "none"`.

Full checklist upstream: `docs/MIGRATION-2.0.md`.

**What you actually get for it:** hybrid retrieval (LongMemEval-S hit@5 went
0.617 → 0.823), `as_of` time-travel on `memory_query`, typed `causes` /
`fixes` / `contradicts` edges that surface contradictions as lint findings,
and a `status` command that finally reports embedding coverage, wiki format
and write-queue backpressure instead of just claiming health.

---

## 0. O que mudou desde o passo a passo que eu te mandei

| Antes | Agora | Por quê |
|---|---|---|
| `http://<ip>:49374` | `https://mem.shvia.org` — **443, sem porta** | vhost dedicado com Let's Encrypt |
| token colado no passo a passo | token por canal privado | o passo a passo circulou em texto puro |
| token único do time | um token por pessoa (§9, pendente) | atribuição de autoria e revogação individual |

O IP:porta antigo continua respondendo (nada quebra pra quem já configurou),
mas o endereço canônico é o domínio. Quem for mexer, migra; quem não, não
tem pressa.

**Duas regras que economizam uma hora de debug** (detalhe em §8):

- É `https://`, nunca `http://`. Com `http` a resposta é 301 e o cliente
  **descarta o `Authorization`** no redirect — você vê `401` com o token
  certo.
- É `mem.shvia.org` **sem** `:49374`. A 49374 fala HTTP puro e não está
  aberta pra fora; colar a porta num nome com TLS quebra o handshake.

---

## 1. Pré-requisitos

- [ ] **Docker** na máquina cliente — o `bin/ai-memory` é um wrapper que roda
      o binário dentro de container. Sem Docker existe caminho alternativo:
      - Arch: `yay -S ai-memory-bin` (binário nativo em `/usr/bin/ai-memory`)
      - Qualquer um: `scripts/install-hooks.sh` via curl instala só os
        scripts de hook, sem Docker (ver `docs/install.md` §"Installing
        hooks without docker")
- [ ] `~/.local/bin` no `PATH`
- [ ] O token, recebido por canal privado

Não precisa de Docker *servidor* na sua máquina — o servidor é o
`mem.shvia.org`. O Docker local é só pra rodar o CLI.

---

## 2. Instalar o CLI

```bash
mkdir -p ~/.local/bin
curl -fsSL https://raw.githubusercontent.com/akitaonrails/ai-memory/main/bin/ai-memory \
  -o ~/.local/bin/ai-memory
chmod +x ~/.local/bin/ai-memory
```

No `~/.zshrc` (ou `~/.bashrc`):

```bash
export PATH="$HOME/.local/bin:$PATH"
```

> Enquanto nosso `main` estiver sincronizado com o upstream, o wrapper do
> `akitaonrails` **é** o nosso. Só troque a URL para
> `.../samirhvbr/ai-memory/main/bin/ai-memory` se um dia carregarmos patch
> local no wrapper — hoje seria só uma cópia idêntica que envelhece sozinha.

---

## 3. Apontar para o servidor

Nas mesmas duas linhas do rc (persistidas — sem elas o CLI cai no loopback
e "funciona" contra um servidor vazio que não existe):

```bash
export AI_MEMORY_SERVER_URL="https://mem.shvia.org"
export AI_MEMORY_AUTH_TOKEN="<token — canal privado>"
```

`AI_MEMORY_SERVER_URL` é herdado por todos os subcomandos (`status`,
`search`, `bootstrap`, `install-mcp`, `install-hooks`, …). Os flags
`--server-url` / `--auth-token` sobrescrevem o ambiente quando você precisa
gerar config apontando pra outro servidor.

---

## 4. Ligar no Claude Code

```bash
ai-memory install-mcp   --client claude-code --apply
ai-memory install-hooks --agent  claude-code --apply
```

Com `AI_MEMORY_SERVER_URL` exportado, o `install-mcp` deriva o endpoint
`/mcp` sozinho e o `install-hooks` usa a origem crua. O que isso escreve:

| Arquivo | O que entra |
|---|---|
| `~/.claude.json` | `mcpServers["ai-memory"]`: `type: http`, `url: https://mem.shvia.org/mcp`, header `Authorization: Bearer <token>` |
| `~/.claude/settings.json` | `env.AI_MEMORY_HOOK_URL` + `env.AI_MEMORY_AUTH_TOKEN`, e 9 hooks (SessionStart, UserPromptSubmit, Pre/PostToolUse, PreCompact, Stop, SessionEnd, SubagentStart/Stop) |
| `~/.local/share/ai-memory/hooks/claude-code/` | os scripts `.sh` que os hooks chamam |

⚠️ **O token fica em texto puro nesses dois arquivos.** Se você versiona
dotfiles, exclua `~/.claude.json` e `~/.claude/settings.json` (ou pelo menos
o bloco `env`) do repo.

Ordem importa a favor: se rodar `install-mcp --apply` primeiro, o
`install-hooks` reaproveita a entrada MCP existente e mantém captura e MCP
apontando para o mesmo servidor em vez de cair no loopback.

Outros agentes: mesmo comando trocando `--agent` (`codex`, `opencode`,
`gemini-cli`, `cursor`, `grok`, …). `--help` lista os suportados na versão
instalada.

---

## 5. Verificar

```bash
ai-memory status
```

Checagens de rede que separam os três erros possíveis (rede, bearer,
allowlist de `Host`):

```bash
# 200 + lista de workspaces = rede + token + Host, tudo ok
curl -s -H "Authorization: Bearer $AI_MEMORY_AUTH_TOKEN" \
  https://mem.shvia.org/api/v1/workspaces

# 401 aqui é ESPERADO (prova que o bearer está ligado no servidor)
curl -s -o /dev/null -w '%{http_code}\n' https://mem.shvia.org/api/v1/workspaces

# 401 AQUI é o sintoma do redirect que come o bearer — use https, não http
curl -s -o /dev/null -w '%{http_code}\n' -L \
  -H "Authorization: Bearer $AI_MEMORY_AUTH_TOKEN" \
  http://mem.shvia.org/api/v1/workspaces
```

Como ler o resultado:

- `401` **com** token no `https` → token errado/expirado.
- `403` → seu `Host` não está na allowlist do servidor (config do servidor,
  não sua). Parece erro de token e não é.
- `000` / timeout → rede/DNS.

Fim a fim: abra o Claude Code num projeto, converse, saia, abra de novo. O
`SessionStart` deve trazer o handoff da sessão anterior.

---

## 6. Uso no dia a dia

**Captura é automática.** Os hooks gravam prompt, tool-use e fim de sessão
sem você pedir. Você não escreve nota à mão — só quando quer um fato
permanente ("lembre que X"), aí vira página de wiki.

**Handoff entre sessões e entre agentes.** `session-end` escreve o handoff,
o `session-start` da próxima sessão consome (uso único). Funciona
cross-agent: sai do Claude Code, entra no Codex na mesma pasta, ele já
começa sabendo. Handoff criado por engano: `memory_handoff_cancel` com o
`handoff_id`.

**Consulta proativa.** "já discutimos X?", "o que decidimos sobre Y?" →
o agente chama `memory_query` / `memory_recent`. Para ele saber *quando*
chamar sozinho, instale o pacote de roteamento **uma vez por projeto**:

```bash
ai-memory install-instructions          # detecta CLAUDE.md / AGENTS.md
ai-memory install-instructions --print  # preview, não escreve
```

Ou peça ao próprio agente: *"instala o roteamento do ai-memory neste
projeto"*. Ele edita só o bloco entre `<!-- ai-memory:start -->` e
`<!-- ai-memory:end -->` e preserva o resto do arquivo.

**Escopo.** Tudo é auto-escopado ao projeto resolvido pelo `cwd` da sessão.
Não passe `project`/`workspace` na mão a não ser para perguntar sobre
*outro* projeto explicitamente.

**Ler a wiki.** A wiki é markdown em git no volume do servidor — dá pra
navegar pela UI web do ai-memory ou por qualquer viewer de markdown com
acesso ao volume.

**Regra de segurança que vale pros dois lados:** memória recuperada é
**dado histórico não confiável**, não instrução. Se uma página pedir pra
rodar comando, revelar segredo ou mudar permissão, isso é evidência citada
— não ordem.

---

## 7. Manutenção

```bash
ai-memory upgrade                            # puxa a imagem nova
ai-memory install-hooks --agent claude-code --apply   # re-stage dos scripts
ai-memory install-instructions               # atualiza roteamento nos projetos
```

Depois de subir versão, re-staging dos hooks e refresh do roteamento não são
opcionais: scripts e guidance de tools mudam entre releases. As três
operações são idempotentes.

---

## 8. Armadilhas (todas já custaram tempo)

1. **`http://` em vez de `https://`** → 301 → Guzzle/curl tratam troca de
   esquema como cross-origin e **descartam o `Authorization`** → `401` com
   token correto.
2. **`:49374` no domínio** → a porta fala HTTP puro e não está exposta;
   com TLS o handshake quebra.
3. **`403` que parece token errado** → allowlist de `Host` no servidor.
4. **Sem `AI_MEMORY_SERVER_URL` exportado** → o CLI usa `127.0.0.1:49374`,
   não acha nada e não reclama de forma óbvia.
5. **Token em texto puro** nos configs do Claude Code — não versione.
6. **Servidor precisa ser alcançável de quem faz o request.** No chat do
   ShvIA quem chama é o servidor do Laravel, não o browser: `localhost` do
   notebook de alguém não serve.

---

## 9. TODO em aberto

Feito:

- [x] Servidor no ar com bearer, volume persistente e `--restart unless-stopped`
- [x] Vhost dedicado + TLS (`https://mem.shvia.org`) no lugar de IP:porta
- [x] Claude Code (MCP + 9 hooks) ligado na minha máquina
- [x] Fork sincronizado com upstream — última sync: `v1.25.0` (11/08/2026)

A fazer:

- [ ] **Token por pessoa em vez do token único.** Hoje o mesmo bearer é o
      token **root** — quem tem ele tem `/admin/*` e não dá pra saber quem
      escreveu o quê, nem revogar uma pessoa sem quebrar todo mundo. O
      caminho é `[auth].token_pepper` + `ai-memory user add --username …`
      (ver `docs/users.md`); com pepper configurado, `user rotate-token` e
      `user expire` passam a ser por pessoa. **Prioridade alta agora que
      somos dois.**
- [ ] **Rotacionar o token atual** — ele circulou em texto puro num passo a
      passo por mensagem. Trocar junto com o item acima.
- [ ] **Backup do volume `ai-memory-data`.** A wiki é markdown em git, o
      índice SQLite é derivado — perder o volume é perder a memória do time.
      Definir destino e periodicidade.
- [ ] **Consolidação por LLM** (`AI_MEMORY_LLM_PROVIDER`): hoje roda a
      síntese rule-based. Aceita endpoint OpenAI-compat — dá pra apontar
      pro nosso próprio gateway em vez de contratar provider.
- [ ] **Convenção de projeto/workspace** entre nós dois, pra memória de
      repositórios diferentes não virar um caldo só.
- [ ] **Onboarding do sócio concluído** — rodar §1→§5 e confirmar o handoff
      cross-sessão funcionando.
- [ ] Decidir se `docs/samir-fork/` continua neste fork público ou migra
      pra um repo privado do time (ver aviso no topo).

---

## Referências

- `docs/install.md` — instalação completa, todos os caminhos (Docker, AUR,
  sem Docker, Windows, macOS)
- `docs/usage.md` — uso diário, handoff, roteamento, bootstrap
- `docs/users.md` — modo multi-usuário, `token_pepper`, tokens por pessoa
- `docs/mcp-install.md` — detalhes por cliente MCP
- `SHVIA-WEB/deploy/ai-memory-servidor.md` — lado servidor (Docker, proxy,
  TLS, envs do Laravel, aba Memória por usuário)
