import logging
import os

from django.contrib import admin


def is_empty_ltla(val):
    return (
        val is None
        or (isinstance(val, list) and len(val) == 0)
        or (isinstance(val, str) and val.strip() == "")
    )


def _fill_source_ltla_utla(obj):
    changed = False
    ltla_name = None
    utla_name = None
    # Strategy 1: Use source_country if populated
    if obj.source_country and len(obj.source_country) > 0:
        country = obj.source_country[0]
        if country == "Scotland":
            ltla_name = ["Aberdeen City"]
        elif country == "Wales":
            ltla_name = ["Cardiff"]
            utla_name = ["Cardiff"]
        elif country == "Northern Ireland":
            ltla_name = ["Belfast"]
            utla_name = ["Belfast"]
    # Strategy 2: Use viewer_groups if still missing
    if not ltla_name and obj.viewer_groups:
        ltl_names = [g.split("LTLA-")[-1] for g in obj.viewer_groups if "LTLA-" in g]
        dest_ltla = (
            obj.destination_ltla_name.strip() if obj.destination_ltla_name else None
        )
        ltl_names = [n for n in ltl_names if n and (not dest_ltla or n != dest_ltla)]
        if ltl_names:
            ltla_name = ltl_names
    if ltla_name:
        obj.source_ltla_name = ltla_name
        changed = True
    if utla_name:
        obj.source_utla_name = utla_name
        changed = True
    return changed


def _fill_destination_ltla_utla(obj):
    changed = False
    ltla_name = None
    utla_name = None
    # Strategy 1: Use destination_country if populated
    if obj.destination_country:
        country = obj.destination_country
        if country == "Scotland":
            ltla_name = "Aberdeen City"
        elif country == "Wales":
            ltla_name = "Cardiff"
            utla_name = "Cardiff"
        elif country == "Northern Ireland":
            ltla_name = "Belfast"
            utla_name = "Belfast"
    # Strategy 2: Use viewer_groups if still missing
    if not ltla_name and obj.viewer_groups:
        ltl_names = [g.split("LTLA-")[-1] for g in obj.viewer_groups if "LTLA-" in g]
        src_ltla = (
            obj.source_ltla_name[0]
            if obj.source_ltla_name and len(obj.source_ltla_name) > 0
            else None
        )
        ltl_names = [n for n in ltl_names if n and (not src_ltla or n != src_ltla)]
        if ltl_names:
            ltla_name = ltl_names[0]  # destination_ltla_name is a string
    if ltla_name:
        obj.destination_ltla_name = ltla_name
        changed = True
    if utla_name:
        obj.destination_utla_name = utla_name
        changed = True
    return changed


@admin.action(description="Fill missing LTLA/UTLA names on reassignment requests")
def fill_missing_ltla_utla(modeladmin, request, queryset):
    updated = 0
    skipped = 0
    not_updated_ids = []
    for obj in queryset:
        changed = False
        if is_empty_ltla(obj.source_ltla_name):
            changed |= _fill_source_ltla_utla(obj)
        if is_empty_ltla(obj.destination_ltla_name):
            changed |= _fill_destination_ltla_utla(obj)
        if changed:
            obj.save(
                update_fields=[
                    "source_ltla_name",
                    "destination_ltla_name",
                    "source_utla_name",
                    "destination_utla_name",
                ]
            )
            updated += 1
        else:
            skipped += 1
        # If either is still missing after attempts, collect ID
        if is_empty_ltla(obj.source_ltla_name) or is_empty_ltla(
            obj.destination_ltla_name
        ):
            not_updated_ids.append(str(getattr(obj, "id", obj.pk)))
    msg = (
        f"Checked {queryset.count()} record{'s' if queryset.count() != 1 else ''}. "
        f"Skipped {skipped} already filled record{'s' if skipped != 1 else ''}. "
        f"Updated {updated} record{'s' if updated != 1 else ''} with LTLA names."
    )
    if not_updated_ids:
        count = len(not_updated_ids)
        plural = "s" if count != 1 else ""
        failed_msg = (
            f"Could not update {count} record{plural} with missing LTLA, id{plural}: "
            f"{', '.join(not_updated_ids)}"
        )
        msg += f" {failed_msg}"
        logging.error("fill_missing_ltla_utla: %s", failed_msg)
    modeladmin.message_user(request, msg)


@admin.action(description="Normalise outcome values to new format")
def normalise_outcome_values(modeladmin, request, queryset):
    if os.environ.get("SENTRY_ENVIRONMENT") == "production":
        modeladmin.message_user(
            request, "You cannot run this action on production", level="error"
        )
        return
    mapping = {
        "ACCEPTED": "Accepted",
        "REJECTED": "Rejected",
        "PENDING": "Pending",
        "NEEDS_ACCOMMODATION_REQUEST": "Needs Accommodation Request",
    }
    updated = 0
    failed_ids = []
    for obj in queryset:
        if obj.outcome in mapping:
            obj.outcome = mapping[obj.outcome]
            try:
                obj.save(update_fields=["outcome"])
                updated += 1
            except Exception:
                failed_ids.append(str(getattr(obj, "id", obj.pk)))
    if updated == 0:
        msg = "No changes made"
    else:
        msg = f"Updated {updated} outcome value(s) to the new format"
    if failed_ids:
        msg += f" Failed to update IDs: {', '.join(failed_ids)}"
    modeladmin.message_user(request, msg)
