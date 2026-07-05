"""One-off script: extend regions/india/gazetteer.in.jsonl with hand-curated
real Indian merchants (UPI payee names / VPA prefixes as keys). No MCC —
India rows carry only canonical name + shared category, per the portability
pack's honest-scope stance.

ponytail: no CLI flags, no argparse -- edit MERCHANTS below and rerun.
Idempotent: skips any key already present in the gazetteer.

Fuzzy-collision rule learned from the US batch: no bare key variant <= 5
chars unless it's an established brand string unlikely to appear inside
ordinary words (rapidfuzz WRatio partial-matches short substrings).
"""

import json
from pathlib import Path

GAZETTEER = (
    Path(__file__).parent.parent
    / "src"
    / "matlas"
    / "regions"
    / "india"
    / "gazetteer.in.jsonl"
)

# (canonical name, category, [key variants])
MERCHANTS = [
    # food delivery / QSR / cafes
    ("McDonald's India", "food_and_drink", ["mcdonalds", "mcdonaldsindia"]),
    ("KFC India", "food_and_drink", ["kfcindia", "kfc india"]),
    ("Burger King India", "food_and_drink", ["burgerking", "burger king"]),
    ("Pizza Hut India", "food_and_drink", ["pizzahut", "pizza hut"]),
    ("Haldiram's", "food_and_drink", ["haldirams", "haldiram"]),
    ("Barbeque Nation", "food_and_drink", ["barbequenation", "barbeque nation"]),
    ("Cafe Coffee Day", "food_and_drink", ["cafecoffeeday", "cafe coffee day", "ccdcafe"]),
    ("Starbucks India", "food_and_drink", ["starbucksindia", "tatastarbucks"]),
    ("Dunzo", "food_and_drink", ["dunzo"]),
    ("Licious", "food_and_drink", ["licious"]),
    ("Wow! Momo", "food_and_drink", ["wowmomo", "wow momo"]),
    ("Chaayos", "food_and_drink", ["chaayos"]),
    ("Blue Tokai Coffee", "food_and_drink", ["bluetokai", "blue tokai"]),
    ("Theobroma", "food_and_drink", ["theobroma"]),
    ("EatSure", "food_and_drink", ["eatsure"]),
    ("Behrouz Biryani", "food_and_drink", ["behrouz", "behrouzbiryani"]),
    # grocery / retail food
    ("DMart", "food_and_drink", ["dmart", "avenuesupermarts"]),
    ("JioMart", "food_and_drink", ["jiomart"]),
    ("Reliance Fresh", "food_and_drink", ["reliancefresh", "reliance fresh"]),
    ("Nature's Basket", "food_and_drink", ["naturesbasket", "natures basket"]),
    ("Spencer's Retail", "food_and_drink", ["spencers", "spencersretail"]),
    ("More Supermarket", "food_and_drink", ["moreretail", "more supermarket"]),
    # transportation / fuel
    ("Indian Oil", "transportation", ["indianoil", "iocl"]),
    ("Bharat Petroleum", "transportation", ["bharatpetroleum", "bpcl"]),
    ("Hindustan Petroleum", "transportation", ["hindustanpetroleum", "hpcl"]),
    ("BluSmart", "transportation", ["blusmart"]),
    ("Meru Cabs", "transportation", ["merucabs", "meru cabs"]),
    ("FASTag Recharge", "transportation", ["fastag"]),
    ("Delhi Metro", "transportation", ["delhimetro", "dmrc"]),
    ("Namma Metro", "transportation", ["nammametro", "bmrcl"]),
    # entertainment / streaming
    ("Spotify India", "entertainment", ["spotifyindia", "spotify"]),
    ("SonyLIV", "entertainment", ["sonyliv"]),
    ("ZEE5", "entertainment", ["zee5"]),
    ("JioCinema", "entertainment", ["jiocinema"]),
    ("PVR Cinemas", "entertainment", ["pvrcinemas", "pvr cinemas"]),
    ("INOX Movies", "entertainment", ["inoxmovies", "inox movies"]),
    ("Amazon Prime Video", "entertainment", ["primevideo", "prime video"]),
    ("Wonderla", "entertainment", ["wonderla"]),
    # general merchandise / e-commerce
    ("AJIO", "general_merchandise", ["ajio"]),
    ("Nykaa", "general_merchandise", ["nykaa"]),
    ("Meesho", "general_merchandise", ["meesho"]),
    ("Snapdeal", "general_merchandise", ["snapdeal"]),
    ("Tata CLiQ", "general_merchandise", ["tatacliq"]),
    ("Croma", "general_merchandise", ["croma"]),
    ("Reliance Digital", "general_merchandise", ["reliancedigital", "reliance digital"]),
    ("Decathlon India", "general_merchandise", ["decathlon"]),
    ("Lenskart", "general_merchandise", ["lenskart"]),
    ("FirstCry", "general_merchandise", ["firstcry"]),
    ("Pepperfry", "general_merchandise", ["pepperfry"]),
    ("Urban Ladder", "general_merchandise", ["urbanladder", "urban ladder"]),
    ("boAt Lifestyle", "general_merchandise", ["boatlifestyle", "imaginemarketing"]),
    ("Shoppers Stop", "general_merchandise", ["shoppersstop", "shoppers stop"]),
    ("Westside", "general_merchandise", ["westside"]),
    ("Max Fashion", "general_merchandise", ["maxfashion", "max fashion"]),
    ("Pantaloons", "general_merchandise", ["pantaloons"]),
    ("Fabindia", "general_merchandise", ["fabindia"]),
    ("Titan", "general_merchandise", ["titancompany", "titan watches"]),
    ("Tanishq", "general_merchandise", ["tanishq"]),
    ("Bata India", "general_merchandise", ["bataindia", "bata india"]),
    # utilities / telecom / broadband
    ("BSNL", "rent_and_utilities", ["bsnl"]),
    ("Tata Power", "rent_and_utilities", ["tatapower", "tata power"]),
    ("Adani Electricity", "rent_and_utilities", ["adanielectricity", "adani electricity"]),
    ("BESCOM", "rent_and_utilities", ["bescom"]),
    ("MSEDCL", "rent_and_utilities", ["msedcl", "mahadiscom"]),
    ("Torrent Power", "rent_and_utilities", ["torrentpower", "torrent power"]),
    ("ACT Fibernet", "rent_and_utilities", ["actfibernet", "act fibernet"]),
    ("Hathway", "rent_and_utilities", ["hathway"]),
    ("Tata Play", "rent_and_utilities", ["tataplay", "tatasky"]),
    ("Indraprastha Gas", "rent_and_utilities", ["indraprasthagas", "igl gas"]),
    ("Mahanagar Gas", "rent_and_utilities", ["mahanagargas", "mahanagar gas"]),
    ("Indane Gas", "rent_and_utilities", ["indanegas", "indane gas"]),
    # travel
    ("Goibibo", "travel", ["goibibo"]),
    ("Cleartrip", "travel", ["cleartrip"]),
    ("Yatra", "travel", ["yatraonline", "yatra.com"]),
    ("ixigo", "travel", ["ixigo"]),
    ("redBus", "travel", ["redbus"]),
    ("IndiGo", "travel", ["indigoairlines", "interglobeaviation", "goindigo"]),
    ("Air India", "travel", ["airindia", "air india"]),
    ("SpiceJet", "travel", ["spicejet"]),
    ("Akasa Air", "travel", ["akasaair", "akasa air"]),
    ("Vistara", "travel", ["vistara"]),
    ("OYO Rooms", "travel", ["oyorooms", "oyo rooms"]),
    ("Treebo Hotels", "travel", ["treebo", "treebohotels"]),
    ("FabHotels", "travel", ["fabhotels"]),
    # medical / pharmacy
    ("Netmeds", "medical", ["netmeds"]),
    ("PharmEasy", "medical", ["pharmeasy"]),
    ("Tata 1mg", "medical", ["tata1mg", "1mg healthcare"]),
    ("MedPlus", "medical", ["medplusmart", "medplus pharmacy"]),
    ("Max Healthcare", "medical", ["maxhealthcare", "max healthcare"]),
    ("Fortis Healthcare", "medical", ["fortishealthcare", "fortis healthcare"]),
    ("Dr Lal PathLabs", "medical", ["lalpathlabs", "dr lal pathlabs"]),
    # personal care / fitness
    ("Cult.fit", "personal_care", ["cultfit", "curefit"]),
    ("Lakme Salon", "personal_care", ["lakmesalon", "lakme salon"]),
    ("Naturals Salon", "personal_care", ["naturalssalon", "naturals salon"]),
    # services
    ("Urban Company", "general_services", ["urbancompany", "urbanclap"]),
    ("NoBroker", "general_services", ["nobroker"]),
    ("PolicyBazaar", "general_services", ["policybazaar"]),
    ("LIC of India", "general_services", ["licindia", "lic of india"]),
    ("Blue Dart", "general_services", ["bluedart", "blue dart"]),
    ("Delhivery", "general_services", ["delhivery"]),
    ("DTDC", "general_services", ["dtdc courier", "dtdcindia"]),
]


def build_rows() -> list[dict[str, str]]:
    rows = []
    for canonical, category, variants in MERCHANTS:
        for key in variants:
            rows.append({"key": key.lower(), "canonical": canonical, "category": category})
    return rows


def main() -> None:
    existing = set()
    with GAZETTEER.open() as f:
        for line in f:
            if line.strip():
                existing.add(json.loads(line)["key"])

    new_rows = [r for r in build_rows() if r["key"] not in existing]
    with GAZETTEER.open("a") as f:
        for r in new_rows:
            f.write(json.dumps(r) + "\n")
    print(f"appended {len(new_rows)} rows ({len(existing)} already present)")


if __name__ == "__main__":
    main()
