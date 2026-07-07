import uuid

from django.db import migrations

from accounts.enums import GroupType
from accounts.models import GroupInfo
from ontology.models import MvAccommodation, MvVolunteer

# Random uuid for namespace to use in host/accommodation uuid generation.
# Using this namespace so that uuids are generated in a deterministic way.
# Each accommodation/host created will have the same uuid every time this
# migration is run. Therefore, all environments will have the same uuid for
# each temporary ghost accommodation and LTLA host.
namespace = uuid.UUID("28e5b0b9-36e7-45bb-9cb4-0979e79c4916")


def create_ltla_host(ltla: GroupInfo, apps):
    Host = apps.get_model("ontology", "MvVolunteer")

    host_id = f"sponsor-{uuid.uuid5(namespace, ltla.ltla_name)}"
    host_name = f"[Local Authority] {ltla.ltla_name}"

    host = Host.objects.create(
        flag_unsuitable=False,
        full_name=host_name,
        id=host_id,
        is_available_for_rematch=True,
        is_eoi=False,
        is_principal=True,
        is_sponsor=True,
        source=["Local Authority list"],
        sponsor_type=MvVolunteer.SponsorType.LOCAL_AUTHORITY,
    )
    return host


def create_ltla_ghost_temporary_accommodation(ltla: GroupInfo, apps):
    Accommodation = apps.get_model("ontology", "MvAccommodation")

    accommodation_id = f"accommodation-{uuid.uuid5(namespace, ltla.ltla_name)}"
    address = f"Temporary Accommodation (Other) - [Local Authority] {ltla.ltla_name}"

    accommodation = Accommodation.objects.create(
        accommodation_type=MvAccommodation.AccommodationType.TEMPORARY_ACCOMMODATION,
        full_address=address,
        id=accommodation_id,
        is_accommodation=True,
        is_available_for_rematch=True,
        is_eoi=False,
        is_principal=True,
        local_authority=ltla.gss_code,
        ltla_name=ltla.ltla_name,
        utla_name=ltla.utla_name,
    )
    return accommodation


def create_ltla_hosts_and_ghost_temporary_accommodations(apps, schema_editor):
    ltla_group_infos = list(
        GroupInfo.objects.filter(group_type=GroupType.LOCAL_AUTHORITY).exclude(
            is_utla=True
        )
    )

    for ltla in ltla_group_infos:
        ltla_host = create_ltla_host(ltla, apps)
        ltla_accommodation = create_ltla_ghost_temporary_accommodation(ltla, apps)

        ltla_accommodation.hosts.add(ltla_host)


class Migration(migrations.Migration):
    dependencies = [
        (
            "ontology",
            "0035_alter_devcheckv2_ar_alter_devcheckv2_accommodation_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(create_ltla_hosts_and_ghost_temporary_accommodations)
    ]
