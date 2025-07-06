"""Static maps for paint colors, killstreak tiers and other enums."""

# Map of killstreak tier id -> readable name
KILLSTREAK_TIERS = {
    1: "Killstreak",
    2: "Specialized Killstreak",
    3: "Professional Killstreak",
}

# Map of killstreak tier id -> badge icon
KILLSTREAK_BADGE_ICONS = {
    1: "›",
    2: "››",
    3: "›››",
}

# Map of sheen id -> name
SHEEN_NAMES = {
    1: "Team Shine",
    2: "Deadly Daffodil",
    3: "Manndarin",
    4: "Mean Green",
    5: "Agonizing Emerald",
    6: "Villainous Violet",
    7: "Hot Rod",
}

# Map of item origin id -> human readable string
ORIGIN_MAP = {
    0: "Timed Drop",
    1: "Achievement",
    2: "Purchased",
    3: "Traded",
    4: "Crafted",
    5: "Store Promotion",
    6: "Gifted",
    7: "Support Promotion",
    8: "Found in Crate",
    9: "Earned",
    10: "Third-Party Promotion",
    11: "Purchased",
    12: "Halloween Drop",
    13: "Package Item",
    14: "Store Promotion",
    15: "Foreign",
}

# Map of paint id -> (name, hex color)
PAINT_COLORS = {
    3100495: ("A Color Similar to Slate", "#2F4F4F"),
    8208497: ("A Deep Commitment to Purple", "#7D4071"),
    1315860: ("A Distinctive Lack of Hue", "#141414"),
    12377523: ("A Mann's Mint", "#BCDDB3"),
    2960676: ("After Eight", "#2D2D24"),
    15308410: ("Dark Salmon Injustice", "#E9967A"),
    7511618: ("Indubitably Green", "#729E42"),
    13595446: ("Mann Co. Orange", "#CF7336"),
    10843461: ("Muskelmannbraun", "#A57545"),
    5322826: ("Noble Hatter's Violet", "#51384A"),
    16738740: ("Pink as Hell", "#FF69B4"),
    12955537: ("Peculiarly Drab Tincture", "#C5AF91"),
    6901050: ("Radigan Conagher Brown", "#694D3A"),
    14204632: ("Color No. 216-190-216", "#D8BED8"),
    3329330: ("The Bitter Taste of Defeat and Lime", "#32CD32"),
    8421376: ("Drably Olive", "#808000"),
    15787660: ("The Color of a Gentlemann's Business Pants", "#FBE85C"),
    8154199: ("Ye Olde Rustic Colour", "#7C6C57"),
    15132390: ("An Extraordinary Abundance of Tinge", "#E6E6E6"),
    12073019: ("Team Spirit", "#B8383B"),
    6637376: ("An Air of Debonair", "#654740"),
    8208496: ("Balaclavas Are Forever", "#3B1F23"),
    12807213: ("Cream Spirit", "#C36C2D"),
    4732984: ("Operator's Overalls", "#483838"),
    11049612: ("Waterlogged Lab Coat", "#A9B4C2"),
    4345659: ("Zepheniah's Greed", "#424F3B"),
    8400928: ("The Value of Teamwork", "#FFD700"),
    5801378: ("A Color Most Splendid", "#FFB000"),
    15185211: ("Australium Gold", "#E7B53B"),
    8289918: ("Aged Moustache Grey", "#7E7E7E"),
}

# Map of killstreak effect id -> name
KILLSTREAK_EFFECTS = {
    2002: "Fire Horns",
    2003: "Cerebral Discharge",
    2004: "Tornado",
    2005: "Flames",
    2006: "Singularity",
    2007: "Incinerator",
    2008: "Hypno-Beam",
    2009: "Tesla Coil",
    2010: "Hellish Inferno",
    2011: "Fireworks",
}

# Map of spell attribute id -> map of value -> spell name
SPELL_MAP = {
    1004: {
        0: "Die Job",
        1: "Chromatic Corruption",
        2: "Putrescent Pigmentation",
        3: "Spectral Spectrum",
        4: "Sinister Staining",
    },
    1005: {
        1: "Team Spirit Footprints",
        2: "Headless Horseshoes",
        3100495: "Corpse Gray Footprints",
        5322826: "Violent Violet Footprints",
        8208497: "Bruised Purple Footprints",
        8421376: "Gangreen Footprints",
        13595446: "Rotten Orange Footprints",
    },
    1006: {1: "Voices From Below"},
    1007: {1: "Pumpkin Bombs"},
    1008: {1: "Halloween Fire"},
    1009: {1: "Exorcism"},
}
