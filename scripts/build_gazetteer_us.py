"""One-off script: extend regions/us/gazetteer.us.jsonl with hand-curated
real US merchants, mapped to MCC/category via a small industry-keyword
table (each MCC verified against iso18245 at authoring time -- run
`python -c "import iso18245; print(iso18245.get_mcc('...'))"` before
adding a new industry keyword here).

ponytail: no CLI flags, no argparse -- edit MERCHANTS below and rerun.
Idempotent: skips any key already present in the gazetteer.
"""

import json
from pathlib import Path

INDUSTRY_TO_MCC_CATEGORY = {
    "car_rental": ("7512", "travel"),
    "clothing": ("5651", "general_merchandise"),
    "shoe": ("5661", "general_merchandise"),
    "sporting_goods": ("5941", "general_merchandise"),
    "toy": ("5945", "general_merchandise"),
    "bookstore": ("5942", "general_merchandise"),
    "florist": ("5992", "general_merchandise"),
    "convenience_store": ("5499", "food_and_drink"),
    "gym": ("7997", "personal_care"),
    "pet_store": ("5995", "general_merchandise"),
    "office_supplies": ("5943", "general_merchandise"),
    "furniture": ("5712", "general_merchandise"),
    "auto_parts": ("5533", "transportation"),
    "car_wash": ("7542", "transportation"),
    "parking": ("7523", "transportation"),
    "postal_shipping": ("4215", "general_services"),
    "insurance": ("6300", "general_services"),
    "utility": ("4900", "rent_and_utilities"),
    "hotel": ("7011", "travel"),
}

# (canonical name, industry keyword, [key variants])
MERCHANTS = [
    ("Hertz", "car_rental", ["hertz", "hertz rent a car"]),
    ("Enterprise Rent-A-Car", "car_rental", ["enterprise rent-a-car", "enterprise"]),
    ("Avis", "car_rental", ["avis", "avis rent a car"]),
    ("Budget Car Rental", "car_rental", ["budget car rental", "budget rent a car"]),
    ("Gap", "clothing", ["gap", "gap inc"]),
    ("Old Navy", "clothing", ["old navy"]),
    ("American Eagle", "clothing", ["american eagle", "american eagle outfitters"]),
    ("Banana Republic", "clothing", ["banana republic"]),
    ("Foot Locker", "shoe", ["foot locker", "footlocker"]),
    ("DSW", "shoe", ["dsw", "designer shoe warehouse"]),
    ("Dick's Sporting Goods", "sporting_goods", ["dicks sporting goods", "dick's sporting goods"]),
    ("Build-A-Bear Workshop", "toy", ["build-a-bear", "build a bear workshop"]),
    ("Barnes & Noble", "bookstore", ["barnes & noble", "barnes and noble"]),
    ("1-800-Flowers", "florist", ["1-800-flowers", "1800flowers"]),
    ("7-Eleven", "convenience_store", ["7-eleven", "7 eleven"]),
    ("Circle K", "convenience_store", ["circle k"]),
    ("Planet Fitness", "gym", ["planet fitness"]),
    ("LA Fitness", "gym", ["la fitness"]),
    ("PetSmart", "pet_store", ["petsmart"]),
    ("Petco", "pet_store", ["petco"]),
    ("Staples", "office_supplies", ["staples"]),
    ("Office Depot", "office_supplies", ["office depot"]),
    ("IKEA", "furniture", ["ikea"]),
    ("Ashley Furniture", "furniture", ["ashley furniture", "ashley homestore"]),
    ("AutoZone", "auto_parts", ["autozone"]),
    ("O'Reilly Auto Parts", "auto_parts", ["o'reilly auto parts", "oreilly auto parts"]),
    ("Mister Car Wash", "car_wash", ["mister car wash"]),
    ("LAZ Parking", "parking", ["laz parking"]),
    ("The UPS Store", "postal_shipping", ["the ups store", "ups store"]),
    ("FedEx Office", "postal_shipping", ["fedex office", "fedex ofc"]),
    ("GEICO", "insurance", ["geico"]),
    ("State Farm", "insurance", ["state farm"]),
    ("Progressive", "insurance", ["progressive"]),
    ("Pacific Gas & Electric", "utility", ["pacific gas & electric", "pg&e"]),
    ("Con Edison", "utility", ["con edison", "coned"]),
    ("Best Western", "hotel", ["best western"]),
    ("Holiday Inn", "hotel", ["holiday inn"]),
]

GAZETTEER_PATH = Path(__file__).parent.parent / "src" / "matlas" / "regions" / "us" / "gazetteer.us.jsonl"


def build_rows() -> list[dict]:
    rows = []
    for canonical, industry, keys in MERCHANTS:
        mcc, category = INDUSTRY_TO_MCC_CATEGORY[industry]
        for key in keys:
            rows.append({"key": key, "canonical": canonical, "category": category, "mcc": mcc})
    return rows


if __name__ == "__main__":
    existing_keys = set()
    with GAZETTEER_PATH.open() as f:
        for line in f:
            if line.strip():
                existing_keys.add(json.loads(line)["key"])

    new_rows = [r for r in build_rows() if r["key"] not in existing_keys]
    with GAZETTEER_PATH.open("a") as f:
        for row in new_rows:
            f.write(json.dumps(row) + "\n")
    print(f"appended {len(new_rows)} rows ({len(build_rows()) - len(new_rows)} already present)")
