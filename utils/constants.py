"""Static maps for paint colors, killstreak tiers and other enums."""

# Map of killstreak tier id -> readable name
KILLSTREAK_TIERS = {
    1: "Killstreak",
    2: "Specialized Killstreak",
    3: "Professional Killstreak",
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
    8208498: ("A Distinctive Lack of Hue", "#141414"),
    15185211: ("A Mann's Mint", "#BCDDB3"),
    12955537: ("After Eight", "#2D2D24"),
    8289918: ("Dark Salmon Injustice", "#E9967A"),
    8421376: ("Indubitably Green", "#729E42"),
    13595446: ("Mann Co. Orange", "#CF7336"),
    12377523: ("Muskelmannbraun", "#A57545"),
    5322826: ("Noble Hatter's Violet", "#51384A"),
    15787660: ("Pink as Hell", "#FF69B4"),
    8154199: ("Peculiarly Drab Tincture", "#C5AF91"),
    4345659: ("Radigan Conagher Brown", "#694D3A"),
    2960676: ("Color No. 216-190-216", "#D8BED8"),
    7511618: ("The Bitter Taste of Defeat and Lime", "#32CD32"),
    15132390: ("Drably Olive", "#808000"),
    8422108: ("The Color of a Gentlemann's Business Pants", "#FBE85C"),
    12807213: ("Ye Olde Rustic Colour", "#7C6C57"),
    1315860: ("An Extraordinary Abundance of Tinge", "#E6E6E6"),
    12073019: ("Team Spirit", "#B8383B"),
    15787618: ("An Air of Debonair", "#654740"),
    8208496: ("Balaclavas Are Forever", "#3B1F23"),
    8208499: ("Cream Spirit", "#C36C2D"),
    1757009: ("Operator's Overalls", "#483838"),
    6901050: ("Waterlogged Lab Coat", "#A9B4C2"),
    2158218: ("Zepheniah's Greed", "#424F3B"),
    3874595: ("The Value of Teamwork", "#FFD700"),
    16341610: ("A Color Most Splendid", "#FFB000"),
    15158332: ("Australium Gold", "#E7B53B"),
    13164768: ("Aged Moustache Grey", "#7E7E7E"),
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
