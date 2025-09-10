from datetime import datetime

ZODIAC_SIGNS = [
    "Aries ♈", "Taurus ♉", "Gemini ♊", "Cancer ♋",
    "Leo ♌", "Virgo ♍", "Libra ♎", "Scorpio ♏",
    "Sagittarius ♐", "Capricorn ♑", "Aquarius ♒", "Pisces ♓"
]

def get_sun_sign(date_str):
    """Return zodiac sign based on date only (approx western system)."""
    date = datetime.strptime(date_str, "%Y-%m-%d")
    m, d = date.month, date.day

    if (m == 3 and d >= 21) or (m == 4 and d <= 19): return "Aries ♈"
    if (m == 4 and d >= 20) or (m == 5 and d <= 20): return "Taurus ♉"
    if (m == 5 and d >= 21) or (m == 6 and d <= 20): return "Gemini ♊"
    if (m == 6 and d >= 21) or (m == 7 and d <= 22): return "Cancer ♋"
    if (m == 7 and d >= 23) or (m == 8 and d <= 22): return "Leo ♌"
    if (m == 8 and d >= 23) or (m == 9 and d <= 22): return "Virgo ♍"
    if (m == 9 and d >= 23) or (m == 10 and d <= 22): return "Libra ♎"
    if (m == 10 and d >= 23) or (m == 11 and d <= 21): return "Scorpio ♏"
    if (m == 11 and d >= 22) or (m == 12 and d <= 21): return "Sagittarius ♐"
    if (m == 12 and d >= 22) or (m == 1 and d <= 19): return "Capricorn ♑"
    if (m == 1 and d >= 20) or (m == 2 and d <= 18): return "Aquarius ♒"
    return "Pisces ♓"

def kundali_report(name, date, time, place):
    """Return a simplified kundali chart."""
    sun_sign = get_sun_sign(date)
    
    chart = {
        "Name": name,
        "Date": date,
        "Time": time,
        "Place": place,
        "Sun Sign": sun_sign,
        "Planets": {
            "Sun": sun_sign,
            "Moon": "Gemini ♊", 
            "Mars": "Leo ♌",
            "Mercury": "Virgo ♍",
            "Jupiter": "Sagittarius ♐",
            "Venus": "Libra ♎",
            "Saturn": "Capricorn ♑",
        }
    }
    return chart

# Kundali API
def kundali_report(person):
    # Example – replace with user input
    # Get Horoscope from Vedastro
    # horoscope = Api.GetHoroscope(person)
    profile= {"name": person.user,
        "date": person.birth_date,
        "time": person.birth_time,
        "place": person.birth_place}
    planets =  [
            {"name": p.Name, "sign": p.Sign, "degrees": round(p.Degrees,2)}
            for p in horoscope.Planets
        ]
    fig = draw_north_indian_chart(planets)
    buf = io.BytesIO()
    canvas = FigureCanvas(fig)
    canvas.print_png(buf)
    chart_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    data = {
        "profile":profile,
        "planets":planets,
        "chart": f"data:image/png;base64,{chart_base64}",
    }

    return JsonResponse(data)

def draw_north_indian_chart(planets):
    fig, ax = plt.subplots(figsize=(6,6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Draw diamond chart
    ax.plot([5, 10, 5, 0, 5], [10, 5, 0, 5, 10], 'k-')
    ax.plot([0, 10], [5, 5], 'k--', alpha=0.5)
    ax.plot([5, 5], [0, 10], 'k--', alpha=0.5)
    # Planet positions (just sample placement, we can map house-wise)
    positions = {
        1: (5, 9),2: (8, 8),3: (9, 5),
        4: (8, 2),5: (5, 1),6: (2, 2),
        7: (1, 5),8: (2, 8),9: (5, 5)
    }

    for i, planet in enumerate(planets, start=1):
        house = (i % 9) + 1
        x, y = positions[house]
        ax.text(x, y, f"{planet['name']}\n{planet['degrees']}°", 
                ha="center", va="center", fontsize=8)

    plt.tight_layout()
    return fig
