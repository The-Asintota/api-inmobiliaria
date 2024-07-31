from django.db.models import Model, QuerySet
from faker import Faker


fake = Faker("es_CO")


def empty_queryset(model: Model) -> QuerySet:
    """
    This function returns an empty queryset for the given model.
    """

    return model.objects.none()
