# Requires: swisseph, geopy, timezonefinder, pytz
# pip install pyswisseph geopy timezonefinder pytz

import swisseph as swe
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from timezonefinderL import TimezoneFinder
import pytz
import itertools
import math

# -------------------------
# Constants
# -------------------------
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshta",
    "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada","Revati"
]

# Rashi ruler map (for Graha Maitri)
RASHI_RULER = {
    "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon","Leo":"Sun","Virgo":"Mercury",
    "Libra":"Venus","Scorpio":"Mars","Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter"
}

# -------------------------
# Geocode + Timezone helper
# -------------------------
def geocode_place_timezone(place_name: str, user_agent="astro_ai_app", timeout=10):
    """
    Returns (lat, lon, tzinfo) or (None, None, None) if geocoding fails.
    """
    try:
        geolocator = Nominatim(user_agent=user_agent, timeout=timeout)
        loc = geolocator.geocode(place_name)
        if not loc:
            return None, None, None
        lat, lon = float(loc.latitude), float(loc.longitude)
        tf = TimezoneFinder()
        tzname = tf.timezone_at(lng=lon, lat=lat)
        if tzname:
            tz = pytz.timezone(tzname)
            return lat, lon, tz
    except Exception:
        return None, None, None
    return None, None, None

# -------------------------
# Astronomy helpers
# -------------------------
def sidereal_longitude(body, jd_ut):
    """
    Return sidereal (Lahiri) longitude of body at julian day UT (degrees).
    """
    lon = swe.calc_ut(jd_ut, body)[0][0]
    ay = swe.get_ayanamsa_ut(jd_ut)  # Lahiri by default in swisseph
    lon_sid = (lon - ay) % 360.0
    return lon_sid

def rashi_from_deg(lon_deg):
    return int(lon_deg // 30)  # 0..11

def nakshatra_from_deg(lon_deg):
    span = 360.0 / 27.0
    index = int(lon_deg // span)  # 0..26
    pada = int(((lon_deg % span) / span) * 4) + 1  # 1..4
    return index, pada

# -------------------------
# Improved Vashya / Yoni / Graha-Maitri tables
# -------------------------

# 1) VASHYA via nakshatra mapping (27 entries)
NAKSHATRA_TO_VASHYA = [
    # 0 Ashwini .. 26 Revati
    "Chatushpada","Chatushpada","Chatushpada","Jalchar","Jalchar","Vanchar",
    "Manushya","Manushya","Keet","Chatushpada","Chatushpada","Chatushpada",
    "Manushya","Vanchar","Vanchar","Manushya","Manushya","Keet",
    "Keet","Chatushpada","Chatushpada","Manushya","Jalchar","Jalchar",
    "Vanchar","Vanchar","Keet"
]

VASHYA_SCORE = {
    "Chatushpada": {"Chatushpada": 2, "Manushya": 1, "Jalchar": 1, "Vanchar": 0, "Keet": 2},
    "Manushya":    {"Chatushpada": 1, "Manushya": 2, "Jalchar": 1, "Vanchar": 1, "Keet": 0},
    "Jalchar":     {"Chatushpada": 1, "Manushya": 1, "Jalchar": 2, "Vanchar": 2, "Keet": 1},
    "Vanchar":     {"Chatushpada": 0, "Manushya": 1, "Jalchar": 2, "Vanchar": 2, "Keet": 0},
    "Keet":        {"Chatushpada": 2, "Manushya": 0, "Jalchar": 1, "Vanchar": 0, "Keet": 2},
}

def vashya_kuta_score_from_nakshatra(nak1_idx, nak2_idx):
    g1 = NAKSHATRA_TO_VASHYA[nak1_idx]
    g2 = NAKSHATRA_TO_VASHYA[nak2_idx]
    return float(VASHYA_SCORE.get(g1, {}).get(g2, 0.0))

# 2) Yoni: 14 categories + 14x14 matrix (0..4)
# A canonical 14-category mapping may differ; this is flexible and editable.
YONI_LIST = [
    "Ashva","Gaja","Aja","Vrisha","Vrishabha","Simha","Nara","Vriksha",
    "Mriga","Sinha","Matsya","Vrisha2","Chatush","Vishnu"
]

# Build symmetric matrix with reasonable defaults (same yoni=4, many neutral=2).
YONI_SCORE = {y: {} for y in YONI_LIST}
def _set_yoni(a, b, val):
    YONI_SCORE[a][b] = val
    YONI_SCORE[b][a] = val

for y in YONI_LIST:
    _set_yoni(y, y, 4.0)

# Some favorable pairs (illustrative)
_pairs_high = [("Ashva","Gaja"), ("Aja","Vrisha"), ("Nara","Vriksha"), ("Matsya","Vrisha2"), ("Chatush","Vishnu")]
for a,b in _pairs_high:
    _set_yoni(a, b, 3.0)

# Fill remaining undefined pairs with neutral (2.0)
for a in YONI_LIST:
    for b in YONI_LIST:
        if b not in YONI_SCORE[a]:
            _set_yoni(a, b, 2.0)

# A few explicit incompatible pairs
_incompatible = [("Ashva","Vrisha2"), ("Gaja","Chatush"), ("Aja","Vishnu")]
for a,b in _incompatible:
    _set_yoni(a,b,0.0)

# Map 27 nakshatras -> 14 yonis (editable)
NAK_TO_YONI = [
    "Ashva","Gaja","Aja","Vrisha","Vrishabha","Simha","Nara","Vriksha","Mriga",
    "Sinha","Matsya","Vrisha2","Chatush","Vishnu","Ashva","Gaja","Aja","Vrisha",
    "Vrishabha","Simha","Nara","Vriksha","Mriga","Sinha","Matsya","Vrisha2","Chatush"
]

def yoni_kuta_score(nak1_idx, nak2_idx):
    y1 = NAK_TO_YONI[nak1_idx]
    y2 = NAK_TO_YONI[nak2_idx]
    return float(YONI_SCORE.get(y1, {}).get(y2, 0.0))

# 3) Full Graha Maitri table (0..5)
PLANETS_FULL = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
GRAHA_MAITRI_SCORE = {p: {} for p in PLANETS_FULL}
def _set_gscore(a,b,val):
    GRAHA_MAITRI_SCORE[a][b] = val
    GRAHA_MAITRI_SCORE[b][a] = val

for p in PLANETS_FULL:
    _set_gscore(p, p, 5.0)

strong_pairs = [
    ("Sun","Moon"), ("Sun","Mars"), ("Sun","Jupiter"),
    ("Moon","Mercury"), ("Mars","Jupiter"),
    ("Mercury","Venus"), ("Jupiter","Venus"), ("Mercury","Saturn"),
    ("Venus","Saturn")
]
for a,b in strong_pairs:
    _set_gscore(a,b,5.0)

neutral_pairs = [
    ("Sun","Mercury"), ("Moon","Jupiter"), ("Moon","Venus"),
    ("Mars","Mercury"), ("Jupiter","Saturn"), ("Mars","Saturn")
]
for a,b in neutral_pairs:
    if b not in GRAHA_MAITRI_SCORE[a]:
        _set_gscore(a,b,3.0)

enemy_pairs_0 = [
    ("Sun","Saturn"), ("Moon","Mars"), ("Mercury","Mars"), ("Jupiter","Mercury")
]
for a,b in enemy_pairs_0:
    _set_gscore(a,b,0.0)

# Remaining unspecified pairs -> mild default 2
for a in PLANETS_FULL:
    for b in PLANETS_FULL:
        if b not in GRAHA_MAITRI_SCORE[a]:
            _set_gscore(a, b, 2.0)

def graha_maitri_score(rashi1, rashi2):
    lord1 = RASHI_RULER.get(rashi1)
    lord2 = RASHI_RULER.get(rashi2)
    if lord1 is None or lord2 is None:
        return 2.0
    return float(GRAHA_MAITRI_SCORE.get(lord1, {}).get(lord2, 2.0))

# -------------------------
# Other Kuta functions (Tara, Gana, Bhakoot, Nadi, Varna)
# -------------------------
def varna_kuta_score(rashi1, rashi2):
    VARNA_OF_RASHI = {
        "Aries": 3, "Leo": 3, "Sagittarius": 3,
        "Taurus": 2, "Virgo": 2, "Capricorn": 2,
        "Gemini": 1, "Libra": 1, "Aquarius": 1,
        "Cancer": 4, "Scorpio": 4, "Pisces": 4
    }
    v1 = VARNA_OF_RASHI[rashi1]
    v2 = VARNA_OF_RASHI[rashi2]
    return 1.0 if v1 >= v2 else 0.0

def tara_kuta_score(nak1, nak2):
    def single_count(a, b):
        return (b - a) % 27 + 1
    cnt1 = single_count(nak1, nak2)
    cnt2 = single_count(nak2, nak1)
    rem1 = cnt1 % 9
    rem2 = cnt2 % 9
    def is_ausp(rem):
        return rem in (0,2,4,6,8)
    if is_ausp(rem1) and is_ausp(rem2):
        return 3.0
    if is_ausp(rem1) or is_ausp(rem2):
        return 1.5
    return 0.0

def gana_kuta_score(nak1, nak2):
    GANA_OF_NAKSHATRA = [
        "Deva","Manushya","Rakshasa","Manushya","Deva","Rakshasa","Deva","Deva","Rakshasa",
        "Manushya","Manushya","Manushya","Deva","Rakshasa","Deva","Rakshasa","Deva","Rakshasa",
        "Rakshasa","Rakshasa","Deva","Deva","Deva","Rakshasa","Manushya","Manushya","Deva"
    ]
    g1 = GANA_OF_NAKSHATRA[nak1]
    g2 = GANA_OF_NAKSHATRA[nak2]
    if g1 == g2:
        return 6.0
    pair = (g1, g2)
    if (pair == ("Deva","Manushya")) or (pair == ("Manushya","Deva")):
        return 5.0
    if (pair == ("Manushya","Rakshasa")) or (pair == ("Rakshasa","Manushya")):
        return 1.0
    if (pair == ("Deva","Rakshasa")) or (pair == ("Rakshasa","Deva")):
        return 0.0
    return 2.0

def bhakoot_kuta_score(rashi1_idx, rashi2_idx):
    s = ((rashi2_idx - rashi1_idx) % 12) + 1  # 1..12
    full7 = {1,7,3,11,4,10}
    zero_set = {2,12,5,9,6,8}
    if s in full7:
        return 7.0
    if s in zero_set:
        return 0.0
    return 4.0

def nadi_kuta_score(nak1, nak2):
    NADIS = ["Adi", "Madhya", "Antya"] * 9
    n1 = NADIS[nak1]
    n2 = NADIS[nak2]
    return 0.0 if n1 == n2 else 8.0

# -------------------------
# Main matching routine
# -------------------------
# (Assumes the previous full implementation is present: imports, constants, helper tables,
#  and helper functions like sidereal_longitude, nakshatra_from_deg, etc.)

def perform_kundali_matching(p1_birth_data, p2_birth_data, use_sidereal=True):
    """
    Extended perform_kundali_matching that returns Ashtakoota breakdown plus additional predictions.
    Input format same as before.
    """
    # Helper to get lat/lon/tz
    def extract_latlon_tz(d):
        if d.get('lat') is not None and d.get('lon') is not None and d.get('timezone'):
            return float(d['lat']), float(d['lon']), d['timezone']
        lat, lon, tz = geocode_place_timezone(d.get('Place'))
        if lat is None:
            raise ValueError(f"Could not geocode place: {d.get('Place')}")
        return lat, lon, tz

    lat1, lon1, tz1 = extract_latlon_tz(p1_birth_data)
    lat2, lon2, tz2 = extract_latlon_tz(p2_birth_data)

    # Convert local date/time to Julian day UT
    def to_jd_ut(date_str, time_str, tz):
        Y, M, D = [int(x) for x in date_str.split("-")]
        hh, mm = [int(x) for x in time_str.split(":")]
        local_dt = datetime(Y, M, D, hh, mm)
        aware = tz.localize(local_dt)
        utc_dt = aware.astimezone(pytz.utc)
        jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0)
        return jd

    jd1 = to_jd_ut(p1_birth_data['Date'], p1_birth_data['Time'], tz1)
    jd2 = to_jd_ut(p2_birth_data['Date'], p2_birth_data['Time'], tz2)

    # compute ascendant degrees for house-based checks (needs lat/lon)
    asc1, cusps1 = swe.houses(jd1, lat1, lon1, b'A')
    asc2, cusps2 = swe.houses(jd2, lat2, lon2, b'A')
    asc1_deg = asc1[0]
    asc2_deg = asc2[0]

    # Compute sidereal moon longitudes (for kuta calculations)
    moon1_lon = sidereal_longitude(swe.MOON, jd1) if use_sidereal else swe.calc_ut(jd1, swe.MOON)[0][0]
    moon2_lon = sidereal_longitude(swe.MOON, jd2) if use_sidereal else swe.calc_ut(jd2, swe.MOON)[0][0]

    # Rashi / Nakshatra / Pada
    r1_idx = rashi_from_deg(moon1_lon)
    r2_idx = rashi_from_deg(moon2_lon)
    r1_name = SIGNS[r1_idx]
    r2_name = SIGNS[r2_idx]
    nak1_idx, pada1 = nakshatra_from_deg(moon1_lon)
    nak2_idx, pada2 = nakshatra_from_deg(moon2_lon)
    nak1_name = NAKSHATRAS[nak1_idx]
    nak2_name = NAKSHATRAS[nak2_idx]

    # Compute kuta scores (use the improved functions defined earlier)
    scores = {}
    scores['Varna'] = (varna_kuta_score(r1_name, r2_name), 1.0)
    scores['Vashya'] = (vashya_kuta_score_from_nakshatra(nak1_idx, nak2_idx), 2.0)
    scores['Tara']  = (tara_kuta_score(nak1_idx, nak2_idx), 3.0)
    scores['Yoni']  = (yoni_kuta_score(nak1_idx, nak2_idx), 4.0)
    scores['Graha Maitri'] = (graha_maitri_score(r1_name, r2_name), 5.0)
    scores['Gana']  = (gana_kuta_score(nak1_idx, nak2_idx), 6.0)
    scores['Bhakoot'] = (bhakoot_kuta_score(r1_idx, r2_idx), 7.0)
    scores['Nadi']  = (nadi_kuta_score(nak1_idx, nak2_idx), 8.0)

    # Normalize/clip each score to its max and build breakdown
    total_score = 0.0
    total_possible = 0.0
    breakdown = {}
    for k, (val, mx) in scores.items():
        clipped = float(max(0.0, min(val, mx)))
        breakdown[k] = {"score": clipped, "max": float(mx)}
        total_score += clipped
        total_possible += float(mx)

    # Determine match status
    if total_score >= 32:
        status = "Best Match"
    elif total_score >= 24:
        status = "Very Good Match"
    elif total_score >= 18:
        status = "Good Match"
    elif total_score >= 10:
        status = "Average Match"
    else:
        status = "Poor Match"

    # -------------------------
    # Additional predictions
    # -------------------------
    # Helpers for house calculation
    def house_number_of_deg(deg, asc_deg):
        # returns 1..12
        house_num = int(((deg - asc_deg + 360) % 360) // 30) + 1
        if house_num > 12:
            house_num -= 12
        return house_num

    # Compute Mars sidereal longitudes and house placement for both persons
    mars1_lon = sidereal_longitude(swe.MARS, jd1) if use_sidereal else swe.calc_ut(jd1, swe.MARS)[0][0]
    mars2_lon = sidereal_longitude(swe.MARS, jd2) if use_sidereal else swe.calc_ut(jd2, swe.MARS)[0][0]
    mars1_house = house_number_of_deg(mars1_lon, asc1_deg)
    mars2_house = house_number_of_deg(mars2_lon, asc2_deg)

    additional_predictions = []

    # Mangal Dosha: common rule - Mars in houses 1,2,4,7,8,12 => Manglik
    mangal_houses = {1,2,4,7,8,12}
    for i, (name, mars_house) in enumerate([("Person 1", mars1_house), ("Person 2", mars2_house)], start=1):
        if mars_house in mangal_houses:
            additional_predictions.append({
                "Name": f"Mangal Dosha ({'P1' if i==1 else 'P2'})",
                "Nature": "Warning",
                "Description": f"{name} is Manglik — Mars is in house {mars_house}. "
                               "Mangliks can cause friction in marriage unless both partners are Manglik or suitable remedies/matching are considered."
            })
        else:
            additional_predictions.append({
                "Name": f"Mangal Dosha ({'P1' if i==1 else 'P2'})",
                "Nature": "Neutral",
                "Description": f"{name} is not Manglik (Mars in house {mars_house})."
            })

    # Nadi Dosha (if Nadi score == 0)
    if breakdown['Nadi']['score'] == 0.0:
        additional_predictions.append({
            "Name": "Nadi Dosha",
            "Nature": "Warning",
            "Description": "Nadi Dosha present — usually considered serious (hereditary/health compatibility). Further detailed analysis recommended."
        })
    else:
        additional_predictions.append({
            "Name": "Nadi Check",
            "Nature": "Positive",
            "Description": f"Nadi different (score {breakdown['Nadi']['score']}/{breakdown['Nadi']['max']}). No Nadi Dosha."
        })

    # Bhakoot Dosha
    if breakdown['Bhakoot']['score'] == 0.0:
        additional_predictions.append({
            "Name": "Bhakoot Dosha",
            "Nature": "Warning",
            "Description": "Bhakoot Dosha present — may indicate trouble with material harmony, finances or family. Consider deeper chart analysis."
        })
    else:
        additional_predictions.append({
            "Name": "Bhakoot Check",
            "Nature": "Neutral",
            "Description": f"Bhakoot score: {breakdown['Bhakoot']['score']}/{breakdown['Bhakoot']['max']}."
        })

    # Varna
    if breakdown['Varna']['score'] < 1.0:
        additional_predictions.append({
            "Name": "Varna Compatibility",
            "Nature": "Caution",
            "Description": f"Varna mismatch (score {breakdown['Varna']['score']}/{breakdown['Varna']['max']}). "
                           "This may imply differing temperament / life-roles; not a standalone disqualification but worth noting."
        })
    else:
        additional_predictions.append({
            "Name": "Varna Compatibility",
            "Nature": "Positive",
            "Description": "Varna compatible."
        })

    # Vashya
    vashya_score = breakdown['Vashya']['score']
    if vashya_score <= 0.5:
        vashya_nature = "Caution"
        vashya_desc = "Vashya compatibility is weak — challenges in mutual influence/attraction may exist."
    elif vashya_score < breakdown['Vashya']['max']:
        vashya_nature = "Neutral"
        vashya_desc = "Vashya partially compatible."
    else:
        vashya_nature = "Positive"
        vashya_desc = "Vashya compatibility strong."
    additional_predictions.append({
        "Name": "Vashya",
        "Nature": vashya_nature,
        "Description": f"{vashya_desc} (score {vashya_score}/{breakdown['Vashya']['max']})."
    })

    # Yoni
    yoni_score = breakdown['Yoni']['score']
    if yoni_score <= 1.0:
        yoni_n = "Warning"
        yoni_d = "Yoni is incompatible — sexual/temperamental compatibility may be poor. Consider remedies or deeper study."
    elif yoni_score < breakdown['Yoni']['max']:
        yoni_n = "Neutral"
        yoni_d = "Yoni is partially compatible."
    else:
        yoni_n = "Positive"
        yoni_d = "Yoni compatibility is good."
    additional_predictions.append({
        "Name": "Yoni",
        "Nature": yoni_n,
        "Description": f"{yoni_d} (score {yoni_score}/{breakdown['Yoni']['max']})."
    })

    # Graha Maitri
    graha_score = breakdown['Graha Maitri']['score']
    if graha_score <= 1.0:
        gm_n = "Caution"
        gm_d = "Graha Maitri is weak — fundamental temperament/lord compatibility is poor."
    elif graha_score < breakdown['Graha Maitri']['max']:
        gm_n = "Neutral"
        gm_d = "Graha Maitri is moderate."
    else:
        gm_n = "Positive"
        gm_d = "Graha Maitri strong — planetary lords are friendly."
    additional_predictions.append({
        "Name": "Graha Maitri",
        "Nature": gm_n,
        "Description": f"{gm_d} (score {graha_score}/{breakdown['Graha Maitri']['max']})."
    })

    # Tara
    tara_score = breakdown['Tara']['score']
    if tara_score == 0.0:
        additional_predictions.append({
            "Name": "Tara",
            "Nature": "Warning",
            "Description": "Tara Koota gives 0 points — indicates inauspicious timings between natal constellations. Consider deeper analysis."
        })
    else:
        additional_predictions.append({
            "Name": "Tara",
            "Nature": "Neutral",
            "Description": f"Tara score: {tara_score}/{breakdown['Tara']['max']}."
        })

    # Gana summary (Gana type of both parties and a note)
    # Determine each person's gana via nakshatra
    GANA_OF_NAKSHATRA = [
        "Deva","Manushya","Rakshasa","Manushya","Deva","Rakshasa","Deva","Deva","Rakshasa",
        "Manushya","Manushya","Manushya","Deva","Rakshasa","Deva","Rakshasa","Deva","Rakshasa",
        "Rakshasa","Rakshasa","Deva","Deva","Deva","Rakshasa","Manushya","Manushya","Deva"
    ]
    g1 = GANA_OF_NAKSHATRA[nak1_idx]
    g2 = GANA_OF_NAKSHATRA[nak2_idx]
    if g1 == g2:
        additional_predictions.append({
            "Name": "Gana",
            "Nature": "Positive",
            "Description": f"Both belong to {g1} gana — temperamentally aligned."
        })
    else:
        additional_predictions.append({
            "Name": "Gana",
            "Nature": "Neutral",
            "Description": f"Different ganas: {g1} vs {g2}. Compatibility depends on other factors (Gana score: {breakdown['Gana']['score']}/{breakdown['Gana']['max']})."
        })

    # Quick summary / suggestion
    warnings = [p for p in additional_predictions if p['Nature'] in ("Warning", "Caution")]
    if warnings:
        additional_predictions.insert(0, {
            "Name": "Summary",
            "Nature": "Advisory",
            "Description": f"{len(warnings)} potential issue(s) detected (e.g., Mangal/Nadi/Bhakoot/low koota scores). Recommend detailed chart-level analysis and traditional remedies if desired."
        })
    else:
        additional_predictions.insert(0, {
            "Name": "Summary",
            "Nature": "Positive",
            "Description": "No major doshas detected in the Ashtakoota comparison. Still consider full chart analysis for finer details."
        })

    # Final result object (includes ascendants, cusps etc.)
    result = {
        "p1": {
            "rashi": r1_name, "rashi_index": int(r1_idx),
            "nakshatra": nak1_name, "nakshatra_index": int(nak1_idx), "pada": int(pada1),
            "moon_lon_sidereal": float(moon1_lon),
            "ascendant_deg": float(asc1_deg),
            "mars_deg_sidereal": float(mars1_lon),
            "mars_house": int(mars1_house)
        },
        "p2": {
            "rashi": r2_name, "rashi_index": int(r2_idx),
            "nakshatra": nak2_name, "nakshatra_index": int(nak2_idx), "pada": int(pada2),
            "moon_lon_sidereal": float(moon2_lon),
            "ascendant_deg": float(asc2_deg),
            "mars_deg_sidereal": float(mars2_lon),
            "mars_house": int(mars2_house)
        },
        "breakdown": breakdown,
        "total_score": float(total_score),
        "total_possible": float(total_possible),
        "match_status": status,
        "additional_predictions": additional_predictions
    }

    return result