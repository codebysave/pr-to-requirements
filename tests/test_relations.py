"""Le relazioni fra un requisito e quelli già in memoria.

Un duplicato e una contraddizione hanno esiti opposti per chi legge, ma lo
stesso trattamento nel sistema: entrambi vengono **accettati e registrati**.

Accettati, perché il candidato è giudicato rispetto alla propria evidenza: se
due Pull Request portano legittimamente allo stesso comportamento, rifiutare la
seconda significherebbe dire che non contiene alcun requisito, e sarebbe falso.
E una contraddizione può essere il requisito *nuovo* che sostituisce il vecchio:
rifiutandolo si conserverebbe quello superato.

Registrati, perché è l'unico modo in cui una persona può ritrovarli. Prima di
questa aggiunta il valutatore riconosceva i duplicati e lo diceva a parole,
mentre la tabella predisposta a contenerli restava vuota.
"""

from __future__ import annotations

from typing import Any, Sequence

import pytest

from are.agents.llm_agents import LLMRequirementAssessor, _relation_claims
from are.agents.state import RelationClaim, RelationKind, RetrievedRequirement
from are.db import IN_MEMORY, SqliteRequirementRepository
from are.input import PullRequestRecord
from are.llm import LLMResponse

RUN_ID = "20260831T200000Z"


def pr(
    pr_number: int = 6880,
    timestamp: str = "2025-06-01T10:00:00Z",
    repository: str = "owner/repo",
) -> PullRequestRecord:
    return PullRequestRecord.from_mapping(
        {
            "id": f"{repository.replace('/', '-')}-pr-{pr_number}",
            "repository": repository,
            "pr_number": pr_number,
            "timestamp": timestamp,
            "title": "Fix the export",
            "body": "The export button did nothing. This restores the download.",
        }
    )


def storico(requirement_id: str = "1", numero: int = 6870) -> RetrievedRequirement:
    return RetrievedRequirement(
        requirement_id=requirement_id,
        statement="The system shall export the report.",
        source_pr_number=numero,
    )


@pytest.fixture
def repository() -> SqliteRequirementRepository:
    with SqliteRequirementRepository(IN_MEMORY, RUN_ID) as repo:
        yield repo


# -- lettura della dichiarazione del modello ------------------------------


def test_a_declared_relation_becomes_a_claim():
    dati = {
        "relations": [
            {"type": "DUPLICATE", "source_pr_number": 6870, "reason": "same behaviour"}
        ]
    }
    dichiarate = _relation_claims(dati, (storico("42", 6870),), "{}")

    assert len(dichiarate) == 1
    assert dichiarate[0].kind is RelationKind.DUPLICATE
    assert dichiarate[0].target_requirement_id == "42"
    assert dichiarate[0].target_pr_number == 6870
    assert dichiarate[0].reason == "same behaviour"


def test_the_identifier_comes_from_the_memory_not_from_the_model():
    """Il modello dichiara il numero della Pull Request, che ha visto; la
    chiave della riga la risolve il codice. Così una relazione non può puntare
    a un identificativo inventato."""

    dati = {"relations": [{"type": "CONFLICTS", "source_pr_number": 6870, "reason": "x"}]}
    dichiarate = _relation_claims(dati, (storico("99", 6870),), "{}")

    assert dichiarate[0].target_requirement_id == "99"


@pytest.mark.parametrize(
    "tipo",
    ["DUPLICATE", "OVERLAPS", "REFINES", "SUPERSEDES", "CONFLICTS"],
)
def test_every_kind_of_the_taxonomy_is_accepted(tipo: str):
    dati = {"relations": [{"type": tipo, "source_pr_number": 6870, "reason": ""}]}
    assert _relation_claims(dati, (storico(),), "{}")[0].kind == RelationKind(tipo)


def test_a_lowercase_type_is_accepted():
    dati = {"relations": [{"type": "duplicate", "source_pr_number": 6870, "reason": ""}]}
    assert _relation_claims(dati, (storico(),), "{}")[0].kind is RelationKind.DUPLICATE


def test_no_relations_field_means_none_declared():
    assert _relation_claims({"decision": "ACCEPT"}, (storico(),), "{}") == ()


# -- cosa viene scartato --------------------------------------------------


def test_a_relation_to_a_pull_request_never_shown_is_discarded():
    """Il modello non può aver osservato un requisito che non ha ricevuto:
    l'affermazione non sarebbe verificabile."""

    dati = {"relations": [{"type": "DUPLICATE", "source_pr_number": 9999, "reason": "x"}]}
    assert _relation_claims(dati, (storico("1", 6870),), "{}") == ()


def test_a_type_outside_the_taxonomy_is_discarded():
    """Il database vincola i valori ammessi: uno diverso farebbe fallire la
    scrittura del requisito, che invece è già stato validato."""

    dati = {"relations": [{"type": "SIMILAR", "source_pr_number": 6870, "reason": "x"}]}
    assert _relation_claims(dati, (storico(),), "{}") == ()


def test_a_malformed_entry_is_skipped_without_raising():
    """Perdere un requisito validato per un campo scritto male sarebbe
    sproporzionato: una relazione è un'informazione aggiuntiva."""

    dati = {"relations": ["non è un oggetto", {"type": "DUPLICATE", "source_pr_number": 6870}]}
    dichiarate = _relation_claims(dati, (storico(),), "{}")

    assert len(dichiarate) == 1
    assert dichiarate[0].reason == ""


def test_a_relations_field_that_is_not_a_list_is_an_error():
    """Qui invece il contratto è violato in modo strutturale, non in una voce."""

    with pytest.raises(Exception, match="relations"):
        _relation_claims({"relations": "DUPLICATE"}, (storico(),), "{}")


# -- persistenza ----------------------------------------------------------


def test_a_relation_is_written_next_to_the_requirement(repository):
    repository.store_accepted(pr(pr_number=6870, timestamp="2025-01-01T10:00:00Z"), "Il primo.")
    primo = repository.list_requirements()[0]

    repository.store_accepted(
        pr(pr_number=6880),
        "Il secondo.",
        (
            RelationClaim(
                kind=RelationKind.DUPLICATE,
                target_requirement_id=str(primo.id),
                target_pr_number=6870,
                reason="stesso comportamento",
            ),
        ),
    )

    secondo = repository.list_requirements()[1]
    relazioni = repository.get_relations(secondo.id)
    assert len(relazioni) == 1
    assert relazioni[0].source_requirement_id == secondo.id
    assert relazioni[0].target_requirement_id == primo.id
    assert relazioni[0].relation_type.value == "DUPLICATE"


def test_the_requirement_is_stored_even_when_a_relation_is_unusable(repository):
    """Il requisito ha superato la valutazione: va conservato comunque. Una
    relazione verso una riga inesistente viene scartata con un avviso."""

    repository.store_accepted(
        pr(),
        "Il requisito.",
        (
            RelationClaim(
                kind=RelationKind.CONFLICTS,
                target_requirement_id="9999",
                target_pr_number=1,
                reason="x",
            ),
        ),
    )

    assert repository.count() == 1
    assert repository.get_relations(repository.list_requirements()[0].id) == []


def test_several_relations_can_be_written_for_one_requirement(repository):
    for numero, giorno in ((6870, "01"), (6879, "02")):
        repository.store_accepted(
            pr(pr_number=numero, timestamp=f"2025-{giorno}-01T10:00:00Z"), f"R{numero}."
        )
    esistenti = repository.list_requirements()

    repository.store_accepted(
        pr(pr_number=6880),
        "Il terzo.",
        tuple(
            RelationClaim(
                kind=RelationKind.OVERLAPS,
                target_requirement_id=str(r.id),
                target_pr_number=r.source_pr_number,
                reason="",
            )
            for r in esistenti
        ),
    )

    nuovo = repository.list_requirements()[-1]
    assert len(repository.get_relations(nuovo.id)) == 2


def test_storing_without_relations_still_works(repository):
    """Il caso di gran lunga più frequente: nessuna relazione osservata."""

    repository.store_accepted(pr(), "Il requisito.")
    assert repository.count() == 1
    assert repository.get_relations(repository.list_requirements()[0].id) == []


# -- il valutatore le dichiara --------------------------------------------


class ClientFinto:
    def __init__(self, testo: str) -> None:
        self._testo = testo
        self.chiamate: list[dict[str, Any]] = []

    def complete(self, *, system: str, user_message: str) -> LLMResponse:
        self.chiamate.append({"system": system, "user_message": user_message})
        return LLMResponse(
            text=self._testo,
            model="finto",
            stop_reason="end_turn",
            input_tokens=0,
            output_tokens=0,
        )


def valuta(risposta: str, storici: Sequence[RetrievedRequirement] = ()):
    client = ClientFinto(risposta)
    assessor = LLMRequirementAssessor(client, "v1")  # type: ignore[arg-type]
    return assessor.assess(pr(), "Il candidato.", storici, (), None)


def test_the_assessment_carries_the_declared_relations():
    esito = valuta(
        '{"decision": "ACCEPT", "issues": [], "unsupported_claims": [], '
        '"missing_information": [], "revision_instructions": [], '
        '"relations": [{"type": "CONFLICTS", "source_pr_number": 6870, '
        '"reason": "opposite obligations"}]}',
        (storico("7", 6870),),
    )

    assert esito.relations[0].kind is RelationKind.CONFLICTS
    assert esito.relations[0].target_requirement_id == "7"


def test_a_contradiction_does_not_change_the_verdict():
    """Il candidato può essere il requisito nuovo che sostituisce il vecchio:
    rifiutarlo conserverebbe quello superato."""

    esito = valuta(
        '{"decision": "ACCEPT", "issues": [], "unsupported_claims": [], '
        '"missing_information": [], "revision_instructions": [], '
        '"relations": [{"type": "CONFLICTS", "source_pr_number": 6870, "reason": "x"}]}',
        (storico("7", 6870),),
    )

    assert esito.decision.value == "ACCEPT"
    assert len(esito.relations) == 1


def test_an_assessment_without_relations_carries_none():
    esito = valuta(
        '{"decision": "ACCEPT", "issues": [], "unsupported_claims": [], '
        '"missing_information": [], "revision_instructions": []}'
    )
    assert esito.relations == ()


# -- i prompt le chiedono -------------------------------------------------


@pytest.mark.parametrize("versione", ["v1", "v2"])
def test_both_prompts_describe_the_taxonomy(versione: str):
    from are.agents.prompts import load_prompt

    testo = load_prompt("assessment", versione)
    for tipo in ("DUPLICATE", "OVERLAPS", "REFINES", "SUPERSEDES", "CONFLICTS"):
        assert tipo in testo, f"{versione} non descrive {tipo}"


@pytest.mark.parametrize("versione", ["v1", "v2"])
def test_both_prompts_single_out_the_contradiction(versione: str):
    """È l'unica relazione che segnala un difetto dell'insieme, e il modello
    deve sapere che non va usata per «dice qualcosa di diverso»."""

    from are.agents.prompts import load_prompt

    assert "cannot both be true" in load_prompt("assessment", versione)
