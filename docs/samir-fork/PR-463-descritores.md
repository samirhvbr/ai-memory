# PR akitaonrails/ai-memory#463 — descritor de hit não-FTS

**Fechado: mergeado em 2026-08-23 e lançado em v1.31.1 no mesmo dia.**
Documento de registro: o que foi enviado, com que evidência, e como o
mantenedor reagiu. As seções técnicas abaixo ficam como estão — descrevem o
defeito e o método de medição, que seguem válidos.

- PR: https://github.com/akitaonrails/ai-memory/pull/463
- Branch: `fix/non-fts-hit-descriptors` no fork `samirhvbr/ai-memory`
- Base: `upstream/main` em `b9b687b` (release v1.31.0)
- Commits: `ad0a64d` (correção) + `3694d05` (fix vindo do review do Copilot)
- Merge: `ce7202b` por Fabio Akita, 2026-08-23 17:40 -03
- Release: `v1.31.1`, 2026-08-23 19:28 -03 (1h48 depois do merge)

## O defeito

Só o caminho FTS5 monta um excerto de verdade para um hit
(`snippet(pages_fts, 1, '<mark>', '</mark>', '…', 24)`, centrado nos termos
casados). Os demais caminhos não têm termo casado para centrar e caíam em
`substr(body, 1, 240)` em **seis** queries de
`crates/ai-memory-store/src/reader.rs`:

| Caminho | Função |
|---|---|
| Recência global | `recent_pages` |
| Recência por projeto | `recent_pages_for_project` |
| Recência cross-project | `recent_pages_global` |
| Entity match | query de frequência inversa |
| Graph neighbour (saída) | `graph_neighbors_for_project_explained` |
| Graph neighbour (entrada) | mesma query, ramo do `UNION ALL` |

Numa página compilada esses 240 caracteres são a linha `# Título` mais o bloco
`## Session metadata` — o título que o hit já carrega no próprio campo, seguido
de um session id e três timestamps.

As seis queries são **byte-idênticas** entre v1.25.0 e v1.31.0 (o `reader.rs`
cresceu 667 linhas entre as versões sem tocar nenhuma dessas linhas).

## A medição

Feita pela API MCP pública, read-only, sem build instrumentado. Dois fatos
tornaram isso possível: `memory_query` já aceita `explain: true` e devolve
`fts_rank`/`vector_rank`/`graph_rank`/`entity_rank` por hit; e `memory_recent`
é servido por `recent_pages_for_project`, um dos seis sites — então um servidor
sem o patch responde exatamente o comportamento "antes".

Reproduzir: `python3 docs/samir-fork/pr-463/medir.py default x`
(servidor medido: `mem.shvia.org`, rodando v1.25.0, projeto `default/x`).

| | todas as 100 | substantivas (55) |
|---|---|---|
| 1ª linha repete o título | 74% | **53%** |
| prosa dentro dos 240 chars | 25 mediana | **35 mediana** |

Separar as substantivas importa: 45 das 100 páginas eram stubs `session-start`
quase vazios, e com eles o número fica bom demais.

Depois do patch, na amostra substantiva: repetição de título **0%**, descritor
médio **198 chars**, e **71%** das páginas de sessão caem nos prompts a partir
do segundo.

### O achado negativo (está declarado no corpo do PR)

Em 18 queries montadas de prompts reais do usuário, **179 hits, 100% via FTS**,
nenhum pelos streams vector/entity/graph. Ou seja: nessa instância o patch não
muda nada no `memory_query`. Causa apurada: não há embedding provider
configurado, e o corpus tem **zero `[[wikilinks]]`**, então o stream graph não
tem aresta para percorrer. É propriedade daquele corpus, não prova de que os
streams sejam ociosos em geral.

Por isso a moldura do PR lidera pelos **caminhos de recência**
(`memory_recent`/`memory_briefing`, afetados em todo hit, e cuja própria
descrição manda o agente chamar no início de toda sessão), e não pela busca.

## O que a evidência mudou no código

Duas regressões que a leitura de código não pegou, e a medição pegou:

1. **"primeira linha de prosa" era pouco.** Dava mediana de 56 chars e jogava
   6 de 25 páginas abaixo de 40, porque as páginas `_lint` abrem com um curto
   `"501 finding(s)."` e tudo que explica vem depois. Trocado por encher o
   orçamento: mediana 211.
2. **Sem pular metadado, ficava pior que o original.** A página de sessão
   passou a ter como descritor `- **session_id:** … - **started_at:** …`.
   Adicionado skip de bullet `- **chave:** valor` e de linha que repete o
   título.

E uma que o **review pegou e a medição não podia pegar** (`3694d05`): o skip
por prefixo do título só vale quando o título foi truncado. `truncate_for_title`
(`crates/ai-memory-hooks/src/payload.rs:888`) só acrescenta `…` acima de 80
chars, então título sem reticências é completo e uma linha maior que apenas
começa com ele é outra frase. Numa página cujas linhas todas abriam com um
título curto, *todas* eram descartadas e o fallback devolvia o corpo cru **com
o `# `** — o patch degradava para o bug que veio corrigir. O corpus medido não
exercitava isso porque todos os seus títulos de sessão passam de 80 chars.

## A objeção antecipada, já escrita no PR

"Isso é problema do compilador de páginas, não do caminho de leitura."

É a objeção certa. O campo `summary` do frontmatter já existe no vocabulário
deles (lint e curator leem), mas **0% das páginas amostradas tinham um
populado** — e no v1.31.0 o único `"summary"` no código de escrita é fixture de
teste (`crates/ai-memory-wiki/src/wiki.rs:2410`). Se o pipeline de consolidação
escrevesse `summary` ao compilar, o primeiro ramo do `COALESCE` dispararia e
todas as heurísticas abaixo virariam código morto.

Resposta já registrada no corpo do PR: a versão de leitura não precisa de
backfill, cobre página escrita via `memory_write_page` que nunca terá summary,
e não adiciona chamada de LLM na compilação. E foi oferecido mandar a versão de
escrita se ele preferir.

## Como o Akita reagiu

Mergeou sem pedir alteração nenhuma, e comentou nomeando três coisas como
"mais raras que o código" (comentário completo no PR):

> Merged, thank you — this is the most carefully evidenced contribution this
> repo has had.

1. **Reportar o número que enfraquece o próprio caso** — a separação em 55
   substantivas e 45 stubs, dizendo abertamente que os stubs inflam o
   resultado. Ele chamou os 53% de "o número honesto", e disse que ainda assim
   claramente vale corrigir.
2. **Limitar a afirmação em vez de generalizar** — os 179 hits 100% FTS
   poderiam virar "os outros streams são pouco usados"; dizer que *aquela
   instância* não tem embedding provider nem wikilinks é, nas palavras dele,
   "a diferença entre uma medição e uma conclusão".
3. **"Duas regras aqui existem porque a medição rejeitou a versão mais
   simples"** — manter o que o dado forçou em vez do que lê bonito.

Ele foi conferir a alegação mecânica das seis ocorrências e o grep dele achou
só duas, por ser literal demais e não pegar os quatro aliases de coluna
(`body`, `pages.body`, `pg.body`, `tp.body`/`fp.body`). Chegou a suspeitar que
a contagem estivesse inflada, verificou, e publicou o próprio erro: *"It was
not; mine was."*

Gate dele: fmt, clippy sob `-D warnings`, `cargo test --workspace` → 2532
passed, 0 failed.

## O que aconteceu com as pendências

- **CI**: fechou verde, 15 checks pass — clippy, rustfmt, test ubuntu e macos,
  cargo-deny, cargo-audit, os três builds release, docker smoke, gitleaks.
  `test (windows-latest)` seguiu SKIPPED, e é comportamento do workflow deles
  (job em run separado), não causado por nós.
- **Atribuição**: não deu problema. Os dois commits aparecem creditados a
  `samirhvbr` + `claude` no merge.
- **A objeção antecipada** (popular `summary` na escrita) **não foi
  levantada.** Continua sendo o trabalho seguinte natural se algum dia
  interessar: popular `summary` no frontmatter ao compilar página de sessão,
  no `ai-memory-consolidate`, com este patch virando o fallback para páginas
  sem summary.
- **Fork desatualizado**: segue pendente e é o único item vivo. O `main` de
  `samirhvbr/ai-memory` está em v1.25.0 contra v1.31.1 no upstream. Não afeta
  nada deste PR, mas se este checkout é o que roda o `mem.shvia.org`, o
  binário é de código de junho — e agora a correção que nós mesmos escrevemos
  só existe no upstream.

## O que sobrevive deste trabalho

O `medir.py` roda contra qualquer instância e não depende do patch: mede
repetição de título e comprimento de prosa pela API MCP pública, sem build
instrumentado nem acesso ao banco. Serve para conferir o efeito real depois de
atualizar o `mem.shvia.org`, e o método (medir pela API pública, separar a
população antes de reportar a média) vale para qualquer alegação de melhoria
que a gente for levar para lá.
