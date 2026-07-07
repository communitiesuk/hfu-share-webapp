VISA_STATUS_LIST = [
    "Refused",
    "Issued",
    "Missing Application",
    "Lapsed",
    "Confirmed",
    "Pending",
    "Arrived",
    "Withdrawn",
    "Flow Visa Pending",
]

# LTLA names for seeding - organized by country with weighted selection
WELSH_LTLA_NAMES = [
    "Cardiff",
    "Swansea",
    "Newport",
]

NORTHERN_IRELAND_LTLA_NAMES = [
    "Belfast",
    "Antrim and Newtownabbey",
    "Lisburn and Castlereagh",
]

SCOTTISH_LTLA_NAMES = [
    "Aberdeen City",
    "Dundee City",
    "City of Edinburgh",
    "Glasgow City",
    "Stirling",
]

# English LAs with favored ones (Bromley, Lewisham, Croydon weighted)
ENGLISH_LTLA_NAMES = [
    "Bromley",  # Favored
    "Lewisham",  # Favored
    "Croydon",  # Favored
    "Birmingham",
    "Manchester",
    "Liverpool",
    "Leeds",
    "Sheffield",
    "Newcastle upon Tyne",
    "Nottingham",
    "Leicester",
    "Bristol, City of",
    "Bromley",  # Appears again for weighting
    "Lewisham",  # Appears again for weighting
    "Croydon",  # Appears again for weighting
]

# Combined list for random selection
ALL_LTLA_NAMES = (
    WELSH_LTLA_NAMES
    + NORTHERN_IRELAND_LTLA_NAMES
    + SCOTTISH_LTLA_NAMES
    + ENGLISH_LTLA_NAMES
)
