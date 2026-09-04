STATIC_PAGES = [
    ("/", "home page"),
    ("/landing-page", "landing page"),
    ("/accessibility-statement", "accessibility statement"),
    ("/cookies", "cookies page"),
    ("/guests/", "guests list"),
    ("/sponsors/", "sponsors list"),
    ("/accommodations/", "accommodations list"),
    ("/accommodation-requests/", "accommodation requests list"),
    ("/applications-to-sponsor-a-child/", "applications to sponsor a child list"),
    ("/visa-applications/", "visa applications list"),
    ("/visa-applications/visa-information-requests", "visa information requests list"),
    ("/downloads/", "downloads page"),
    ("/reassignment-requests/made/", "reassignment requests made"),
    ("/reassignment-requests/received/", "reassignment requests received"),
    ("/deduplication/", "deduplication start page"),
    ("/deduplication/sponsors/", "sponsor deduplication wizard"),
    ("/deduplication/accommodations/", "accommodation deduplication wizard"),
    ("/deduplication/guests/", "guest deduplication wizard"),
    ("/user-management/request-access/intro", "request access intro"),
    ("/user-management/request-access", "request access form"),
]

# Pages a local authority user cannot access. Scanned only when
# BROWSER_TEST_USER_TYPE=admin, for running locally against an admin user;
# the shared dev browser test user is a local authority user.
ELEVATED_ACCESS_PAGES = [
    ("/unassigned-accommodation-requests/", "unassigned accommodation requests list"),
    ("/safeguarding/escalated_checks", "escalated checks"),
    ("/user-management/users", "manage people"),
    ("/user-management/groups", "manage groups"),
    ("/user-management/access-requests", "manage access requests"),
]

RECORD_LIST_PAGES = [
    ("/guests/", "guest"),
    ("/sponsors/", "sponsor"),
    ("/accommodations/", "accommodation"),
    ("/accommodation-requests/", "accommodation request"),
    ("/applications-to-sponsor-a-child/", "application to sponsor a child"),
    ("/visa-applications/", "visa application"),
]

NOT_SCANNABLE = {
    "/auth_callback",
    "/csp-report/",
    "/favicon.ico",
    "/login",
    "/logout",
    "/accommodations/postcode-search",
    "/safeguarding/escalated_checks/download",
    "/user-management/confirmation",
}
