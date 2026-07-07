from django.http import HttpRequest
from django.urls import ResolverMatch


def get_title(request: HttpRequest, service_name: str) -> str:
    # We need resolver match to build the title
    # If not present, we default to Service Name only
    if request.resolver_match is None:
        return service_name

    # Resolver match contains route and app name info
    resolver_match = request.resolver_match

    # Quick return for Home page
    if is_home_page(resolver_match):
        return service_name

    # Title composition
    # [Section Title]:[Record Name][, Tab Title] - Service Name
    # e.g. Guest: Full Name of Guest, Overview - Share Homes for Ukraine data

    # Build title step by step
    title = ""
    title = apply_section_title(title, resolver_match)
    title = apply_record_name(title, request)
    title = apply_tab_title(title, resolver_match)
    title = apply_service_name(title, service_name)

    return title


def apply_section_title(title: str, resolver_match: ResolverMatch) -> str:
    section_title = get_section_title(resolver_match)

    if section_title:
        return f"{section_title}"

    return title


def apply_record_name(title: str, request: HttpRequest) -> str:
    record_name = getattr(request, "record_name", None)

    if record_name:
        short_record_name = get_short_record_name(str(record_name))

        if ":" not in title:
            title = f"{title}: {short_record_name}"
        else:
            title += f"{short_record_name}"

    return title


def apply_tab_title(title: str, resolver_match: ResolverMatch) -> str:
    tab_title = get_tab_title(resolver_match)

    if tab_title:
        if ":" not in title:
            title = f"{title}: {tab_title}"
        else:
            title = f"{title}, {tab_title}"

    return title


def apply_service_name(title: str, service_name: str) -> str:
    if title:
        return f"{title} - {service_name}"

    return service_name


def get_section_title(resolver_match: ResolverMatch) -> str:
    TITLE_MAP = {
        "sponsors": "Sponsors and hosts",
        "download": "Download data",
        "safeguarding": "Escalated checks",
        "uams": "UAMs",
        "user-management": "Request access",
    }

    app_name = resolver_match.app_name

    # overrides for specific user-management pages
    if app_name == "user-management":
        if resolver_match.url_name == "access-request-details":
            return "Review access request"
        elif resolver_match.url_name == "user-details":
            return "User account"
        elif resolver_match.url_name == "group-details":
            return "Group details"

    if app_name in TITLE_MAP:
        return TITLE_MAP[app_name]

    # webapp.routes will act as section titles
    if app_name == "webapp":
        app_name = resolver_match.route

    return slug_to_title(app_name)


def get_tab_title(resolver_match: ResolverMatch) -> str:
    TAB_MAP = {
        "ListView": "List view",
        "Overview": "Overview",
        "Properties": "Properties",
        "LinkedRecords": "Linked records",
        "Actions": "Actions",
        "History": "History",
        "VIRView": "Visa Information Request",
        "CommentsView": "Comments",
        "SafeguardingChecksView": "Safeguarding checks",
        "MadePageView": "Requests made",
        "ReceivedPageView": "Requests received",
        "FilesView": "Files",
        "CentralSafeguarding": "Central safeguarding",
    }

    func_path = resolver_match._func_path

    for key, value in TAB_MAP.items():
        if key in func_path:
            return value

    return ""


def is_home_page(resolver_match: ResolverMatch) -> bool:
    return resolver_match.route == "landing-page"


def slug_to_title(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").capitalize()


def get_short_record_name(record_name: str, max_length: int = 20) -> str:
    if len(record_name) <= max_length:
        return record_name

    return record_name[: max_length - 3] + "..."
