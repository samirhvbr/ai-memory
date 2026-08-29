# PR akitaonrails/ai-memory#477 — summary na escrita das páginas de sessão

**Fechado: mergeado em 2026-08-24 como `488a0b6`.** Continuação direta de
[PR-463-descritores.md](PR-463-descritores.md) — aquele fez o descritor
preferir `frontmatter.summary`; este fez alguém escrever um.

- Issue: https://github.com/akitaonrails/ai-memory/issues/473 (fechada)
- PR: https://github.com/akitaonrails/ai-memory/pull/477
- Commits: `b5fee47` (zero-LLM) + `4828ab2` (LLM) + `f3398fd` (correções do review)
- Release: ainda não saiu no fechamento deste registro (última tag `v1.31.1`,
  o merge é posterior)

## O que motivou

Medição pós-patch do #463 em produção: **0 de 25** páginas substantivas tinham
`frontmatter.summary`. Ou seja, o ramo preferido do `COALESCE` que tínhamos
acabado de mergear nunca disparava — tudo vinha do fallback heurístico.

## O que entrou

Três escritores, não um:

| caminho | onde | por quê |
|---|---|---|
| zero-LLM (`SessionEnd`) | `ai-memory-hooks/src/synth.rs` | é o **padrão documentado** |
| LLM single-page | `consolidate_session` → `build_frontmatter` | `multi_page` default é **false** |
| LLM batch | `consolidate_session_multi` → `build_update` | opt-in |

No zero-LLM o summary vem de contagens que o `render_body` já calculava e
jogava fora (prompts, chamadas completas por ferramenta, duração). Um tally
por página, emprestado aos dois renderizadores.

Nos caminhos LLM é campo opcional no structured output — zero chamada nova de
modelo — mais `usable_summary`, que rejeita no boundary o que o reader
descartaria.

## Os dois erros meus, e quem pegou cada um

**O Akita pegou o primeiro, antes do código:** eu propus corrigir só o
`ai-memory-consolidate` e ele apontou que o zero-LLM é o padrão. "There are
two writers, not one."

**O Copilot pegou o mesmo erro de novo, no outro eixo.** Eu cobri
`consolidate_session_multi` e deixei de fora o `consolidate_session`, que é o
default (`multi_page.unwrap_or(false)`, `server.rs:2501`) e o que o worker do
serve usa. Metade do PR era código morto. Ele também pegou que o prompt do
batch dizia literalmente `No 'body', no 'content', no 'summary'` — então nem
no caminho coberto o modelo emitiria o campo.

E pegou um tally calculado duas vezes, exatamente o que o Akita tinha pedido
para não acontecer — sendo que a doc e a minha mensagem de commit afirmavam o
contrário. Mais um teste flaky (`Timestamp::now()` duas vezes com asserção de
duração zero) e o CHANGELOG fora do formato do `AGENTS.md:362`.

**Todos procedentes.** Verifiquei cada um contra o código antes de aceitar.

## O achado que só apareceu no merge

Eu tinha corrigido a descrição da armadilha dele: um summary em estilo de
bullet de metadado **não** produz descritor vazio — o `page_descriptor` cai em
`truncate_chars(raw.trim(), …)` e ecoa o raw inteiro, então a página fica
descrita *pior* do que se o campo estivesse vazio.

Ele confirmou ("You were right and I was wrong about the trap") e fez a
conexão que eu não tinha explicitado: **é essa correção que torna o
`usable_summary` necessário em vez de só organizado.** E notou um efeito que
eu não tinha percebido — a validação no boundary **limita o risco que eu
declarei não ter testado**: um modelo pequeno emitindo summary malformado
agora perde o campo em vez de estragar a página.

## O que ele destacou como hábito

1. O teste principal afirma que **a linha de base é forte** — que o descritor
   derivado do body chega nos prompts, "what #463 already delivers" — antes de
   afirmar o que o summary acrescenta. Comparar com espantalho teria parecido
   mais impressionante.
2. Dizer abertamente que não rodei a checagem contra modelo pequeno vale mais
   para ele do que a checagem valeria.

Verificação dele: merge limpo, `fmt`, `clippy -D warnings`, gate do changelog,
**2562 testes / 0 falhas** na árvore mergeada. Conferiu especificamente que a
entrada caiu em `[Unreleased]` — auto-merge já derrubou entrada em seção
congelada nesse repo antes.

## Pendências

- **Medir em produção quando o release sair.** Será a primeira vez que o ramo
  preferido dispara de verdade. `python3 docs/samir-fork/pr-463/medir.py
  default x` roda contra qualquer instância; o número a bater é o `0 de 25`.
- **Schema contra modelo pequeno** (Kimi/qwen3) segue não testado. Declarado
  no PR. O `usable_summary` limita o dano, não elimina o teste.
- **43 páginas pré-#386** de lixo lifecycle-only na instância do `mem.shvia.org`
  (43% do projeto `x`). Sujam listagem por recência e qualquer medição futura.

## Medição pós-release (27/08/2026, produção em v1.32.2)

**O código está escrevendo.** Linha de base era `0 de 25` páginas com
`frontmatter.summary` (v1.31.1). Agora:

| | |
|---|---|
| com `frontmatter.summary` | **4 de 100** |
| descritor: 1ª linha repete o título | 0% (todas e substantivas) |
| prosa nos 240 chars, substantivas | mediana 185, média 187 |
| hits de busca sem FTS | 0,0% de 219 hits em 22 queries |

São 4 e não mais porque o PR é **new-writes-only**: só sessões encerradas
depois do upgrade ganham o campo. As 4 são as das últimas ~12h. O número sobe
sozinho conforme sessões novas fecham.

Texto real gerado, exatamente a forma projetada:

```
8 prompts, 580 completed tool calls across tool non-file, tool unknown and tool file, over 19h 30m.
2 prompts, 53 completed tool calls across tool non-file, tool file and tool unknown, over 5h 20m.
```

**Achado colateral, não reportado ainda:** `across tool non-file, tool unknown
and tool file` são os literais compartilhados do `safe_tool_title`
(`payload.rs`) vazando para dentro do resumo. Funciona, mas não informa nada —
"580 chamadas entre *tool non-file* e *tool unknown*". É a mesma família do
defeito de título da #484, agora do lado do resumo. Candidato a issue com
medição, no molde que já rendeu três merges.

**Sonda instalada** (`~/.local/state/ai-memory-watch/sonda-477.sh`, cron do
sistema às 09:17): mede a cobertura todo dia e escreve em
`477-cobertura.log` + `477-status.txt`. Se travar por dias com sessões
acontecendo, aí sim é defeito.
