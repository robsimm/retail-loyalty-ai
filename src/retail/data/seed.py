from __future__ import annotations

import random
import sqlite3
import uuid
from datetime import datetime, timedelta

CATEGORIES = [
    "grocery", "dairy", "bakery", "produce", "meat",
    "frozen", "beverages", "snacks", "household", "personal_care",
]

PRODUCT_NAMES: dict[str, list[str]] = {
    "grocery": [
        "Heinz Baked Beans 415g", "Heinz Tomato Soup 400g", "Oxo Beef Stock Cubes 12pk",
        "Baxters Vegetable Soup 400g", "Sharwood's Tikka Masala Sauce 420g",
        "Napolina Chopped Tomatoes 400g", "Branston Pickle 720g", "Hellmann's Mayonnaise 400g",
        "HP Brown Sauce 285g", "Bisto Gravy Granules 190g", "Colman's English Mustard 170g",
        "Heinz Salad Cream 285g", "Lyle's Golden Syrup 454g", "Ambrosia Custard 400g",
        "Lea & Perrins Worcestershire Sauce 150ml", "Robertson's Marmalade 454g",
        "Crosse & Blackwell Tomato Soup 400g", "Bachelors Pasta 'n' Sauce Cheese 99g",
        "Homepride Pasta Sauce 490g", "Hartley's Strawberry Jam 340g",
    ],
    "dairy": [
        "Cravendale Whole Milk 2L", "Cravendale Semi-Skimmed Milk 2L",
        "Cathedral City Mature Cheddar 400g", "Anchor Salted Butter 250g",
        "Lurpak Spreadable 500g", "Yeo Valley Organic Yogurt 500g",
        "Müller Corner Strawberry 135g", "Activia Strawberry Yogurt 4pk",
        "Philadelphia Light Cream Cheese 300g", "Elmlea Double Cream 300ml",
        "Cathedral City Extra Mature Cheddar 400g", "Dairylea Triangles 140g",
        "Clover Dairy Spread 500g", "Onken Natural Set Yogurt 500g",
        "Müller Light Vanilla 4pk", "Longley Farm Cottage Cheese 250g",
        "Galbani Mozzarella 125g", "Kerrygold Irish Butter 200g",
        "Arla Organic Whole Milk 1L", "St Ivel Gold Spread 500g",
    ],
    "bakery": [
        "Warburtons Medium Sliced White 800g", "Warburtons Toastie Thick White 800g",
        "Hovis Best of Both 800g", "Hovis Seed Sensations 800g",
        "Kingsmill 50/50 800g", "Mr Kipling Apple Pies 6pk",
        "Mr Kipling Bakewell Slices 6pk", "McVitie's Digestives 400g",
        "McVitie's Rich Tea 300g", "Jacob's Cream Crackers 200g",
        "Tunnock's Caramel Wafers 8pk", "Fox's Party Rings 125g",
        "Warburtons Seeded Batch 400g", "Hovis Granary Farmhouse 800g",
        "Kingsmill Mighty White 800g", "McVitie's Jaffa Cakes 12pk",
        "Cadbury Chocolate Fingers 114g", "Tunnock's Tea Cakes 6pk",
        "Hovis Wholemeal 400g", "Warburtons Crumpets 6pk",
    ],
    "produce": [
        "Florette Crispy Salad 200g", "Tenderstem Broccoli 200g",
        "British Strawberries 400g", "Bramley Cooking Apples 4pk",
        "Conference Pears 6pk", "Clementines 600g",
        "Baby Plum Tomatoes 300g", "Avocado Ripe & Ready 2pk",
        "British Asparagus 250g", "Sugar Snap Peas 150g",
        "Chantenay Carrots 350g", "Cucumber Each",
        "Iceberg Lettuce Each", "Red Pepper Each",
        "Sweetheart Cabbage Each", "Florette Mixed Salad 120g",
        "Baby Courgettes 300g", "British Leeks 500g",
        "Vine Ripened Tomatoes 500g", "Radishes 200g",
    ],
    "meat": [
        "Richmond Thick Pork Sausages 454g", "Heck 97% Pork Sausages 400g",
        "Walls Pork Sausages 454g", "Mattessons Smoked Pork Sausage 260g",
        "Quorn Mince 500g", "Quorn Fillets 4pk",
        "Bernard Matthews Turkey Steaks 2pk", "Bernard Matthews Kievs 2pk",
        "Quorn Sausages 300g", "Bernard Matthews Wafer Thin Turkey 125g",
        "Richmond Chicken Sausages 400g", "Mattessons Wafer Thin Smoked Ham 200g",
        "Heck Chicken Sausages 400g", "Bernard Matthews Dino Nuggets 325g",
        "Walls Bacon Medallions 200g", "Moy Park Chicken Breast Fillets 400g",
        "Heck 10 Beef Burgers", "Richmond Bacon Rashers 240g",
        "Quorn Peppered Steaks 2pk", "Bernard Matthews Mini Fillets 300g",
    ],
    "frozen": [
        "Birds Eye Garden Peas 900g", "Birds Eye Fish Fingers 10pk",
        "McCain Oven Chips 1kg", "McCain Micro Chips 400g",
        "Birds Eye Chicken Dippers 320g", "Young's Chip Shop Cod Fillets 2pk",
        "Goodfella's Thin Pepperoni Pizza", "Chicago Town Pepperoni Pizza",
        "Birds Eye Beef Burgers 4pk", "Aunt Bessie's Roast Potatoes 800g",
        "Aunt Bessie's Homestyle Mash 800g", "Young's Beer Battered Fish 2pk",
        "Birds Eye Steamfresh Sweetcorn 4pk", "Linda McCartney Vegetarian Sausages 300g",
        "Walls Carte d'Or Vanilla Ice Cream 1L", "Ben & Jerry's Chocolate Fudge Brownie 465ml",
        "Häagen-Dazs Strawberry 460ml", "Magnum Classic 3pk",
        "Findus Crispy Pancakes Minced Beef 5pk", "Birds Eye Chicken Pie 400g",
    ],
    "beverages": [
        "Ribena Original Blackcurrant 1L", "Tropicana Pure Orange 850ml",
        "Innocent Orange Juice 900ml", "Lucozade Energy Original 380ml",
        "Lucozade Sport Orange 500ml", "Volvic Still Water 1.5L",
        "Highland Spring Still Water 1.5L", "Coca-Cola Original 1.75L",
        "Pepsi Max 1.75L", "Schweppes Lemonade 1L",
        "J2O Orange & Passion Fruit 4pk", "Ribena Light Blackcurrant 1L",
        "Fanta Orange 1.75L", "Robinsons Squash'd Orange 66ml",
        "Fever-Tree Tonic Water 4pk", "Belvoir Elderflower Cordial 500ml",
        "Oasis Summer Fruits 500ml", "Tango Orange 1.75L",
        "Dr Pepper 1.75L", "7UP Free 1.75L",
    ],
    "snacks": [
        "Walkers Ready Salted Crisps 6pk", "Walkers Salt & Vinegar 6pk",
        "Pringles Original 200g", "Pringles Sour Cream & Onion 200g",
        "Doritos Chilli Heatwave 150g", "Haribo Starmix 175g",
        "Haribo Tangfastics 175g", "Cadbury Dairy Milk 110g",
        "Kit Kat 4-Finger 45g", "Maltesers 103g",
        "Cadbury Roses 375g", "Quality Street 600g",
        "Rowntrees Fruit Pastilles 52g", "Quavers Cheese 6pk",
        "Hula Hoops Original 6pk", "Monster Munch Pickled Onion 6pk",
        "Butterkist Toffee Popcorn 270g", "Tyrrell's Mature Cheddar Crisps 150g",
        "Pom-Bear Original 5pk", "Maryland Chocolate Chip Cookies 200g",
    ],
    "household": [
        "Fairy Original Washing-Up Liquid 900ml", "Ariel 3-in-1 PODS 20 Washes",
        "Bold 2-in-1 Washing Powder 25 Washes", "Comfort Tropical Fresh 57 Washes",
        "Flash All Purpose Spray 500ml", "Dettol Antibacterial Spray 500ml",
        "Domestos Thick Bleach 750ml", "Mr Muscle Oven Cleaner 300ml",
        "Cillit Bang Power Cleaner 750ml", "Andrex Classic Clean 9pk",
        "Cushelle Original Toilet Roll 9pk", "Plenty Original Kitchen Roll 2pk",
        "Finish All-in-1 Dishwasher Tablets 48pk", "Ecover Washing-Up Liquid 450ml",
        "Carex Original Hand Wash 250ml", "Zoflora Concentrated Disinfectant 250ml",
        "Dettol Laundry Cleanser 1.5L", "Surf Tropical Lily Powder 25 Washes",
        "Radox Sensitive Hand Wash 300ml", "Method All-Purpose Cleaner 828ml",
    ],
    "personal_care": [
        "Head & Shoulders Classic Clean Shampoo 400ml", "Pantene Repair & Protect Shampoo 400ml",
        "Dove Original Beauty Bar 4pk", "Sure Men Sport Antiperspirant 250ml",
        "Dove Original Antiperspirant 250ml", "Colgate Total Whitening Toothpaste 125ml",
        "Sensodyne Repair & Protect 75ml", "Oral-B Advantage Plus Toothbrush 2pk",
        "Gillette Fusion5 Blades 8pk", "Nivea Men Sensitive Moisturiser 75ml",
        "Olay Total Effects Moisturiser 50ml", "Simple Kind to Skin Moisturiser 125ml",
        "Radox Muscle Soak Bath Soak 500ml", "Imperial Leather Shower Gel 500ml",
        "Tampax Pearl Regular 18pk", "Always Ultra Normal 28pk",
        "Clearasil Rapid Action Gel 15ml", "E45 Dry Skin Moisturising Cream 350g",
        "Boots Vitamin C Serum 30ml", "Veet Hair Removal Cream Sensitive 200ml",
    ],
}

AGE_BRACKETS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
CHANNELS = ["online", "instore", "both"]
SEGMENTS = ["champions", "loyal", "at_risk", "lost"]

SEGMENT_CONFIG = {
    "champions":  {"freq_range": (40, 60),  "days_ago_range": (1, 14),   "spend_range": (20, 80)},
    "loyal":      {"freq_range": (20, 40),  "days_ago_range": (14, 45),  "spend_range": (15, 60)},
    "at_risk":    {"freq_range": (5, 20),   "days_ago_range": (45, 120), "spend_range": (10, 40)},
    "lost":       {"freq_range": (1, 5),    "days_ago_range": (120, 365),"spend_range": (5, 20)},
}


def seed_database(db_path: str = "retail.db", n_customers: int = 1000) -> dict[str, int]:
    """Seed SQLite with synthetic retail data. Returns counts."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
        DROP TABLE IF EXISTS transactions;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS products;

        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            age_bracket TEXT,
            channel_preference TEXT,
            signup_date TEXT,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE products (
            product_id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            price_gbp REAL,
            is_high_consideration INTEGER DEFAULT 0,
            available_online INTEGER DEFAULT 1,
            available_instore INTEGER DEFAULT 1
        );

        CREATE TABLE transactions (
            transaction_id TEXT PRIMARY KEY,
            customer_id TEXT,
            amount_gbp REAL,
            category TEXT,
            timestamp TEXT,
            channel TEXT,
            is_return INTEGER DEFAULT 0
        );
    """)

    # Seed products (200)
    products = []
    for i in range(1, 201):
        cat = CATEGORIES[(i - 1) % len(CATEGORIES)]
        idx = (i - 1) // len(CATEGORIES)
        price = round(random.uniform(0.50, 25.00), 2)
        products.append((
            f"PRD_{i:05d}",
            PRODUCT_NAMES[cat][idx],
            cat,
            price,
            1 if price > 15 else 0,
            1, 1,
        ))
    cur.executemany(
        "INSERT INTO products VALUES (?,?,?,?,?,?,?)", products
    )

    # Seed customers + transactions
    all_transactions = []
    segment_counts: dict[str, int] = {s: 0 for s in SEGMENTS}

    segment_labels = (
        ["champions"] * 120 + ["loyal"] * 380 + ["at_risk"] * 300 + ["lost"] * 200
    )
    random.shuffle(segment_labels)

    for i in range(n_customers):
        cid = f"CUS_{i+1:08d}"
        age = random.choice(AGE_BRACKETS)
        channel = random.choice(CHANNELS)
        signup = (datetime.now() - timedelta(days=random.randint(180, 1800))).date().isoformat()
        cur.execute(
            "INSERT INTO customers VALUES (?,?,?,?,?)", (cid, age, channel, signup, 1)
        )

        segment = segment_labels[i]
        cfg = SEGMENT_CONFIG[segment]
        segment_counts[segment] += 1

        n_tx = random.randint(*cfg["freq_range"])
        for _ in range(n_tx):
            days_ago = random.randint(*cfg["days_ago_range"])
            ts = (datetime.now() - timedelta(days=days_ago)).isoformat(timespec="seconds")
            cat = random.choice(CATEGORIES)
            amount = round(random.uniform(*cfg["spend_range"]), 2)
            if channel in ("online", "instore"):
                ch = channel
            else:
                ch = random.choice(["online", "instore"])
            all_transactions.append((
                str(uuid.uuid4()), cid, amount, cat, ts, ch, 0
            ))

    cur.executemany(
        "INSERT INTO transactions VALUES (?,?,?,?,?,?,?)", all_transactions
    )

    conn.commit()
    conn.close()

    return {
        "customers": n_customers,
        "transactions": len(all_transactions),
        "products": len(products),
        **segment_counts,
    }
