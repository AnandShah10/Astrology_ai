import swisseph as swe
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io, base64

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_ABBR = ["Ari","Tau","Gem","Can","Leo","Vir","Lib","Sco","Sag","Cap","Aqu","Pis"]
PLANETS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]

NUM_LIST = {
    "Ari" :1 ,"Tau" : 2,"Gem":3,"Can":4,"Leo":5,"Vir":6,
    "Lib":7,"Sco":8,"Sag":9,"Cap":10,"Aqu":11,"Pis":12
}

PLANET_ABBR = {
    "Sun": "Su",
    "Moon": "Mo",
    "Mars": "Ma",
    "Mercury": "Me",
    "Jupiter": "Ju",
    "Venus": "Ve",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke"
}
SIGN_LORDS = {
    "Ari": "Mars",
    "Tau": "Venus",
    "Gem": "Mercury",
    "Can": "Moon",
    "Leo": "Sun",
    "Vir": "Mercury",
    "Lib": "Venus",
    "Sco": "Mars",   # (Ketu also considered)
    "Sag": "Jupiter",
    "Cap": "Saturn",
    "Aqu": "Saturn", # (Rahu also considered)
    "Pis": "Jupiter" # (Ketu also considered)
}

# Nakshatra lords (Vimshottari Dasha sequence)
NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus", "Sun",
    "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury"
]
# Nakshatra & Pada Calculation
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Planetary Relationships (Permanent)
PLANET_RELATIONS = {
    "Sun": {"friends": ["Moon", "Mars", "Jupiter"], "enemies": ["Venus", "Saturn"], "neutral": ["Mercury"]},
    "Moon": {"friends": ["Sun", "Mercury"], "enemies": [], "neutral": ["Mars", "Jupiter", "Venus", "Saturn"]},
    "Mars": {"friends": ["Sun", "Moon", "Jupiter"], "enemies": ["Mercury"], "neutral": ["Venus", "Saturn"]},
    "Mercury": {"friends": ["Sun", "Venus"], "enemies": ["Moon"], "neutral": ["Mars", "Jupiter", "Saturn"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "enemies": ["Mercury", "Venus"], "neutral": ["Saturn"]},
    "Venus": {"friends": ["Mercury", "Saturn"], "enemies": ["Sun", "Moon"], "neutral": ["Mars", "Jupiter"]},
    "Saturn": {"friends": ["Mercury", "Venus"], "enemies": ["Sun", "Moon", "Mars"], "neutral": ["Jupiter"]},
    "Rahu": {"friends": ["Venus", "Saturn", "Mercury"], "enemies": ["Sun", "Moon"], "neutral": ["Mars", "Jupiter"]},
    "Ketu": {"friends": ["Mars", "Jupiter"], "enemies": ["Sun", "Moon"], "neutral": ["Mercury", "Venus", "Saturn"]}
}

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday","Sunday"]

TITHIS = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashti", "Saptami", "Ashtami",
    "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya"
]

KARANAS = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti",
    "Shakuni", "Chatushpada", "Naga", "Kimstughna"
]

YOGAS = [
    "Vishkumbha", "Preeti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma",
    "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", 
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", 
    "Shukla", "Brahma", "Indra", "Vaidhriti"
]

# Varna (by Moon sign)
VARNA = {
    "Ari": "Kshatriya", "Leo": "Kshatriya", "Sco": "Kshatriya", "Sag": "Kshatriya",
    "Tau": "Vaishya", "Lib": "Vaishya", "Cap": "Vaishya", "Aqu": "Vaishya",
    "Gem": "Shudra", "Vir": "Shudra", "Pis": "Shudra",
    "Can": "Brahmin"
}

# Vashya (sign classification for compatibility)
VASHYA = {
    "Ari": "Chatushpad", "Leo": "Chatushpad", "Sag": "Chatushpad", "Cap": "Chatushpad",
    "Tau": "Chatushpad", "Sco": "Keet", 
    "Gem": "Manav", "Vir": "Manav", "Lib": "Manav", "Aqu": "Manav",
    "Can": "Jalachar", "Pis": "Jalachar"
}

# Yoni mapping by Nakshatra
YONI = {
    "Ashwini":"Horse","Bharani":"Elephant","Krittika":"Sheep","Rohini":"Snake",
    "Mrigashira":"Snake","Ardra":"Dog","Punarvasu":"Cat","Pushya":"Sheep","Ashlesha":"Cat",
    "Magha":"Rat","Purva Phalguni":"Rat","Uttara Phalguni":"Cow","Hasta":"Buffalo",
    "Chitra":"Tiger","Swati":"Buffalo","Vishakha":"Tiger","Anuradha":"Deer","Jyeshtha":"Deer",
    "Mula":"Dog","Purva Ashadha":"Monkey","Uttara Ashadha":"Mongoose","Shravana":"Monkey",
    "Dhanishta":"Lion","Shatabhisha":"Horse","Purva Bhadrapada":"Lion","Uttara Bhadrapada":"Cow","Revati":"Elephant"
}

# Gana
GANA = {
    "Ashwini":"Deva","Bharani":"Manushya","Krittika":"Rakshasa","Rohini":"Manushya",
    "Mrigashira":"Deva","Ardra":"Manushya","Punarvasu":"Deva","Pushya":"Deva","Ashlesha":"Rakshasa",
    "Magha":"Rakshasa","Purva Phalguni":"Manushya","Uttara Phalguni":"Manushya","Hasta":"Deva",
    "Chitra":"Rakshasa","Swati":"Deva","Vishakha":"Rakshasa","Anuradha":"Deva","Jyeshtha":"Rakshasa",
    "Mula":"Rakshasa","Purva Ashadha":"Manushya","Uttara Ashadha":"Manushya","Shravana":"Deva",
    "Dhanishta":"Rakshasa","Shatabhisha":"Rakshasa","Purva Bhadrapada":"Manushya","Uttara Bhadrapada":"Manushya","Revati":"Deva"
}

# Nadi
NADI = {
    "Ashwini":"Adya","Bharani":"Madhya","Krittika":"Antya","Rohini":"Adya",
    "Mrigashira":"Madhya","Ardra":"Antya","Punarvasu":"Adya","Pushya":"Madhya","Ashlesha":"Antya",
    "Magha":"Adya","Purva Phalguni":"Madhya","Uttara Phalguni":"Antya","Hasta":"Adya",
    "Chitra":"Madhya","Swati":"Antya","Vishakha":"Adya","Anuradha":"Madhya","Jyeshtha":"Antya",
    "Mula":"Adya","Purva Ashadha":"Madhya","Uttara Ashadha":"Antya","Shravana":"Adya",
    "Dhanishta":"Madhya","Shatabhisha":"Antya","Purva Bhadrapada":"Adya","Uttara Bhadrapada":"Madhya","Revati":"Antya"
}

# ---------- KARANA (correct algorithm) ----------
MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
FIXED_KARANAS = {
    57: "Shakuni",
    58: "Chatushpada",
    59: "Naga",
    0:  "Kimstughna"
}

def get_karana_from_degrees(sun_deg, moon_deg):
    """
    Classical algorithm: K = int(((Moon - Sun) mod 360) / 6)
    If K in {57,58,59,0} -> fixed names, else reduce mod 7 to pick movable list.
    Returns the karana name.
    """
    diff = (moon_deg - sun_deg) % 360
    k = int(diff // 6)  # 0..59
    if k in FIXED_KARANAS:
        return FIXED_KARANAS[k]
    rem = k % 7
    if rem == 0:
        rem = 7
    return MOVABLE_KARANAS[rem - 1]


# ---------- PAYA (by Moon's nakshatra) ----------
# Many Jyotish sources determine paya from the nakshatra the Moon is in.
GOLD_PAYA_NAKS = {"Revati", "Ashwini", "Bharani"}
IRON_PAYA_NAKS = {"Krittika", "Rohini", "Mrigashira"}
SILVER_PAYA_NAKS = {
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra",
    "Swati", "Vishakha", "Anuradha"
}
# Remaining nakshatras => Copper (common convention in many sources)
def get_paya_from_nakshatra(nakshatra_name):
    if nakshatra_name in GOLD_PAYA_NAKS:
        return "Gold"
    if nakshatra_name in SILVER_PAYA_NAKS:
        return "Silver"
    if nakshatra_name in IRON_PAYA_NAKS:
        return "Iron"
    return "Copper"


# ---------- NAKSHATRA DEITY (Yujna) / canonical mapping ----------
NAKSHATRA_DEITY = {
    "Ashwini": "Ashvini Kumaras",
    "Bharani": "Yama",
    "Krittika": "Agni",
    "Rohini": "Brahma",
    "Mrigashira": "Soma (Chandra)",
    "Ardra": "Rudra",
    "Punarvasu": "Aditi",
    "Pushya": "Brihaspati",
    "Ashlesha": "Nagas",
    "Magha": "Pitris",
    "Purva Phalguni": "Bhaga",
    "Uttara Phalguni": "Aryaman",
    "Hasta": "Savitar",
    "Chitra": "Tvastar (Vishvakarma)",
    "Swati": "Vayu",
    "Vishakha": "Indra & Agni",
    "Anuradha": "Mitra",
    "Jyeshtha": "Indra",
    "Mula": "Nirrti",
    "Purva Ashadha": "Apah (Water Deity)",
    "Uttara Ashadha": "Vishwadevas",
    "Shravana": "Vishnu",
    "Dhanishta": "Vasus",
    "Shatabhisha": "Varuna",
    "Purva Bhadrapada": "Ajaikapada",
    "Uttara Bhadrapada": "Ahirbudhnya",
    "Revati": "Pushan"
}
def get_nakshatra_deity(nakshatra_name):
    return NAKSHATRA_DEITY.get(nakshatra_name, "")


# Tatva by signs
TATVA = {
    "Ari":"Agni","Leo":"Agni","Sag":"Agni",
    "Tau":"Prithvi","Vir":"Prithvi","Cap":"Prithvi",
    "Gem":"Vayu","Lib":"Vayu","Aqu":"Vayu",
    "Can":"Jala","Sco":"Jala","Pis":"Jala"
}

# Name alphabets per Nakshatra Pada
NAKSHATRA_PADA_ALPHABETS = {
    "Ashwini": ["Chu","Che","Cho","La"],
    "Bharani": ["Li","Lu","Le","Lo"],
    "Krittika": ["A","E","U","Ea"],
    "Rohini": ["O","Va","Vi","Vu"],
    "Mrigashira": ["Ve","Vo","Ka","Ki"],
    "Ardra": ["Ku","Kham","Ja","Ji"],
    "Punarvasu": ["Ju","Je","Jo","Kha"],
    "Pushya": ["Hu","He","Ho","Da"],
    "Ashlesha": ["De","Du","De","Do"],
    "Magha": ["Ma","Mi","Mu","Me"],
    "Purva Phalguni": ["Mo","Ta","Ti","Tu"],
    "Uttara Phalguni": ["Te","To","Pa","Pe"],
    "Hasta": ["Pu","Sha","Na","Tha"],
    "Chitra": ["Pe","Po","Ra","Ri"],
    "Swati": ["Ru","Re","Ro","Ta"],
    "Vishakha": ["Ti","Tu","Te","To"],
    "Anuradha": ["Na","Ni","Nu","Ne"],
    "Jyeshtha": ["No","Ya","Yi","Yu"],
    "Mula": ["Ye","Yo","Ba","Bi"],
    "Purva Ashadha": ["Bu","Dha","Pha","Da"],
    "Uttara Ashadha": ["Be","Bo","Ja","Ji"],
    "Shravana": ["Ju","Je","Jo","Khi"],
    "Dhanishta": ["Ga","Gi","Gu","Ge"],
    "Shatabhisha": ["Go","Sa","Si","Su"],
    "Purva Bhadrapada": ["Se","So","Da","Di"],
    "Uttara Bhadrapada": ["Du","Tha","Jha","Na"],
    "Revati": ["De","Do","Cha","Chi"]
}

def get_nakshatra_pada(degree):
    # Each nakshatra = 13°20' = 13.333...
    nakshatra_size = 13 + 20/60
    total_deg = degree % 360
    nak_index = int(total_deg // nakshatra_size)
    pada = int(((total_deg % nakshatra_size) / (nakshatra_size / 4))) + 1
    return NAKSHATRAS[nak_index], pada

def get_tithi(moon_deg, sun_deg):
    diff = (moon_deg - sun_deg + 360) % 360
    tithi_num = int(diff // 12) + 1  # 30 tithis
    paksha = "Shukla" if diff < 180 else "Krishna"
    return paksha + " " + TITHIS[(tithi_num-1) % 15], tithi_num

# def get_karana(tithi_num, moon_deg, sun_deg):
#     # Each tithi has 2 karanas (total 60, but repeating)
#     karana_index = (int(((moon_deg - sun_deg + 360) % 360) // 6)) % len(KARANAS)
#     return KARANAS[karana_index]

def get_yoga(sun_deg, moon_deg):
    yoga_num = int(((sun_deg + moon_deg) % 360) // (360/27))
    return YOGAS[yoga_num]

# Retrograde check
def is_retrograde(jd, planet_id):
    flag = swe.FLG_SIDEREAL
    xx, ret = swe.calc_ut(jd, planet_id, flag)
    speed = xx[3]
    return speed < 0

# Combustion check (Planet close to Sun)
def is_combust(planet_deg, sun_deg, orb=8):
    diff = abs((planet_deg - sun_deg + 180) % 360 - 180)  # shortest distance
    return diff < orb


# Karakas (simplified from Jaimini system)
def get_karaka(rank):
    karakas = ["Atmakaraka", "Amatyakaraka", "Bhratrikaraka", "Matrikaraka", 
               "Putrakaraka", "Gnatikaraka", "Darakaraka"]
    if rank < len(karakas):
        return karakas[rank]
    return None


# Avastha (very simplified version: by degree in sign)
def get_avastha(deg_in_sign):
    if deg_in_sign < 6: return "Bala (Infant)"
    elif deg_in_sign < 12: return "Kumara (Child)"
    elif deg_in_sign < 18: return "Yuva (Young)"
    elif deg_in_sign < 24: return "Vriddha (Mature)"
    else: return "Mrita (Old)"
    
def get_yanja_from_nakshatra_index(nak_index):
    """
    nak_index: 0-based index (0=Ashwini, 1=Bharani, ..., 26=Revati)
    Returns Poorva / Madhya / Para Yanja
    """
    if 0 <= nak_index <= 5:
        return "Poorva Yanja"
    elif 6 <= nak_index <= 17:
        return "Madhya Yanja"
    elif 18 <= nak_index <= 26:
        return "Para Yanja"
    else:
        return ""
    
def get_navamsa_chart(jd, planet_positions, asc_deg):
    """
    Compute Navamsa (D9) chart using sidereal positions.
    jd: Julian Day
    planet_positions: dict from D1 chart with {"deg": x, "sign": y}
    asc_deg: Ascendant degree from D1
    """

    # Helper: get navamsa sign index from planet longitude
    def get_navamsa_sign(longitude, sign_index):
        # which part of 3°20′
        part = int((longitude % 30) // (30/9))  # 0..8
        sign_type = sign_index % 3  # 0 movable, 1 fixed, 2 dual
        if sign_type == 0:  # movable
            start = sign_index
        elif sign_type == 1:  # fixed
            start = (sign_index + 8) % 12  # 9th sign
        else:  # dual
            start = (sign_index + 4) % 12  # 5th sign
        return (start + part) % 12

    # Ascendant navamsa
    asc_sign_index = int(asc_deg // 30)
    asc_nav_sign = get_navamsa_sign(asc_deg, asc_sign_index)

    # Prepare house → planets
    nav_house_planets = {i+1: [] for i in range(12)}
    nav_house_signs = {}

    # Ascendant = navamsa sign we just found
    for i in range(12):
        nav_house_signs[i+1] = SIGN_ABBR[(asc_nav_sign + i) % 12]

    # Compute navamsa position for planets
    nav_planet_positions = {}
    for pl, info in planet_positions.items():
        deg = info["deg"]
        sign_index = int(deg // 30)
        nav_sign_index = get_navamsa_sign(deg, sign_index)
        nav_planet_positions[pl] = {"sign": SIGNS[nav_sign_index]}
        # Place in house (whole sign from nav ascendant)
        house_num = ((nav_sign_index - asc_nav_sign + 12) % 12) + 1
        nav_house_planets[house_num].append(pl)

    return {
        "ascendant_navamsa": SIGNS[asc_nav_sign],
        "nav_planet_positions": nav_planet_positions,
        "nav_house_planets": nav_house_planets,
        "nav_house_signs": nav_house_signs
    }

def draw_navamsa_chart(navamsa_data):
    """
    Draw North Indian style Navamsa (D9) chart.
    navamsa_data = dict returned by get_navamsa_chart()
    """

    house_points = {
        1: [(100,75), (200,150), (300,75), (200,0)],
        2: [(0,0), (100,75), (200,0)],
        3: [(0,0), (0,150), (100,75)],
        4: [(0,150), (100,225), (200,150), (100,75)],
        5: [(0,150), (0,300), (100,225)],
        6: [(100,225), (0,300), (200,300)],
        7: [(100,225), (200,300), (300,225), (200,150)],
        8: [(300,225), (200,300), (400,300)],
        9: [(300,225), (400,300), (400,150)],
        10: [(300,75), (200,150), (300,225), (400,150)],
        11: [(300,75), (400,150), (400,0)],
        12: [(200,0), (300,75), (400,0)]
    }

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(0, 400)
    ax.set_ylim(300, 0)  # invert y-axis
    ax.axis("off")

    house_signs = navamsa_data["nav_house_signs"]
    house_planets = navamsa_data["nav_house_planets"]

    # Draw houses
    for house, points in house_points.items():
        polygon = plt.Polygon(points, closed=True, fill=None, edgecolor='black', lw=2)
        ax.add_patch(polygon)

        # House center
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)

        # Sign abbr + number
        sign_abbr = house_signs[house]
        # ax.text(center_x, center_y - 15, sign_abbr, ha="center", va="center", fontsize=10, color="green")
        ax.text(center_x, center_y +20, NUM_LIST[sign_abbr], ha="center", va="center", fontsize=10, color="orange")

        # Planets
        if house_planets.get(house):
            text = "\n".join([PLANET_ABBR[pl] for pl in house_planets[house]])
            ax.text(center_x, center_y + 10, text, ha="center", va="center", fontsize=9, color="blue")

    plt.tight_layout()

    # Save to base64
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    nav_chart_b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close()

    return nav_chart_b64

def get_ascendant_details(asc_deg,moon_deg):
    # Get cusp data (Lagna = cusp[1])
    # Zodiac sign
    sign_index = int(asc_deg // 30)
    sign_name = SIGNS[sign_index]
    sign_lord = SIGN_LORDS[SIGN_ABBR[sign_index]]

    # Nakshatra
    
    nak_name, pada = get_nakshatra_pada(asc_deg)
    nak_index = NAKSHATRAS.index(nak_name)
    # nak_lord = NAKSHATRA_LORDS[nak_name]

    # Pada
    sign_lord = SIGN_LORDS[SIGN_ABBR[sign_index]]
    nak_lord = NAKSHATRA_LORDS[nak_index]

    return {
        "degree": round(asc_deg, 2)%30,
        "sign": sign_name,
        "nakshatra": nak_name,
        "avastha": "--",
        "relation": "--",
        "retrograde": False,
        "combust": False,
        "sign_lord": sign_lord,
        "nakshatra_lord": nak_lord,
        "house": 1,
        "pada":pada,
        "karka":"--"
    }
    
def assign_house_to_planets(planet_positions, house_planets):
    """
    Adds 'house' key to each planet in planet_positions
    using the house_planets dict.
    """
    for house_num, planets in house_planets.items():
        for pl in planets:
            if pl in planet_positions:
                planet_positions[pl]["house"] = house_num
    return planet_positions

def get_kundali_chart(year, month, day, hour, minute, lat, lon, tz_offset):
    # Set sidereal mode (Lahiri ayanamsa)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Convert local time to UTC
    dt = datetime(year, month, day, hour, minute)
    dt_utc = dt - timedelta(hours=tz_offset)
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60)

    # Houses (Whole sign)
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'W', swe.FLG_SIDEREAL)
    asc_deg = ascmc[0]

    # Determine Ascendant sign
    asc_sign_index = int(asc_deg // 30)

    # Planet positions (sidereal)
    planet_positions = {}
    for pl in PLANETS:
        if pl == "Rahu":
            deg = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
        elif pl == "Ketu":
            deg = (swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0] + 180) % 360
        else:
            deg = swe.calc_ut(jd, getattr(swe, pl.upper()), swe.FLG_SIDEREAL)[0][0]
        sign_index = int(deg // 30)
        deg_in_sign = deg % 30
        nak, pada = get_nakshatra_pada(deg)
        
        sign_lord = SIGN_LORDS[SIGN_ABBR[sign_index]]
        nak_lord = NAKSHATRA_LORDS[NAKSHATRAS.index(nak)]

        # Retrograde & Combustion
        retro = False
        combust = False
        if pl not in ["Rahu", "Ketu", "Sun"]:
            retro = is_retrograde(jd, getattr(swe, pl.upper()))
            combust = is_combust(deg, planet_positions.get("Sun", {}).get("deg", deg), orb=8)
        elif pl in ["Rahu", "Ketu"]:
            retro = True
            combust = is_combust(deg, planet_positions.get("Sun", {}).get("deg", deg), orb=8)

        # Relation
        relation = "neutral"
        if "Sun" in planet_positions:
            if pl in PLANET_RELATIONS["Sun"]["friends"]:
                relation = "friend"
            elif pl in PLANET_RELATIONS["Sun"]["enemies"]:
                relation = "enemy"

        # Avastha
        avastha = get_avastha(deg_in_sign)

        planet_positions[pl] = {"deg": deg, "sign": SIGNS[sign_index],'nakshatra':nak,"degree":deg % 30,
                                'avastha':avastha,"relation":relation,'pada':pada,'retro':retro,
                                'combust':combust,'sign_lord':sign_lord,'nak_lord':nak_lord}
        
        sorted_planets = sorted(
        [(pl, info["deg"] % 30) for pl, info in planet_positions.items() if pl not in ["Rahu","Ketu"]],
        key=lambda x: -x[1] )
    for i, (pl, _) in enumerate(sorted_planets):
        planet_positions[pl]["karaka"] = get_karaka(i)
    
    # Assign planets to houses based on whole sign
    house_planets = {i+1: [] for i in range(12)}
    for pl, info in planet_positions.items():
        sign_index = int(info["deg"] // 30)
        house_num = ((sign_index - asc_sign_index + 12) % 12) + 1
        house_planets[house_num].append(pl)
    # Zodiac signs in houses
    house_signs = {}
    for i in range(12):
        house_index = (asc_sign_index + i) % 12
        house_signs[i+1] = SIGN_ABBR[house_index]

    # Define polygon points for each house in North Indian style, counter-clockwise
    house_points = {
        1: [(100,75), (200,150), (300,75), (200,0)],  # Top diamond (House 1)
        2: [(0,0), (100,75), (200,0)],  # Top-left upper triangle (formerly 12)
        3: [(0,0), (0,150), (100,75)],  # Top-left lower triangle (formerly 11)
        4: [(0,150), (100,225), (200,150), (100,75)],  # Left diamond (formerly 10)
        5: [(0,150), (0,300), (100,225)],  # Bottom-left upper triangle (formerly 9)
        6: [(100,225), (0,300), (200,300)],  # Bottom-left lower triangle (formerly 8)
        7: [(100,225), (200,300), (300,225), (200,150)],  # Bottom diamond (House 7)
        8: [(300,225), (200,300), (400,300)],  # Bottom-right lower triangle (formerly 6)
        9: [(300,225), (400,300), (400,150)],  # Bottom-right upper triangle (formerly 5)
        10: [(300,75), (200,150), (300,225), (400,150)],  # Right diamond (formerly 4)
        11: [(300,75), (400,150), (400,0)],  # Top-right lower triangle (formerly 3)
        12: [(200,0), (300,75), (400,0)]  # Top-right upper triangle (formerly 2)
    }

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(0, 400)
    ax.set_ylim(300, 0)  # Invert y-axis to match SVG coordinate system
    ax.axis("off")

    # Draw house polygons
    for house, points in house_points.items():
        polygon = plt.Polygon(points, closed=True, fill=None, edgecolor='black', lw=2)
        ax.add_patch(polygon)

        # Calculate center for text placement
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)

        # House sign abbr
        # ax.text(center_x, center_y - 10, house_signs[house], ha='center', va='center', fontsize=10, color='green')
        ax.text(center_x, center_y +20, NUM_LIST[house_signs[house]], ha='center', va='center', fontsize=10, color='orange')

        # Planets with abbreviations and degrees within sign
        if house_planets.get(house):
            text = "\n".join([f"{PLANET_ABBR[pl]} {(planet_positions[pl]['deg'] % 30):.2f}°" for pl in house_planets[house]])
            ax.text(center_x, center_y + 10, text, ha='center', va='center', fontsize=9, color='blue')

    plt.tight_layout()

    # Save chart to base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    kundali_chart = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    # Avakhada details
    sun_deg = planet_positions["Sun"]["deg"]
    moon_deg = planet_positions["Moon"]["deg"]

    # Lagna sign
    lagna_sign = house_signs[1]

    # Moon sign
    moon_sign = planet_positions["Moon"]["sign"]

    # Nakshatra & Pada of Moon
    moon_nak = planet_positions["Moon"]["nakshatra"]
    moon_pada = planet_positions["Moon"]["pada"]

    # Panchanga
    weekday = WEEKDAYS[dt.weekday()]
    tithi, tithi_num = get_tithi(moon_deg, sun_deg)
    karana = get_karana_from_degrees(sun_deg,moon_deg)
    yoga = get_yoga(sun_deg, moon_deg)
    
    moon_sign_abbr = SIGN_ABBR[int(moon_deg // 30)]
    moon_sign_lord = SIGN_LORDS[moon_sign_abbr]

    varna = VARNA.get(moon_sign_abbr, "")
    vashya = VASHYA.get(moon_sign_abbr, "")
    yoni = YONI.get(moon_nak, "")
    gana = GANA.get(moon_nak, "")
    nadi = NADI.get(moon_nak, "")
    tatva = TATVA.get(moon_sign_abbr, "")
    paya = get_paya_from_nakshatra(moon_nak)
    nak_deity = get_nakshatra_deity(moon_nak)
    
    nak_index = int((moon_deg % 360) // (360/27))  # 0..26
    yujna = get_yanja_from_nakshatra_index(nak_index)
    # Name alphabet suggestion
    pada_index = moon_pada - 1
    name_alphabet = NAKSHATRA_PADA_ALPHABETS.get(moon_nak, [""]*4)[pada_index]
    ascendent = get_ascendant_details(asc_deg,moon_deg)
    
    planet_positions = assign_house_to_planets(planet_positions,house_planets)
    avakhada = {
        "weekday": weekday,
        "lagna": lagna_sign,
        "moon_sign": moon_sign,
        "moon_nakshatra": moon_nak,
        "moon_pada": moon_pada,
        "tithi": tithi,
        "karana": karana,
        "yoga": yoga,
        "lat": lat,
        "lon": lon,
        "dob": dt.strftime("%d-%m-%Y"),
        "tob": dt.strftime("%H:%M"),
        "varna": varna,
        "vashya": vashya,
        "yoni": yoni,
        "gana": gana,
        "nadi": nadi,
        "sign": moon_sign,
        "sign_lord": moon_sign_lord,
        "paya": paya,
        "tatva": tatva,
        "yujna": yujna,
        "name_alphabet": name_alphabet,
        "nak_deity":nak_deity
    }
    
    navamsa = get_navamsa_chart(jd, planet_positions, asc_deg)
    navamsa_chart = draw_navamsa_chart(navamsa)
    
    return {
        "ascendant": ascendent,
        "houses": cusps,
        "planet_positions": planet_positions,
        "house_planets": house_planets,
        "house_signs": house_signs,
        "kundali_chart": kundali_chart,
        "avakhada":avakhada,
        "navamsa_chart":navamsa_chart
    }