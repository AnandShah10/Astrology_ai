import swisseph as swe
from datetime import datetime, timedelta
import math

swe.set_sid_mode(swe.SIDM_LAHIRI)

TITHI_NAMES = [
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

KARANAS = [
    "Bava","Balava","Kaulava","Taitila","Garaja","Vanija","Vishti",
    "Shakuni","Chatushpada","Naga","Kimstughna"
]

WEEKDAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]


CHO_NAMES = [
    "Amrit", "Shubh", "Labh", "Chal",
    "Udveg", "Rog", "Kaal"
]

# Daytime order (Sunrise → Sunset)
CHO_DAY = [
    ["Amrit","Shubh","Rog","Udveg","Chal","Labh","Amrit","Kaal"],
    ["Amrit","Rog","Shubh","Udveg","Chal","Labh","Amrit","Kaal"],
    ["Udveg","Amrit","Shubh","Rog","Chal","Labh","Amrit","Kaal"],
    ["Shubh","Amrit","Rog","Udveg","Chal","Labh","Amrit","Kaal"],
    ["Rog","Amrit","Shubh","Udveg","Chal","Labh","Amrit","Kaal"],
    ["Udveg","Amrit","Shubh","Rog","Chal","Labh","Amrit","Kaal"],
    ["Amrit","Shubh","Rog","Udveg","Chal","Labh","Amrit","Kaal"],
]

# Night order (Sunset → Sunrise)
CHO_NIGHT = [
    ["Shubh","Amrit","Chal","Rog","Udveg","Labh","Kaal","Amrit"],
    ["Amrit","Shubh","Chal","Rog","Udveg","Labh","Kaal","Amrit"],
    ["Rog","Amrit","Chal","Shubh","Udveg","Labh","Kaal","Amrit"],
    ["Amrit","Shubh","Chal","Rog","Udveg","Labh","Kaal","Amrit"],
    ["Chal","Amrit","Rog","Shubh","Udveg","Labh","Kaal","Amrit"],
    ["Shubh","Amrit","Chal","Rog","Udveg","Labh","Kaal","Amrit"],
    ["Rog","Amrit","Chal","Shubh","Udveg","Labh","Kaal","Amrit"],
]

def get_choghadiya(sunrise, sunset, weekday):
    # Daytime
    day_dur = (sunset - sunrise).seconds / 8
    cho_day = []
    for i, name in enumerate(CHO_DAY[weekday]):
        start = sunrise + timedelta(seconds=i*day_dur)
        end = start + timedelta(seconds=day_dur)
        cho_day.append({
            "name": name,
            "time": f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
        })

    # Nighttime
    next_sunrise = sunrise + timedelta(days=1)
    night_dur = (next_sunrise - sunset).seconds / 8
    cho_night = []
    for i, name in enumerate(CHO_NIGHT[weekday]):
        start = sunset + timedelta(seconds=i*night_dur)
        end = start + timedelta(seconds=night_dur)
        cho_night.append({
            "name": name,
            "time": f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
        })

    return cho_day, cho_night


def _get_sunrise_sunset(year, month, day, lat, lon, tz_offset=5.5):
    jd = swe.julday(year, month, day, 0)
    flag = swe.BIT_DISC_CENTER + swe.BIT_NO_REFRACTION
    sunrise = swe.rise_trans(jd, swe.SUN, lon, lat, rsmi=swe.CALC_RISE, special=flag)[1][0]
    sunset = swe.rise_trans(jd, swe.SUN, lon, lat, rsmi=swe.CALC_SET, special=flag)[1][0]

    def jd_to_time(jd_val):
        dt = swe.revjul(jd_val)
        h, m = math.modf(dt[3])
        return datetime(dt[0], dt[1], dt[2], int(dt[3]), int(m*60)) + timedelta(hours=tz_offset)

    return jd_to_time(sunrise), jd_to_time(sunset)

def _time_range(start, duration):
    h = start.hour + start.minute/60
    return f"{start.strftime('%H:%M')} - {(start + timedelta(minutes=duration)).strftime('%H:%M')}"

def get_panchang(year, month, day, hour=12, minute=0, lat=28.6139, lon=77.2090, tz_offset=5.5):
    jd = swe.julday(year, month, day, hour + minute/60.0)

    lon_moon = (swe.calc_ut(jd, swe.MOON)[0] - swe.get_ayanamsa_ut(jd)) % 360
    lon_sun = (swe.calc_ut(jd, swe.SUN)[0] - swe.get_ayanamsa_ut(jd)) % 360

    # Tithi
    diff = (lon_moon - lon_sun) % 360
    tithi = int(diff / 12)
    tithi_name = TITHI_NAMES[tithi if tithi < len(TITHI_NAMES) else -1]

    # Nakshatra
    nak = int(lon_moon / (360/27))
    nakshatra = NAKSHATRAS[nak]

    # Yoga
    yoga_sum = (lon_sun + lon_moon) % 360
    yoga = int(yoga_sum / (360/27))
    yoga_name = YOGAS[yoga]

    # Karana
    karana = int(diff / 6) % len(KARANAS)
    karana_name = KARANAS[karana]

    # Vara
    weekday = WEEKDAYS[datetime(year, month, day).weekday()]

    # Sunrise / Sunset
    sunrise, sunset = _get_sunrise_sunset(year, month, day, lat, lon, tz_offset)
    day_duration = (sunset - sunrise).seconds / 8  # divide into 8 equal parts

    # Rahu, Gulika, Yamaganda (using weekday rules)
    rahu_periods = [ [7,2], [1,6], [6,5], [4,4], [5,3], [3,2], [2,1] ]  # weekday-based
    gulika_periods = [ [6,7], [5,6], [4,5], [3,4], [2,3], [1,2], [7,1] ]
    yamaganda_periods = [ [5,3], [4,2], [3,1], [2,7], [1,6], [7,5], [6,4] ]

    wd = datetime(year, month, day).weekday()  # 0=Monday
    rahu_start = sunrise + timedelta(seconds=(rahu_periods[wd][1]-1)*day_duration)
    gulika_start = sunrise + timedelta(seconds=(gulika_periods[wd][1]-1)*day_duration)
    yam_start = sunrise + timedelta(seconds=(yamaganda_periods[wd][1]-1)*day_duration)

    rahu_kaal = _time_range(rahu_start, day_duration/60)
    gulika_kaal = _time_range(gulika_start, day_duration/60)
    yamaganda = _time_range(yam_start, day_duration/60)

    # Abhijit Muhurta (midday +- 24 mins approx)
    midday = sunrise + (sunset - sunrise)/2
    abhijit = f"{(midday - timedelta(minutes=24)).strftime('%H:%M')} - {(midday + timedelta(minutes=24)).strftime('%H:%M')}"
    
    cho_day, cho_night = get_choghadiya(sunrise, sunset, wd)

    return {
        "tithi": tithi_name,
        "nakshatra": nakshatra,
        "yoga": yoga_name,
        "karana": karana_name,
        "weekday": weekday,
        "sunrise": sunrise.strftime("%H:%M"),
        "sunset": sunset.strftime("%H:%M"),
        "rahu_kaal": rahu_kaal,
        "gulika_kaal": gulika_kaal,
        "yamaganda": yamaganda,
        "abhijit_muhurta": abhijit,
        "choghadiya_day": cho_day,
        "choghadiya_night": cho_night,
    }
