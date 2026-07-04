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
    "fast_food": ("5814", "food_and_drink"),
    "grocery": ("5411", "food_and_drink"),
    "gas_station": ("5541", "transportation"),
    "warehouse_club": ("5300", "general_merchandise"),
    "department_store": ("5311", "general_merchandise"),
    "electronics": ("5732", "general_merchandise"),
    "pharmacy": ("5912", "medical"),
    "airline": ("4511", "travel"),
    "bank": ("6011", "bank_fees"),
    "liquor_store": ("5921", "general_merchandise"),
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
    ("Wendy's", "fast_food", ["wendys", "wendy's"]),
    ("Burger King", "fast_food", ["burger king"]),
    ("Taco Bell", "fast_food", ["taco bell"]),
    ("KFC", "fast_food", ["kfc"]),
    ("Subway", "fast_food", ["subway"]),
    ("Popeyes", "fast_food", ["popeyes"]),
    ("Panera Bread", "fast_food", ["panera bread", "panera"]),
    ("Panda Express", "fast_food", ["panda express"]),
    ("Domino's", "fast_food", ["dominos", "domino's pizza"]),
    ("Pizza Hut", "fast_food", ["pizza hut"]),
    ("Papa John's", "fast_food", ["papa johns", "papa john's"]),
    ("Five Guys", "fast_food", ["five guys"]),
    ("In-N-Out Burger", "fast_food", ["in-n-out", "in-n-out burger"]),
    ("Chick-fil-A", "fast_food", ["chick-fil-a", "chickfila"]),
    ("Peet's Coffee", "fast_food", ["peets coffee", "peet's coffee"]),
    ("Dutch Bros Coffee", "fast_food", ["dutch bros"]),
    ("Safeway", "grocery", ["safeway"]),
    ("Kroger", "grocery", ["kroger"]),
    ("Publix", "grocery", ["publix"]),
    ("Aldi", "grocery", ["aldi"]),
    ("Albertsons", "grocery", ["albertsons"]),
    ("Chevron", "gas_station", ["chevron"]),
    ("BP", "gas_station", ["bp", "bp gas station"]),
    ("Marathon", "gas_station", ["marathon petroleum", "marathon gas"]),
    ("Speedway", "gas_station", ["speedway"]),
    ("Sunoco", "gas_station", ["sunoco"]),
    ("Valero", "gas_station", ["valero"]),
    ("Phillips 66", "gas_station", ["phillips 66"]),
    ("Sam's Club", "warehouse_club", ["sams club", "sam's club"]),
    ("BJ's Wholesale", "warehouse_club", ["bjs wholesale", "bj's wholesale club"]),
    ("Kohl's", "department_store", ["kohls", "kohl's"]),
    ("JCPenney", "department_store", ["jcpenney", "jc penney"]),
    ("Nordstrom", "department_store", ["nordstrom"]),
    ("Dillard's", "department_store", ["dillards", "dillard's"]),
    ("Apple Store", "electronics", ["apple store", "apple.com/bill"]),
    ("Micro Center", "electronics", ["micro center"]),
    ("GameStop", "toy", ["gamestop"]),
    ("Rite Aid", "pharmacy", ["rite aid"]),
    ("American Airlines", "airline", ["american airlines"]),
    ("Southwest Airlines", "airline", ["southwest airlines", "southwest"]),
    ("JetBlue", "airline", ["jetblue"]),
    ("Alaska Airlines", "airline", ["alaska airlines"]),
    ("Chase", "bank", ["chase", "jpmorgan chase"]),
    ("Bank of America", "bank", ["bank of america", "bofa"]),
    ("Wells Fargo", "bank", ["wells fargo"]),
    ("Citibank", "bank", ["citibank", "citi"]),
    ("Total Wine & More", "liquor_store", ["total wine", "total wine & more"]),
    ("BevMo", "liquor_store", ["bevmo"]),
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
