# utils/panchang.py  (drop-in)
import math
from datetime import datetime, timedelta, date, time
import swisseph as swe

# ensure sidereal Lahiri if you want sidereal calculations
swe.set_sid_mode(swe.SIDM_LAHIRI)

# Constants (trimmed/used)
TITHI_SHORT = [
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dvadashi",
    "Trayodashi", "Chaturdashi", "Purnima/Amavasya"
]

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
    "Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta",
    "Chitra","Swati","Vishakha","Anuradha","Jyeshta","Mula","Purva Ashadha",
    "Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
    "Uttara Bhadrapada","Revati"
]

YOGAS = [
    "Vishkumbha","Preeti","Ayushman","Saubhagya","Shobhana","Atiganda","Sukarma",
    "Dhriti","Shoola","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana","Vajra",
    "Siddhi","Vyatipata","Variyan","Parigha","Shiva","Siddha","Sadhya","Shubha",
    "Shukla","Brahma","Indra","Vaidhriti"
]

WEEKDAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

def _normalize_angle(a):
    return a % 360.0

def _deg2rad(d):
    return d * math.pi / 180.0

def _rad2deg(r):
    return r * 180.0 / math.pi

def sunrise_sunset_noaa(year, month, day, lat, lon, tz_offset_hours=5.5):
    """
    Returns (sunrise_dt_local, sunset_dt_local) as naive datetimes in local time (tz offset applied).
    Algorithm adapted from NOAA solar calculations.
    tz_offset_hours = local timezone offset in hours (e.g. IST = +5.5)
    """
    # helper funcs
    def _calc_for_event(is_sunrise):
        # 1) day of year
        dt = date(year, month, day)
        N = dt.timetuple().tm_yday

        lngHour = lon / 15.0
        # approximate time in days
        t = N + ((6 - lngHour) / 24.0) if is_sunrise else N + ((18 - lngHour) / 24.0)

        # Sun's mean anomaly
        M = (0.9856 * t) - 3.289

        # Sun's true longitude
        L = M + (1.916 * math.sin(_deg2rad(M))) + (0.020 * math.sin(_deg2rad(2*M))) + 282.634
        L = _normalize_angle(L)

        # Sun's right ascension
        RA = _rad2deg(math.atan2(0.91764 * math.sin(_deg2rad(L)), math.cos(_deg2rad(L))))
        RA = _normalize_angle(RA)
        RA = RA / 15.0  # hours

        # Sun's declination
        sinDec = 0.39782 * math.sin(_deg2rad(L))
        cosDec = math.cos(math.asin(sinDec))

        # Sun's local hour angle
        zenith = 90.833  # official
        cosH = (math.cos(_deg2rad(zenith)) - (math.sin(_deg2rad(lat)) * sinDec)) / (math.cos(_deg2rad(lat)) * cosDec)

        if cosH > 1:
            return None  # sun never rises
        if cosH < -1:
            return None  # sun never sets

        H = (360 - _rad2deg(math.acos(cosH))) / 15.0 if is_sunrise else _rad2deg(math.acos(cosH)) / 15.0

        # local mean time of rising/setting
        T = H + RA - (0.06571 * t) - 6.622

        # UT
        UT = T - lngHour
        UT = UT % 24.0

        # local time
        localT = UT + tz_offset_hours
        # normalize to 0..24 and then to hours/minutes
        localT = localT % 24.0
        hour = int(localT)
        minute = int((localT - hour) * 60)
        return datetime(year, month, day, hour, minute)

    sunrise = _calc_for_event(is_sunrise=True)
    sunset = _calc_for_event(is_sunrise=False)

    # If algorithm returns None (polar day/night), fallback to simple approximate:
    if sunrise is None or sunset is None:
        # fallback: use simple day/night split approx (sunrise = 06:00, sunset = 18:00)
        today = datetime(year, month, day)
        sunrise = today.replace(hour=6, minute=0)
        sunset = today.replace(hour=18, minute=0)

    return sunrise, sunset

CHO_DAY_ORDER = [
    ["Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Chal", "Labh", "Amrit"],
    ["Rog", "Udveg", "Chal", "Labh", "Amrit", "Kaal", "Shubh", "Rog"],
    ["Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Chal", "Labh"],
    ["Shubh", "Rog", "Udveg", "Chal", "Labh", "Amrit", "Kaal", "Shubh"],
    ["Chal", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Chal"],
    ["Kaal", "Shubh", "Rog", "Udveg", "Chal", "Labh", "Amrit", "Kaal"],
    ["Udveg", "Chal", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg"],
]

CHO_NIGHT_ORDER = [
    ["Chal", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Chal"],
    ["Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Chal", "Rog", "Kaal"],
    ["Udveg", "Shubh", "Amrit", "Chal", "Rog", "Kaal", "Labh", "Udveg"],
    ["Amrit", "Chal", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit"],
    ["Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Chal", "Rog"],
    ["Labh", "Udveg", "Shubh", "Amrit", "Chal", "Rog", "Kaal", "Labh"],
    ["Shubh", "Amrit", "Chal", "Rog", "Kaal", "Labh", "Udveg", "Shubh"],
]

def get_choghadiya(sunrise_dt, sunset_dt, weekday_index):
    """
    weekday_index: 0=Monday ... 6=Sunday
    Returns (list_day, list_night) each item = {"name":..., "time":"HH:MM - HH:MM"}
    """
    # daytime slots
    day_seconds = (sunset_dt - sunrise_dt).total_seconds()
    slot = day_seconds / 8.0
    day_list = []
    order = CHO_DAY_ORDER[weekday_index % 7]
    for i, name in enumerate(order):
        start = sunrise_dt + timedelta(seconds=i * slot)
        end = start + timedelta(seconds=slot)
        day_list.append({"name": name, "time": f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"})

    # nighttime: from sunset to next day's sunrise
    next_sunrise = sunrise_dt + timedelta(days=1)
    night_seconds = (next_sunrise - sunset_dt).total_seconds()
    nslot = night_seconds / 8.0
    night_list = []
    order_n = CHO_NIGHT_ORDER[weekday_index % 7]
    for i, name in enumerate(order_n):
        start = sunset_dt + timedelta(seconds=i * nslot)
        end = start + timedelta(seconds=nslot)
        night_list.append({"name": name, "time": f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"})

    return day_list, night_list

# ---------------------------
# Helper formatting for time ranges
# ---------------------------
def _time_range(start_dt, duration_seconds):
    end_dt = start_dt + timedelta(seconds=duration_seconds)
    return f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"

def sunrise_sunset(year, month, day, lat, lon, tz_offset_hours=5.5):
    """Return sunrise and sunset (local time) using Swiss Ephemeris."""
    jd = swe.julday(year, month, day, 0.0 -tz_offset_hours)  # midnight UT
    # Sunrise
    rise_jd= swe.rise_trans(
        jd,
        swe.SUN,
        geopos=(lon, lat, 0),
        rsmi=swe.CALC_RISE,
    )[1][0]
    # Sunset
    set_jd = swe.rise_trans(
        jd,
        swe.SUN,
        geopos=(lon, lat, 0),
        rsmi=swe.CALC_SET,
    )[1][0]

    # Convert JD UT to calendar datetime
    rise_ut = swe.revjul(rise_jd)  # (year, month, day, hour)
    set_ut = swe.revjul(set_jd)
    print(rise_ut,set_ut)
    rise_dt_utc = datetime(rise_ut[0], rise_ut[1], rise_ut[2]) + timedelta(hours=rise_ut[3])
    set_dt_utc = datetime(set_ut[0], set_ut[1], set_ut[2]) + timedelta(hours=set_ut[3])

    # Apply tz offset
    rise_local = rise_dt_utc + timedelta(hours=tz_offset_hours)
    set_local = set_dt_utc + timedelta(hours=tz_offset_hours)

    return rise_local, set_local

def moonrise_moonset(year, month, day, lat, lon, tz_offset_hours=5.5):
    """Return moonrise and moonset (local time) using Swiss Ephemeris."""
    jd = swe.julday(year, month, day, 0.0 - tz_offset_hours)  # midnight UT
    # Sunrise
    rise_jd= swe.rise_trans(
        jd,
        swe.MOON,
        geopos=(lon, lat, 0),
        rsmi=swe.CALC_RISE,
    )[1][0]
    # Sunset
    set_jd = swe.rise_trans(
        jd,
        swe.MOON,
        geopos=(lon, lat, 0),
        rsmi=swe.CALC_SET,
    )[1][0]

    # Convert JD UT to calendar datetime
    rise_ut = swe.revjul(rise_jd)  # (year, month, day, hour)
    set_ut = swe.revjul(set_jd)
    print(rise_ut,set_ut)
    rise_dt_utc = datetime(rise_ut[0], rise_ut[1], rise_ut[2]) + timedelta(hours=rise_ut[3])
    set_dt_utc = datetime(set_ut[0], set_ut[1], set_ut[2]) + timedelta(hours=set_ut[3])
    print(rise_dt_utc,set_dt_utc)
    # Apply tz offset
    rise_local = rise_dt_utc + timedelta(hours=tz_offset_hours)
    set_local = set_dt_utc + timedelta(hours=tz_offset_hours)

    return rise_local, set_local

KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti (Bhadra)"
]

FIXED_KARANAS = ["Shakuni", "Chatushpada", "Nagava", "Kimstughna"]

def _karana_name_from_index(k_index: int) -> str:
    """
    k_index = floor(elong/6), 0-based (0..59)
    """
    # Each tithi is 12°, so karna index goes 0..59 in a lunar month.
    # First 56 indices (0..55) are movable repeating every 7.
    # The last 4 (56..59) are the fixed ones.
    if k_index < 56:
        return KARANA_NAMES[k_index % 7 -1]
    else:
        return FIXED_KARANAS[k_index - 57]

def _compute_current_and_next_karana(jd_ut, tz_offset_hours=5.5):
    """
    Given jd_ut (Julian day, UT) returns:
      - k_index, k_name (current karana index+name)
      - next_k_index, next_k_name (next karana)
      - current_start_local (datetime)
      - next_start_local (datetime)  <-- this is the end of current karana
      - next_end_local (datetime)    <-- this is the end of next karana
    Uses ayanamsa-adjusted ecliptic longitudes so it's consistent with sidereal panchang.
    """
    # baseline longitudes (sidereal if you use ayanamsa elsewhere)
    pos_m, _ = swe.calc_ut(jd_ut, swe.MOON)
    pos_s, _ = swe.calc_ut(jd_ut, swe.SUN)
    ayan = swe.get_ayanamsa_ut(jd_ut)
    moon_lon = _normalize_angle(pos_m[0] - ayan)
    sun_lon = _normalize_angle(pos_s[0] - ayan)
    diff_now = (moon_lon - sun_lon) % 360.0

    # current karana index (0..59)
    k_index = int(diff_now // 6)

    # second point to estimate relative speed (0.5 day baseline is accurate enough)
    dt = 0.5
    pos_m2, _ = swe.calc_ut(jd_ut + dt, swe.MOON)
    pos_s2, _ = swe.calc_ut(jd_ut + dt, swe.SUN)
    ayan2 = swe.get_ayanamsa_ut(jd_ut + dt)
    moon_lon2 = _normalize_angle(pos_m2[0] - ayan2)
    sun_lon2 = _normalize_angle(pos_s2[0] - ayan2)
    diff2 = (moon_lon2 - sun_lon2) % 360.0

    # minimal-angle difference taking wrap into account
    raw_dd = diff2 - diff_now
    if raw_dd > 180:
        raw_dd -= 360.0
    if raw_dd < -180:
        raw_dd += 360.0

    rel_deg_per_day = raw_dd / dt
    # fallback to typical mean relative speed if estimate is degenerate
    if abs(rel_deg_per_day) < 1e-6:
        rel_deg_per_day = 12.19071064  # mean Moon−Sun deg/day

    # indexes for next and next-after
    next_k_index = (k_index + 1) % 60
    next2_k_index = (k_index + 2) % 60

    # target degrees where those karanas start (absolute multiples of 6°)
    target_deg_next = (next_k_index * 6.0) % 360.0
    target_deg_next2 = (next2_k_index * 6.0) % 360.0
    target_deg_start = (k_index * 6.0) % 360.0

    # compute days to each target from current diff (use positive modular distances)
    deg_to_next = (target_deg_next - diff_now) % 360.0
    deg_to_next2 = (target_deg_next2 - diff_now) % 360.0
    deg_since_start = (diff_now - target_deg_start) % 360.0

    days_to_next = deg_to_next / rel_deg_per_day
    days_to_next2 = deg_to_next2 / rel_deg_per_day
    days_since_start = deg_since_start / rel_deg_per_day

    jd_next = jd_ut + days_to_next
    jd_next2 = jd_ut + days_to_next2
    jd_start = jd_ut - days_since_start

    # convert JDs -> UTC datetimes (swe.revjul returns (y,m,d, hour_frac))
    r_start = swe.revjul(jd_start)
    dt_start_utc = datetime(r_start[0], r_start[1], r_start[2]) + timedelta(hours=r_start[3])
    r_next = swe.revjul(jd_next)
    dt_next_utc = datetime(r_next[0], r_next[1], r_next[2]) + timedelta(hours=r_next[3])
    r_next2 = swe.revjul(jd_next2)
    dt_next2_utc = datetime(r_next2[0], r_next2[1], r_next2[2]) + timedelta(hours=r_next2[3])

    # apply local tz offset
    current_start_local = dt_start_utc + timedelta(hours=tz_offset_hours)
    next_start_local = dt_next_utc + timedelta(hours=tz_offset_hours)   # end of current karana
    next_end_local = dt_next2_utc + timedelta(hours=tz_offset_hours)    # end of next karana

    return {
        "k_index": k_index,
        "k_name": _karana_name_from_index(k_index),
        "next_k_index": next_k_index,
        "next_k_name": _karana_name_from_index(next_k_index),
        "current_start_local": current_start_local,
        "next_start_local": next_start_local,
        "next_end_local": next_end_local
    }

# ---------------------------
# Main function (fixed)
# ---------------------------
def get_panchang(year, month, day, hour=12, minute=0, lat=28.6139, lon=77.2090, tz_offset=5.5):
    """
    Returns a dict with panchang details (tithi, paksha, nakshatra, yoga, karana, vara,
    sunrise/sunset, rahu/gulika/yamaganda, abhijit, choghadiya_day/night, sun_rashi, moon_rashi).
    tz_offset in hours (e.g., IST = +5.5)
    """
    # compute JD UT for given datetime (use the provided hour/minutes as local time -> convert to UT)
    # convert local hour to UT by subtracting tz_offset
    local_dt = datetime(year, month, day, hour, minute)
    ut_hour = hour - tz_offset
    jd_ut = swe.julday(year, month, day, ut_hour)

    # Sun & Moon longitudes (sidereal if you set sidereal above)
    pos_moon, _ = swe.calc_ut(jd_ut, swe.MOON)
    lon_moon = (_normalize_angle(pos_moon[0] - swe.get_ayanamsa_ut(jd_ut)))  # degrees

    pos_sun, _ = swe.calc_ut(jd_ut, swe.SUN)
    lon_sun = (_normalize_angle(pos_sun[0] - swe.get_ayanamsa_ut(jd_ut)))  # degrees

    # Tithi (0..29)
    diff = (lon_moon - lon_sun) % 360.0
    tithi_index = int(diff // 12)  # 0..29
    paksha = "Shukla" if tithi_index < 15 else "Krishna"
    tithi_name = f"{TITHI_SHORT[tithi_index % 15]}"

    # Nakshatra (0..26)
    nak_index = int(lon_moon // (360.0 / 27.0)) % 27
    nakshatra = NAKSHATRAS[nak_index]

    # Yoga (0..26)
    yoga_index = int(((lon_sun + lon_moon) % 360.0) // (360.0 / 27.0)) % 27
    yoga_name = YOGAS[yoga_index]

    # Vara (weekday)
    vara = WEEKDAYS[local_dt.weekday()]

    # Sunrise / Sunset (NOAA algorithm)
    # sunrise_dt, sunset_dt = sunrise_sunset_noaa(year, month, day, lat, lon, tz_offset_hours=tz_offset)
    
    #Sunrise/ Sunset ()
    sunrise_dt, sunset_dt = sunrise_sunset(year, month, day, lat, lon, tz_offset)
    # ensure sunrise < sunset; if not swap or adjust
    if sunrise_dt >= sunset_dt:
        # fallback: set approximate values
        sunrise_dt = local_dt.replace(hour=6, minute=0)
        sunset_dt = local_dt.replace(hour=18, minute=0)
        
    moonrise_dt, moonset_dt = moonrise_moonset(year, month, day, lat, lon, tz_offset)    
    

    # Day-duration in seconds
    day_seconds = (sunset_dt - sunrise_dt).total_seconds()
    # Rahu/Gulika/Yamaganda logic: use classical division into 8 parts
    wd_idx = local_dt.weekday()  # 0=Monday
    # the 'slot index' numbers in classical tables vary; using previously used arrays:
    rahu_periods = [[7,2],[1,6],[6,5],[4,4],[5,3],[3,2],[2,1]]
    gulika_periods = [[6,7],[5,6],[4,5],[3,4],[2,3],[1,2],[7,1]]
    yamaganda_periods = [[5,3],[4,2],[3,1],[2,7],[1,6],[7,5],[6,4]]

    # pick position index (a 1-based index in the 8 slots to start Rahu/Gulika/Yam)
    # if arrays provide [a,b], use b as the slot number to start (1..8)
    slot_seconds = day_seconds / 8.0
    
    rahu_slot_order_day = [2, 7, 5, 6, 4, 3, 8]  # Mon..Sun
    rahu_slot = rahu_slot_order_day[wd_idx] - 1  # 0-based
    rahu_start = sunrise_dt + timedelta(seconds=rahu_slot * slot_seconds)
    gulika_slot_order_day = [6, 5, 4, 3, 2, 1, 7]  # classical formula
    gulika_slot = gulika_slot_order_day[wd_idx] - 1
    gulika_start = sunrise_dt + timedelta(seconds=gulika_slot * slot_seconds)
    yamaganda_slot_order_day = [4, 3, 2, 1, 7, 6, 5]
    yam_slot = yamaganda_slot_order_day[wd_idx] - 1
    yam_start = sunrise_dt + timedelta(seconds=yam_slot * slot_seconds)
    rahu_kaal = _time_range(rahu_start, slot_seconds)
    gulika_kaal = _time_range(gulika_start, slot_seconds)
    yamaganda_kaal = _time_range(yam_start, slot_seconds)


    # Abhijit Muhurta: center of day ± 24 minutes
    mid = sunrise_dt + timedelta(seconds=(sunset_dt - sunrise_dt).total_seconds() / 2.0)
    abhijit = f"{(mid - timedelta(minutes=24)).strftime('%H:%M')} - {(mid + timedelta(minutes=24)).strftime('%H:%M')}"

    # Choghadiya
    cho_day, cho_night = get_choghadiya(sunrise_dt, sunset_dt, wd_idx)

    # Sun/Moon rashi names (use SIGNS list: Aries=0,...)
    sun_rashi_idx = int(lon_sun // 30.0) % 12
    moon_rashi_idx = int(lon_moon // 30.0) % 12
    sun_rashi = SIGNS[sun_rashi_idx]
    moon_rashi = SIGNS[moon_rashi_idx]
    kar = _compute_current_and_next_karana(jd_ut, tz_offset_hours=tz_offset)
    result = {
        "tithi": tithi_name,
        "paksha": paksha,
        "nakshatra": nakshatra,
        "yoga": yoga_name,
        "vara": vara,
        "sunrise": sunrise_dt.strftime("%H:%M"),
        "sunset": sunset_dt.strftime("%H:%M"),
        "rahu_kaal": rahu_kaal,
        "gulika_kaal": gulika_kaal,
        "yamaganda": yamaganda_kaal,
        "abhijit_muhurta": abhijit,
        "choghadiya_day": cho_day,
        "choghadiya_night": cho_night,
        "sun_rashi": sun_rashi,
        "moon_rashi": moon_rashi,
        "moonrise": moonrise_dt.strftime("%H:%M"),
        "moonset": moonset_dt.strftime("%H:%M"),
        "karana_1": kar["k_name"],
        "karana_2": kar["next_k_name"],
        "karana_1_range": f"{kar['current_start_local'].strftime('%H:%M')} - {kar['next_start_local'].strftime('%H:%M')}",
        "karana_2_range": f"{kar['next_start_local'].strftime('%H:%M')} - {kar['next_end_local'].strftime('%H:%M')}",
    }

    return result
