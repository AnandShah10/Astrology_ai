import swisseph as swe
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io, base64

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
PLANETS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]

def get_kundali_chart(year, month, day, hour, minute, lat, lon, tz_offset):
    # Convert local time to UTC
    dt = datetime(year, month, day, hour, minute)
    dt_utc = dt - timedelta(hours=tz_offset)
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60)

    # Houses (Placidus)
    asc, cusps = swe.houses(jd, lat, lon, b'A')
    asc_deg = asc[0]

    # Determine Ascendant sign
    asc_sign_index = int(asc_deg // 30)

    # Planet positions
    planet_positions = {}
    for pl in PLANETS:
        if pl == "Rahu":
            deg = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
        elif pl == "Ketu":
            deg = (swe.calc_ut(jd, swe.MEAN_NODE)[0][0] + 180) % 360
        else:
            deg = swe.calc_ut(jd, getattr(swe, pl.upper()))[0][0]
        sign_index = int(deg // 30)
        planet_positions[pl] = {"deg": deg, "sign": SIGNS[sign_index]}

    # Assign planets to houses based on Ascendant
    house_planets = {i+1: [] for i in range(12)}
    for pl, info in planet_positions.items():
        deg = info["deg"]
        house_num = int(((deg - asc_deg + 360) % 360) // 30) + 1
        if house_num > 12:
            house_num -= 12
        house_planets[house_num].append(pl)

    # Correct zodiac signs in houses
    house_signs = {}
    for i in range(12):
        house_index = (asc_sign_index + i) % 12
        house_signs[i+1] = SIGNS[house_index]

    # Coordinates for North-Indian style diamond chart
    diamond_houses = {
        1: (2, 0), 2: (0, 2), 3: (2, 4), 4: (4, 2),
        5: (0, 4), 6: (4, 0), 7: (2, -2), 8: (-2, 2),
        9: (2, 6), 10: (6, 2), 11: (-2, 4), 12: (2, 8)
    }

    fig, ax = plt.subplots(figsize=(6,6))
    ax.axis("off")

    # Draw house diamonds
    for house, (x, y) in diamond_houses.items():
        diamond = plt.Polygon([[x-1,y-1],[x+1,y-1],[x+1,y+1],[x-1,y+1]], closed=True, fill=None, edgecolor='black', lw=2)
        ax.add_patch(diamond)
        ax.text(x, y+0.4, str(house), ha='center', va='center', fontsize=12, fontweight='bold', color='orange')
        if house_planets.get(house):
            text = "\n".join([f"{pl}-{planet_positions[pl]['deg']:.2f}°" for pl in house_planets[house]])
            ax.text(x, y-0.1, text, ha='center', va='center', fontsize=9, color='blue')


    ax.set_xlim(-3, 8)
    ax.set_ylim(-3, 8)
    plt.tight_layout()

    # Save chart to base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    kundali_chart = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return {
        "ascendant": asc_deg,
        "houses": cusps,
        "planet_positions": planet_positions,
        "house_planets": house_planets,
        "house_signs": house_signs,
        "kundali_chart": kundali_chart
    }
