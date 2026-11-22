"""Guards the identity/health separation described in docs/architecture.

Health-side apps hold a subject_id and nothing that points at a person. If one of them
ever adds a foreign key to User, Subject or SubjectLink, these tests fail.
"""

from django.apps import apps
from django.db import models

HEALTH_SIDE_APPS = {
    "health_records",
    "data_ingestion",
    "evaluations",
    "conversations",
    "ai_gateway",
}
IDENTITY_MODELS = {"User", "Subject", "SubjectLink"}


def find_violations(model_classes):
    """Relations from a health-side model to an identity model, as readable strings."""
    found = []
    for model in model_classes:
        if model._meta.app_label not in HEALTH_SIDE_APPS:
            continue
        for field in model._meta.get_fields():
            related = getattr(field, "related_model", None)
            if related is None or not field.is_relation:
                continue
            if related._meta.app_label == "identity" and related.__name__ in IDENTITY_MODELS:
                found.append(f"{model._meta.label}.{field.name} -> {related._meta.label}")
    return found


def test_health_side_apps_do_not_reference_identity_models():
    assert find_violations(apps.get_models()) == []


def test_detector_catches_a_violation():
    # Proves the guard works, so a passing test above is not just an empty scan.
    from apps.identity.models import User

    class Leaky(models.Model):
        owner = models.ForeignKey(User, on_delete=models.CASCADE)

        class Meta:
            app_label = "health_records"
            managed = False

        def __str__(self):
            return "leaky"

    try:
        assert find_violations([Leaky]) == ["health_records.Leaky.owner -> identity.User"]
    finally:
        apps.all_models["health_records"].pop("leaky", None)
        apps.clear_cache()


def test_health_side_app_labels_exist():
    labels = {config.label for config in apps.get_app_configs()}
    assert HEALTH_SIDE_APPS <= labels
