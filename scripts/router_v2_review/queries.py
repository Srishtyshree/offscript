"""v2.1 search-query review: every SEARCH query uses only places and names from its own row.

The v2 draft added cities, full official names and filler that the question never gave
("Lodhi Garden Delhi ... official", "Zakir Hussain Rose Garden"), and the tuned model learned to
invent places. Each family gets one keyword-style query below, then `faithful_query` drops any
capitalised word the row's own question or context does not contain, so a short wording such as
"national museum closing today" does not get "Delhi" added back.
"""

import re

# seed -> query written from the family's fullest wording (keywords only, no "of"/"in", so
# dropping a word never leaves a broken phrase).
QUERY_FIXES = {
    73: "Lodhi Garden opening hours Saturday",
    74: "National Museum Delhi closing time today",
    75: "Birla Planetarium Kolkata Monday opening hours",
    76: "Salar Jung Museum Hyderabad opening time tomorrow",
    77: "Cubbon Park step free entrance current",
    78: "Chennai museum wheelchair loan today",
    79: "Mehrangarh Fort current entry ticket price",
    80: "Chandigarh rose garden entry fee this weekend",
    81: "Fort Kochi public heritage walk Sunday meeting point",
    82: "Pune free outdoor film screening this week",
    83: "Jaipur open air craft market next date",
    84: "Guwahati public bird walk this weekend",
    85: "Mysuru community run this weekend starting point",
    86: "Indore outdoor art workshop next Saturday",
    87: "Ahmedabad public food festival this month start date",
    88: "Bengaluru public astronomy night this month",
    89: "Bhubaneswar park clean up next event location",
    90: "Lucknow public outdoor poetry reading Friday",
    91: "Sector 17 Chandigarh public badminton court hours this evening",
    92: "Kochi sports ground open football session schedule",
    93: "Noida public tennis court Saturday booking",
    94: "last metro Connaught Place tonight",
    95: "Elephanta Caves ferry tomorrow",
    96: "Panaji public beach bus last service tonight",
    97: "Pune rain forecast tomorrow morning",
    98: "Delhi air quality index today",
    99: "Jaipur heat warning today",
    100: "Ooty lakeside trail open to visitors",
    101: "Gangtok botanical garden public hours",
    102: "Visakhapatnam beach promenade closure today",
    103: "Panampilly Nagar farmers market Saturday hours",
    104: "Bhopal public book swap this weekend",
    105: "Aundh public pottery drop in tomorrow",
    106: "Patna public library Sunday hours",
    107: "latest AFC Asian Cup winner",
    108: "India cricket match yesterday final score",
    109: "ISL current standings",
    110: "Mumbai Marathon most recent winner",
    111: "National Human Rights Commission India current chairperson",
    112: "Election Commission India current head",
    113: "Pune current mayor",
    114: "Pune Lok Sabha constituency current representative",
    115: "Japanese yen rupee rate today",
    116: "Bengaluru petrol price today",
    117: "RBI repo rate latest",
    118: "restaurant food GST rate current",
    119: "CAT application deadline this year",
    120: "NPTEL next enrollment deadline",
    121: "NEET correction window open now",
    122: "SPPU BSc semester two result date",
    123: "Shillong rain forecast tomorrow afternoon",
    124: "Chennai temperature now",
    125: "Odisha cyclone alert today",
    126: "Delhi current air quality index",
    127: "Mumbai local train Central line delay today",
    128: "Bengaluru metro first train tomorrow",
    129: "Delhi airport express service status now",
    130: "India passport application fee current",
    131: "IIT Delhi attendance rule this semester",
    132: "voter registration required documents current",
    133: "GitHub outage now",
    134: "Python latest stable version",
    135: "WhatsApp security update this week",
    136: "Kho-Kho official rules standard match",
    137: "Onam Sadya traditional dishes",
    138: "Hindustani classical vocal concert typical instruments",
    "context-pair-5": "Pune reserve next public beginner bird walk time",
    "context-pair-6": "Pune public run club next session time meeting point",
    "context-pair-8": "Lalbagh Botanical Garden Bengaluru entry today",
    "context-pair-9": "Jaipur craft fair this weekend public venue",
    "context-pair-10": "National Museum Delhi visitor rules",
    213: "meteor shower visible India this month",
}

# Rows whose wording names the place or thing differently from the family's fullest wording.
ROW_QUERIES = {
    "v2-0467": "last metro Rajiv Chowk tonight",
    "v2-0468": "Delhi metro last train tonight",
    "v2-0470": "last metro Rajiv Chowk tonight",
    "v2-0553": "NHRC current chairperson",
    "v2-0558": "election commission current head",
    "v2-0568": "Pune current MP",
    "v2-0572": "JPY INR rate now",
    "v2-0573": "JPY INR rate now",
    "v2-0575": "JPY INR rate now",
}

FILLER = re.compile(
    r"\b(?:official|organizer|public listing|listing|reliable cultural source|reliable source)\b",
    re.IGNORECASE,
)


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def faithful_query(query: str, question: str, context: str = "") -> str:
    """Drop filler the row did not ask for, and capitalised words the row never gave."""
    source = _words(f"{question} {context}")
    query = FILLER.sub(lambda m: m.group(0) if _words(m.group(0)) <= source else "", query)
    kept = [
        token
        for token in query.split()
        if not token[0].isupper() or set(re.findall(r"[a-z0-9]+", token.lower())) <= source
    ]
    return " ".join(kept)
