import os
import random
from typing import List, Literal
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "TCG Pack Opener Backend Ready"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


# --- Pack Generation Logic ---
RARITIES: List[Literal["Common","Rare","Super Rare","Ultra Rare","Legendary"]] = [
    "Common","Rare","Super Rare","Ultra Rare","Legendary"
]
RARITY_WEIGHTS = {
    "Common": 70,
    "Rare": 20,
    "Super Rare": 7,
    "Ultra Rare": 2.7,
    "Legendary": 0.3,
}

ELEMENTS = [
    "Aether", "Ember", "Tide", "Gaia", "Umbral", "Lumina", "Chrono", "Arcane"
]

ADJECTIVES = [
    "Veiled", "Gilded", "Obsidian", "Celestial", "Crimson", "Iridescent", "Mythic", "Nocturne",
    "Prismatic", "Sovereign", "Eternal", "Radiant", "Duskborn", "Starlit"
]
NOUNS = [
    "Seraph", "Warden", "Drake", "Oracle", "Harbinger", "Vanguard", "Matriarch", "Savant",
    "Revenant", "Duelist", "Archon", "Leviathan", "Reclaimer", "Specter"
]

RARITY_THEME = {
    "Common": {
        "frame":"from-slate-800/80 via-slate-700/60 to-slate-900/80",
        "glow":"shadow-slate-400/20",
        "foil":"to-slate-400/10",
    },
    "Rare": {
        "frame":"from-sky-600/70 via-sky-700/60 to-indigo-800/80",
        "glow":"shadow-sky-400/40",
        "foil":"to-sky-300/20",
    },
    "Super Rare": {
        "frame":"from-emerald-600/70 via-teal-700/60 to-cyan-800/80",
        "glow":"shadow-emerald-300/50",
        "foil":"to-emerald-300/25",
    },
    "Ultra Rare": {
        "frame":"from-fuchsia-600/70 via-violet-700/60 to-indigo-800/80",
        "glow":"shadow-fuchsia-300/60",
        "foil":"to-fuchsia-300/30",
    },
    "Legendary": {
        "frame":"from-amber-500/80 via-rose-600/70 to-violet-800/80",
        "glow":"shadow-amber-300/70",
        "foil":"to-amber-300/40",
    },
}


def weighted_rarity() -> str:
    pool = []
    for r, w in RARITY_WEIGHTS.items():
        pool.extend([r] * int(w * 10))
    return random.choice(pool)


def make_card(seed: int):
    rarity = weighted_rarity()
    name = f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"
    element = random.choice(ELEMENTS)
    holographic = rarity in ("Super Rare","Ultra Rare","Legendary")
    art = f"https://picsum.photos/seed/{seed}-{element.replace(' ','')}/300/450"
    theme = RARITY_THEME[rarity]
    return {
        "id": f"{seed}-{random.randint(1000,9999)}",
        "name": name,
        "rarity": rarity,
        "element": element,
        "holographic": holographic,
        "art": art,
        "theme": theme,
        "attack": random.randint(100, 4000),
        "defense": random.randint(100, 4000),
        "lore": "A coveted relic from an adult-leaning arcane saga, crafted for collectors who appreciate elegance over cartoons.",
    }


@app.get("/api/open-pack")
def open_pack(size: int = Query(10, ge=3, le=12)):
    # Guarantee at least one Rare+
    cards = [make_card(i) for i in range(size)]
    if not any(RARITIES.index(c["rarity"]) >= RARITIES.index("Rare") for c in cards):
        cards[random.randrange(size)] = make_card(99999)
        cards[-1]["rarity"] = "Ultra Rare"
    return {"pack": cards}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
