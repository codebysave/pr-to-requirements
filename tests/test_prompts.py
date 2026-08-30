from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from are.agents.prompts import (
    ASSESSMENT_AGENT,
    GENERATION_AGENT,
    PromptNotFoundError,
    load_prompt,
)

AGENTS = (GENERATION_AGENT, ASSESSMENT_AGENT)


def test_repository_prompts_are_available_for_every_agent() -> None:
    for agent in AGENTS:
        prompt = load_prompt(agent)

        assert prompt.strip()


def test_generation_prompt_states_the_project_conventions() -> None:
    prompt = load_prompt(GENERATION_AGENT)

    # I vincoli della Decisione 3.1 devono essere presenti nel prompt.
    assert "shall" in prompt
    assert "black-box" in prompt.lower()
    # I cinque pattern EARS adottati (Decisione 3.1, §6).
    assert "The system shall <response>" in prompt
    assert "When <trigger>" in prompt
    assert "While <state>" in prompt
    assert "If <undesired condition>" in prompt
    assert "Where <feature is present>" in prompt


def test_both_prompts_forbid_referring_to_the_change_itself() -> None:
    """Il requisito descrive il sistema, non la Pull Request (Decisione 3.1, §8.2)."""

    for agent in AGENTS:
        prompt = load_prompt(agent)

        assert "the remediation" in prompt, agent
        assert "Pull Request" in prompt, agent


def test_assessment_prompt_lists_every_decision() -> None:
    prompt = load_prompt(ASSESSMENT_AGENT)

    for decision in ("ACCEPT", "REVISE", "REJECT", "CONFIRM_NOT_EXTRACTABLE"):
        assert decision in prompt


def test_every_prompt_requires_a_single_json_object() -> None:
    for agent in AGENTS:
        prompt = load_prompt(agent)

        assert "single JSON object" in prompt, agent
        assert "no markdown code fences" in prompt, agent


def test_every_prompt_contains_at_least_one_valid_json_example() -> None:
    """Gli esempi guidano i modelli piccoli: devono essere JSON realmente validi."""

    for agent in AGENTS:
        prompt = load_prompt(agent)
        # Gli esempi compaiono come oggetto dentro <output>, oppure come riga
        # a sé stante. Le righe con il carattere di alternativa descrivono lo
        # schema di risposta, non un esempio concreto.
        esempi = re.findall(r"<output>(\{.*?\})</output>", prompt, re.DOTALL)
        esempi += [
            riga for riga in re.findall(r"^\{.*\}$", prompt, re.MULTILINE) if '" | "' not in riga
        ]

        assert esempi, f"nessun esempio in {agent}"
        for esempio in esempi:
            json.loads(esempio)  # solleva se malformato


def test_loads_prompt_from_custom_directory(tmp_path: Path) -> None:
    agent_dir = tmp_path / "generation"
    agent_dir.mkdir()
    (agent_dir / "v2.md").write_text("Prompt sperimentale", encoding="utf-8")

    assert load_prompt("generation", "v2", tmp_path) == "Prompt sperimentale"


def test_rejects_missing_prompt(tmp_path: Path) -> None:
    with pytest.raises(PromptNotFoundError, match="file non trovato"):
        load_prompt("generation", "v99", tmp_path)


def test_rejects_empty_prompt(tmp_path: Path) -> None:
    agent_dir = tmp_path / "generation"
    agent_dir.mkdir()
    (agent_dir / "v1.md").write_text("   \n", encoding="utf-8")

    with pytest.raises(PromptNotFoundError, match="vuoto"):
        load_prompt("generation", "v1", tmp_path)


def test_prompts_do_not_leak_the_experimental_sample() -> None:
    """I prompt non devono contenere elementi delle PR del campione.

    Gli esempi nei prompt guidano il modello: se provenissero dalle stesse
    Pull Request su cui misuriamo i risultati, la valutazione sperimentale
    sarebbe contaminata (Decisione 3.7). Gli esempi devono restare inventati
    e indipendenti dal campione.
    """

    samples_dir = Path(__file__).parent.parent / "experiments" / "samples"
    identificatori: set[str] = set()

    for sample_file in samples_dir.glob("*.json"):
        for record in json.loads(sample_file.read_text(encoding="utf-8")):
            identificatori.add(record["repository"].split("/")[0].lower())
            testo = f"{record['title']} {record['body']}"
            # Nomi di modulo, funzioni e file citati nella PR.
            identificatori.update(
                match.lower() for match in re.findall(r"\b\w+\.(?:py|\w+\(\))", testo)
            )

    for agent in AGENTS:
        prompt = load_prompt(agent).lower()
        trovati = sorted(term for term in identificatori if term in prompt)

        assert not trovati, f"il prompt '{agent}' cita il campione: {trovati}"


def _extract_block(prompt: str, tag: str) -> str:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", prompt, re.DOTALL)
    assert match, f"blocco <{tag}> assente"
    return match.group(1).strip()


def test_all_prompts_share_an_identical_definitions_block() -> None:
    """I due agenti devono usare le stesse definizioni, parola per parola.

    Quando le nozioni di 'comportamento richiesto' e di 'evidenza' divergono,
    generatore e valutatore applicano criteri diversi allo stesso requisito e
    il ciclo di revisione non converge.
    """

    blocchi = {agent: _extract_block(load_prompt(agent), "definitions") for agent in AGENTS}

    assert len(set(blocchi.values())) == 1, "le definizioni divergono fra i prompt"


def test_both_prompts_state_that_a_name_is_not_evidence() -> None:
    """Il nome di un artefatto non fonda il suo comportamento (Decisione 3.1, §9.2).

    Il principio era già nelle definizioni ("your own knowledge of similar
    systems is not evidence"), ma nessun passo della procedura lo faceva
    scattare: un componente nominato veniva trattato come se l'evidenza ne
    descrivesse il comportamento, e cinque Pull Request equivalenti hanno
    ricevuto quattro esiti diversi. Il criterio deve restare esplicito, o torna
    a essere un principio che nessuno applica.
    """

    for agent in AGENTS:
        prompt = load_prompt(agent)

        # Estensione del removal test, nel blocco condiviso.
        assert "added or implemented" in prompt, agent
        assert "equally true of any system" in prompt, agent

    # Ciascun agente deve poi sapere che cosa farne.
    assert "only names an artefact" in load_prompt(GENERATION_AGENT)
    assert "nothing beneath the name" in load_prompt(ASSESSMENT_AGENT)


def test_assessment_procedure_steps_are_numbered_consecutively() -> None:
    """La procedura decide con il primo passo che scatta: l'ordine è sostanza.

    Un passo inserito senza rinumerare i successivi produce due passi con lo
    stesso numero, e il modello non ha più un ordine da seguire.
    """

    procedura = _extract_block(load_prompt(ASSESSMENT_AGENT), "procedure")
    numeri = [int(n) for n in re.findall(r"^(\d+)\.", procedura, re.MULTILINE)]

    assert numeri == list(range(1, len(numeri) + 1)), numeri


def test_the_procedure_hooks_the_comparison_with_historical_requirements() -> None:
    """La sezione esisteva ma nessun passo la faceva scattare.

    La procedura decide con il primo passo che si applica: un'istruzione che
    resta fuori da quell'elenco puo' essere semplicemente ignorata.
    """

    prompt = load_prompt(ASSESSMENT_AGENT)
    procedura = _extract_block(prompt, "procedure")

    assert "previously validated requirements were supplied" in procedura
    # Il confronto si riporta, non decide: l'esito resta quello dei passi.
    assert "does not change the outcome" in procedura
    # Nominare la Pull Request rende la segnalazione verificabile.
    assert "naming the Pull Request" in procedura


def test_resembling_an_earlier_requirement_is_not_a_defect() -> None:
    """Due Pull Request diverse possono legittimamente produrre lo stesso comportamento."""

    storici = _extract_block(load_prompt(ASSESSMENT_AGENT), "historical_requirements")

    assert "Never reject or ask for a revision merely because" in storici


def test_prompts_use_the_expected_structure() -> None:
    for agent in AGENTS:
        prompt = load_prompt(agent)

        for tag in ("role", "task", "definitions", "procedure", "examples", "output_format"):
            assert f"<{tag}>" in prompt and f"</{tag}>" in prompt, f"{agent}: manca <{tag}>"


def test_prompts_provide_several_diverse_examples() -> None:
    """La documentazione ufficiale raccomanda da 3 a 5 esempi variati."""

    for agent in AGENTS:
        esempi = re.findall(r"<example>", load_prompt(agent))

        assert len(esempi) >= 4, f"{agent}: solo {len(esempi)} esempi"
