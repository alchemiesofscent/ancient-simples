import csv
import os
import pytest

# Path to the lemmata CSV in the data-workbench
LEMMATA_CSV = os.path.join(
    os.path.dirname(__file__), "..", "data-workbench", "lemmata.csv"
)

# First 55 unique headword_gr values from lemmata.csv
GREEK_HEADWORDS = [
    "\u1f00\u03b2\u03c1\u03cc\u03c4\u03bf\u03bd\u03bf\u03bd",       # L001 ἀβρότονον
    "\u1f04\u03b3\u03bd\u03bf\u03c2",                                 # L002 ἄγνος
    "\u03bb\u03cd\u03b3\u03bf\u03c2",                                 # L003 λύγος
    "\u1f04\u03b3\u03c1\u03c9\u03c3\u03c4\u03b9\u03c2",             # L004 ἄγρωστις
    "\u1f04\u03b3\u03c7\u03bf\u03c5\u03c3\u03b1",                   # L005 ἄγχουσα
    "\u1f40\u03bd\u03cc\u03ba\u03bb\u03b5\u03b9\u03b1",             # L006 ὀνόκλεια
    "\u03bb\u03cd\u03ba\u03bf\u03c8\u03b9\u03c2",                   # L007 λύκοψις
    "\u1f40\u03bd\u03cc\u03c7\u03b5\u03b9\u03bb\u03bf\u03c2",       # L008 ὀνόχειλος
    "\u1f00\u03bb\u03ba\u03b9\u03b2\u03b9\u03ac\u03b4\u03b5\u03b9\u03bf\u03bd",  # L009 ἀλκιβιάδειον
    "\u1f00\u03b3\u03b1\u03c1\u03b9\u03ba\u03cc\u03bd",             # L010 ἀγαρικόν
    "\u1f00\u03b3\u03ae\u03c1\u03b1\u03c4\u03bf\u03bd",             # L011 ἀγήρατον
    "\u1f00\u03b4\u03af\u03b1\u03bd\u03c4\u03bf\u03bd",             # L012 ἀδίαντον
    "\u1f00\u03b5\u03af\u03b6\u03c9\u03bf\u03bd",                   # L013 ἀείζωον
    "\u1f00\u03b5\u03af\u03b6\u03c9\u03bf\u03bd \u03c4\u1f78 \u03bc\u03ad\u03b3\u03b1",  # L014 ἀείζωον τὸ μέγα
    "\u1f00\u03b5\u03af\u03b6\u03c9\u03bf\u03bd \u03c4\u1f78 \u03bc\u03b9\u03ba\u03c1\u03cc\u03bd",  # L015 ἀείζωον τὸ μικρόν
    "\u03b1\u1f30\u03b3\u03af\u03bb\u03c9\u03c8",                   # L016 αἰγίλωψ
    "\u03b1\u1f36\u03c1\u03b1",                                       # L017 αἶρα
    "\u03b1\u1f34\u03b3\u03b5\u03b9\u03c1\u03bf\u03c2",             # L018 αἴγειρος
    "\u1f00\u03ba\u03b1\u03ba\u03af\u03b1",                         # L019 ἀκακία
    "\u1f00\u03ba\u03b1\u03bb\u03cd\u03c6\u03b7",                   # L020 ἀκαλύφη
    "\u1f04\u03ba\u03b1\u03bd\u03b8\u03bf\u03c2",                   # L021 ἄκανθος
    "\u03bc\u03b5\u03bb\u03ac\u03bc\u03c6\u03c5\u03bb\u03bb\u03bf\u03c2",  # L022 μελάμφυλλος
    "\u03c0\u03b1\u03b9\u03b4\u03ad\u03c1\u03c9\u03c4\u03b1",       # L023 παιδέρωτα
    "\u1f00\u03ba\u03ac\u03bd\u03b8\u03b9\u03bf\u03bd",             # L024 ἀκάνθιον
    "\u1f04\u03ba\u03b1\u03bd\u03b8\u03b1 \u03bb\u03b5\u03c5\u03ba\u03ae",  # L025 ἄκανθα λευκή
    "\u03bb\u03b5\u03c5\u03ba\u03ac\u03ba\u03b1\u03bd\u03b8\u03bf\u03c2",  # L026 λευκάκανθος
    "\u1f04\u03ba\u03b1\u03bd\u03b8\u03b1 \u0391\u1f30\u03b3\u03c5\u03c0\u03c4\u03af\u03b1",  # L027 ἄκανθα Αἰγυπτία
    "\u1f04\u03ba\u03b1\u03bd\u03b8\u03b1 \u1f08\u03c1\u03b1\u03b2\u03b9\u03ba\u03ae",  # L028 ἄκανθα Ἀραβική
    "\u1f04\u03ba\u03bf\u03c1\u03bf\u03bd",                         # L029 ἄκορον
    "\u1f00\u03ba\u03cc\u03bd\u03b9\u03c4\u03bf\u03bd",             # L030 ἀκόνιτον
    "\u03c0\u03b1\u03c1\u03b4\u03b1\u03bb\u03b9\u03b1\u03b3\u03c7\u03ad\u03c2",  # L031 παρδαλιαγχές
    "\u03bb\u03c5\u03ba\u03bf\u03ba\u03c4\u03cc\u03bd\u03bf\u03bd",  # L032 λυκοκτόνον
    "\u1f00\u03ba\u03c4\u03ae",                                       # L033 ἀκτή
    "\u1f04\u03ba\u03c4\u03b7 \u1f21 \u03bc\u03b5\u03b3\u03ac\u03bb\u03b7",  # L034 ἄκτη ἡ μεγάλη
    "\u03b4\u03b5\u03bd\u03b4\u03c1\u03ce\u03b4\u03b7\u03c2",       # L035 δενδρώδης
    "\u1f04\u03ba\u03c4\u03b7 \u1f21 \u03b2\u03bf\u03c4\u03b1\u03bd\u03c9\u03b4\u03b5\u03c3\u03c4\u03ad\u03c1\u03b1",  # L036
    "\u1f04\u03ba\u03c4\u03b7 \u03c7\u03b1\u03bc\u03b1\u03b9\u03ac\u03ba\u03c4\u03b7\u03bd",  # L037 ἄκτη χαμαιάκτην
    "\u1f05\u03bb\u03b9\u03bc\u03bf\u03bd",                         # L038 ἅλιμον
    "\u1f00\u03bb\u03cc\u03b7",                                       # L039 ἀλόη
    "\u1f04\u03bb\u03c5\u03c3\u03c3\u03bf\u03bd",                   # L040 ἄλυσσον
    "\u1f00\u03bb\u03c3\u03af\u03bd\u03b7",                         # L041 ἀλσίνη
    "\u03bc\u03c5\u1f78\u03c2 \u1f66\u03c4\u03b1",                   # L042 μυὸς ὦτα
    "\u1f00\u03bc\u03ac\u03c1\u03b1\u03ba\u03bf\u03bd",             # L043 ἀμάρακον
    "\u1f00\u03bc\u03b2\u03c1\u03bf\u03c3\u03af\u03b1",             # L044 ἀμβροσία
    "\u1f04\u03bc\u03b9",                                             # L045 ἄμι
    "\u1f00\u03bc\u03ac\u03c1\u03b1\u03bd\u03c4\u03bf\u03bd",       # L046 ἀμάραντον
    "\u1f00\u03bc\u03cc\u03c1\u03b3\u03b7",                         # L047 ἀμόργη
    "\u1f00\u03bc\u03c0\u03b5\u03bb\u03cc\u03c0\u03c1\u03b1\u03c3\u03bf\u03bd",  # L048 ἀμπελόπρασον
    "\u1f04\u03bc\u03c0\u03b5\u03bb\u03bf\u03c2 \u1f04\u03b3\u03c1\u03b9\u03b1",  # L049 ἄμπελος ἄγρια
    "\u1f04\u03bc\u03c0\u03b5\u03bb\u03bf\u03c2 \u1f25\u03bc\u03b5\u03c1\u03bf\u03c2",  # L050 ἄμπελος ἥμερος
    "\u1f04\u03bc\u03c0\u03b5\u03bb\u03bf\u03c2 \u03bb\u03b5\u03c5\u03ba\u03ae",  # L051 ἄμπελος λευκή
    "\u03b2\u03c1\u03c5\u03c9\u03bd\u03af\u03b1",                   # L052 βρυωνία
    "\u03c8\u03af\u03bb\u03c9\u03b8\u03c1\u03bf\u03bd",             # L053 ψίλωθρον
    "\u1f04\u03bc\u03c0\u03b5\u03bb\u03bf\u03c2 \u03bc\u03ad\u03bb\u03b1\u03b9\u03bd\u03b1",  # L054 ἄμπελος μέλαινα
    "\u1f00\u03bc\u03cd\u03b3\u03b4\u03b1\u03bb\u03b1",             # L055 ἀμύγδαλα
]


@pytest.fixture
def greek_headwords():
    """Return list of 55 Greek headwords from lemmata.csv for parity testing."""
    return list(GREEK_HEADWORDS)


@pytest.fixture
def lemmata_csv_path():
    """Return the path to the lemmata CSV file."""
    return LEMMATA_CSV
