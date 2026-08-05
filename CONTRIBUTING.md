# Come contribuire

## Setup

1. Clona il repository:
```bash
   git clone https://github.com/codebysave/pr-to-requirements.git
   cd pr-to-requirements
```

2. Installa uv (se non lo hai): https://docs.astral.sh/uv/

3. Installa le dipendenze:
```bash
   uv sync
```

4. Verifica che tutto funzioni:
```bash
   uv run pytest
```

## Convenzioni per i commit

Usiamo Conventional Commits:

- `feat:` — nuova funzionalità
- `fix:` — correzione di un bug
- `docs:` — modifiche alla documentazione
- `chore:` — manutenzione (dipendenze, CI, configurazione)
- `test:` — aggiunta o modifica di test
- `refactor:` — refactoring senza cambio di comportamento

Esempio: `git commit -m "feat: add generation agent prompt"`

## Workflow

1. Crea un branch per ogni task: `git checkout -b feat/nome-task`
2. Lavora e fai commit sul tuo branch
3. Pusha il branch: `git push origin feat/nome-task`
4. Apri una Pull Request su GitHub
5. L'altro revisiona e approva
6. Squash and merge su main
7. Cancella il branch dopo il merge

## Formattazione del codice

Prima di ogni commit, controlla e formatta:

```bash
uv run ruff check .
uv run ruff format .
```

## Test

Esegui i test con:

```bash
uv run pytest
```