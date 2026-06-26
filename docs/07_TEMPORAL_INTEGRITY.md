# Intégrité temporelle — règle suprême

## Invariant

Pour une prédiction à l'heure `T = prediction_time`, aucune entrée avec `available_at > T` ne peut être utilisée, directement ou indirectement.

**E005, E029–E031, E037–E039 sont des erreurs bloquantes.** Le build échoue si une feature peut lire une ligne future.

## Horodatages obligatoires

| Champ | Signification |
|---|---|
| `event_time` | Heure réelle de l'événement (coup de sifflet, but, etc.) |
| `observed_at` | Heure à laquelle le fournisseur a observé l'événement |
| `fetched_at` | Heure à laquelle notre système a récupéré la donnée |
| `available_at` | Heure à laquelle la donnée était exploitable pour une prédiction |
| `processed_at` | Heure à laquelle la normalisation canonique a été appliquée |
| `prediction_time` | Heure à laquelle la prédiction est produite (référence invariante) |

`available_at` est le champ pivot. Il doit toujours être `>= fetched_at` et `>= observed_at`.

## Règle AS OF

Toute feature, cote, lineup ou statistique utilisée dans une prédiction doit satisfaire :

```python
assert observation.available_at <= prediction_time, (
    f"TEMPORAL VIOLATION: {observation.provider_event_id} "
    f"available_at={observation.available_at} > prediction_time={prediction_time}"
)
```

Cette assertion doit être exécutée avant chaque calcul de feature et avant chaque inférence modèle.

## Règles spécifiques par type de donnée

### Statistiques cumulées
- Calculées en excluant le match cible (E039).
- Exemple correct : `SELECT AVG(goals_1h) FROM matches WHERE team_id = ? AND date < match_date`
- Exemple interdit : `SELECT AVG(goals_1h) FROM matches WHERE team_id = ?` ← inclut le match cible

### Lineups officielles (E038)
- Utilisables seulement si `available_at < prediction_time`.
- Lineup probable (`source = 'estimated'`) ≠ lineup officielle (`source = 'official'`).
- Si lineup officielle non disponible avant `prediction_time` → utiliser lineup probable ou `missing`.

### Cotes de marché (E037)
- Cote de clôture interdite si non disponible avant `prediction_time`.
- Utiliser `odds_snapshot_id` pointant vers un snapshot `as_of = prediction_time`.
- Cote stale (âge > seuil) → déclencher `NO_BET`.

### Normalisation et preprocessing (E031)
- `StandardScaler`, `MinMaxScaler`, et tout transformateur doivent être `fit` uniquement sur le train set.
- Le test set et les données de production ne doivent jamais alimenter un `fit`.

### Split d'évaluation (E029)
- Split toujours chronologique : `train < cutoff_date < validation < test`.
- Interdiction absolue de `train_test_split(shuffle=True)` sur données temporelles.

## Structure du Feature Store (AS OF)

```python
# Correct — AS OF semantics
def get_features(team_id: str, snapshot_time: datetime) -> FeatureVector:
    return db.query(
        """
        SELECT *
        FROM feature_snapshots
        WHERE team_id = :team_id
          AND available_at <= :snapshot_time
        ORDER BY available_at DESC
        LIMIT 1
        """,
        team_id=team_id,
        snapshot_time=snapshot_time,
    )

# INTERDIT — lit le futur
def get_features_wrong(team_id: str) -> FeatureVector:
    return db.query("SELECT * FROM feature_snapshots WHERE team_id = :team_id ORDER BY available_at DESC LIMIT 1", ...)
```

## Tests adversariaux obligatoires

### tests/temporal/test_as_of_guard.py

```python
import pytest
from datetime import datetime, timezone

def test_no_future_feature_in_snapshot(db, prediction_time):
    """E005, E029 — Aucune feature avec available_at > prediction_time."""
    snapshot = FeatureStore.get_snapshot(prediction_time=prediction_time)
    for field_name, observation in snapshot.observations.items():
        assert observation.available_at <= prediction_time, (
            f"TEMPORAL VIOLATION: field '{field_name}' "
            f"available_at={observation.available_at} > prediction_time={prediction_time}"
        )

def test_no_official_lineup_before_announcement(db):
    """E038 — Lineup officielle pas utilisée avant publication officielle."""
    pre_announcement_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    lineup = LineupFetcher.get_as_of(match_id="test_match", as_of=pre_announcement_time)
    assert lineup.source != "official", "Lineup officielle utilisée avant annonce"

def test_odds_snapshot_is_pre_match(db):
    """E037 — Cote de clôture non utilisée avant fermeture du marché."""
    snapshot = OddsStore.get_snapshot(match_id="test_match", as_of=prediction_time)
    assert snapshot.timestamp <= prediction_time

def test_cumulative_stats_exclude_target_match(db):
    """E039 — Statistiques cumulées excluent le match cible."""
    stats = StatsFetcher.get_team_avg_goals_1h(
        team_id="team_a",
        before_date=match_date,
    )
    assert "target_match" not in stats.match_ids_included

def test_split_is_chronological():
    """E029 — Split temporel chronologique obligatoire."""
    train, val, test = DataSplitter.split(dataset=historical_matches)
    assert train.max_date < val.min_date
    assert val.max_date < test.min_date

def test_scaler_fit_only_on_train():
    """E031 — Normalisation apprise uniquement sur le train."""
    scaler = TemporalScaler()
    scaler.fit(train_data)
    # Le scaler ne doit pas avoir vu les données test
    assert scaler.fitted_on == "train_only"
    assert not scaler.saw_validation
    assert not scaler.saw_test
```

### Gate CI bloquante

Le job `temporal-gate` dans `.github/workflows/ci.yml` doit exécuter `pytest tests/temporal -x --tb=short` et échouer si un seul test temporel rate. Ce gate est obligatoire avant toute merge en production.

## Stockage de provenance

Chaque prédiction stocke les observations exactes utilisées :

```json
{
  "prediction_id": "pred_01HG...",
  "prediction_time": "2026-06-26T14:00:00Z",
  "feature_snapshot_id": "fs_01HG...",
  "observations_used": [
    {
      "field": "team_a_avg_goals_1h",
      "provider": "provider_x",
      "available_at": "2026-06-25T18:00:00Z",
      "raw_hash": "sha256:abc123..."
    }
  ]
}
```

Cette structure permet de rejouer la prédiction à partir du `prediction_id` et de vérifier que toutes les `available_at` étaient bien `<= prediction_time`.

## Erreurs bloquantes couvertes

| Erreur | Description | Gate |
|---|---|---|
| E005 | Mauvaise synchronisation temporelle | `test_no_future_feature_in_snapshot` |
| E029 | Split aléatoire temporel | `test_split_is_chronological` |
| E030 | Même dataset pour réglage et évaluation | Séparation `fit/transform` obligatoire |
| E031 | Prétraitement sur tout le dataset | `test_scaler_fit_only_on_train` |
| E037 | Cote de clôture utilisée trop tôt | `test_odds_snapshot_is_pre_match` |
| E038 | Lineup officielle trop tôt | `test_no_official_lineup_before_announcement` |
| E039 | Statistiques incluant le match cible | `test_cumulative_stats_exclude_target_match` |
