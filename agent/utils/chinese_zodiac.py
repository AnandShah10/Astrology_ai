import sxtwl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io, base64

# Heavenly Stems & Earthly Branches
STEMS = ["Jia 甲", "Yi 乙", "Bing 丙", "Ding 丁", "Wu 戊", "Ji 己", "Geng 庚", "Xin 辛", "Ren 壬", "Gui 癸"]
BRANCHES = ["Zi 子 (Rat)", "Chou 丑 (Ox)", "Yin 寅 (Tiger)", "Mao 卯 (Rabbit)",
            "Chen 辰 (Dragon)", "Si 巳 (Snake)", "Wu 午 (Horse)", "Wei 未 (Goat)",
            "Shen 申 (Monkey)", "You 酉 (Rooster)", "Xu 戌 (Dog)", "Hai 亥 (Pig)"]

# Elements (Wood, Fire, Earth, Metal, Water)
STEM_TO_ELEMENT = {0:"Wood",1:"Wood",2:"Fire",3:"Fire",4:"Earth",5:"Earth",6:"Metal",7:"Metal",8:"Water",9:"Water"}
STEM_POLARITY = {0:"Yang",1:"Yin",2:"Yang",3:"Yin",4:"Yang",5:"Yin",6:"Yang",7:"Yin",8:"Yang",9:"Yin"}

# Element colors (for chart & legend)
ELEMENT_COLORS = {
    "Wood": "#27ae60",
    "Fire": "#e74c3c",
    "Earth": "#d35400",
    "Metal": "#95a5a6",
    "Water": "#2980b9"
}

# 5 Elements Generating / Controlling relationships
GENERATES = {"Wood":"Fire","Fire":"Earth","Earth":"Metal","Metal":"Water","Water":"Wood"}
CONTROLS = {"Wood":"Earth","Earth":"Water","Water":"Fire","Fire":"Metal","Metal":"Wood"}

# Day Master personalities
DAY_MASTER_INFO = {
    "Jia 甲": {"element":"Wood","traits":"Tall tree, upright, dependable, stubborn but principled.","favorable":"Water, Fire","unfavorable":"Metal"},
    "Yi 乙": {"element":"Wood","traits":"Flexible grass, elegant, gentle, diplomatic, sometimes indecisive.","favorable":"Water, Fire","unfavorable":"Metal"},
    "Bing 丙": {"element":"Fire","traits":"Sun, warm, generous, inspirational, but prideful.","favorable":"Wood, Earth","unfavorable":"Water"},
    "Ding 丁": {"element":"Fire","traits":"Candle flame, soft warmth, insightful, caring, but moody.","favorable":"Wood, Earth","unfavorable":"Water"},
    "Wu 戊": {"element":"Earth","traits":"Mountain, stable, reliable, strong leader, but inflexible.","favorable":"Fire, Metal","unfavorable":"Wood"},
    "Ji 己": {"element":"Earth","traits":"Field soil, nurturing, adaptable, practical, sometimes overthinking.","favorable":"Fire, Metal","unfavorable":"Wood"},
    "Geng 庚": {"element":"Metal","traits":"Axe/iron, strong, disciplined, justice-driven, but rigid.","favorable":"Earth, Water","unfavorable":"Fire"},
    "Xin 辛": {"element":"Metal","traits":"Precious metal, refined, graceful, intelligent, but vain.","favorable":"Earth, Water","unfavorable":"Fire"},
    "Ren 壬": {"element":"Water","traits":"Ocean, wise, resourceful, ambitious, sometimes overwhelming.","favorable":"Metal, Wood","unfavorable":"Earth"},
    "Gui 癸": {"element":"Water","traits":"Rain, gentle, nurturing, intuitive, mysterious, sometimes anxious.","favorable":"Metal, Wood","unfavorable":"Earth"},
}

# Mapping of Day Master → Other Stem = 10 Gods
def get_ten_god(day_stem, other_stem):
    dm_elem = STEM_TO_ELEMENT[day_stem]
    dm_polarity = STEM_POLARITY[day_stem]

    other_elem = STEM_TO_ELEMENT[other_stem]
    other_polarity = STEM_POLARITY[other_stem]

    if other_elem == dm_elem:
        return "比肩 (Friend)" if other_polarity == dm_polarity else "劫财 (Rob Wealth)"
    elif GENERATES[dm_elem] == other_elem:
        return "食神 (Eating God)" if other_polarity == dm_polarity else "伤官 (Hurting Officer)"
    elif GENERATES[other_elem] == dm_elem:
        return "正印 (Direct Resource)" if other_polarity == dm_polarity else "偏印 (Indirect Resource)"
    elif CONTROLS[dm_elem] == other_elem:
        return "正财 (Direct Wealth)" if other_polarity != dm_polarity else "偏财 (Indirect Wealth)"
    elif CONTROLS[other_elem] == dm_elem:
        return "正官 (Official)" if other_polarity != dm_polarity else "七杀 (Seven Killings)"
    return "Unknown"

def pillar(stem_index, branch_index):
    return f"{STEMS[stem_index]} - {BRANCHES[branch_index]}"

def generate_bazi(year, month, day, hour):
    day_obj = sxtwl.fromSolar(year, month, day)
    year_gz = day_obj.getYearGZ()
    month_gz = day_obj.getMonthGZ()
    day_gz = day_obj.getDayGZ()

    hour_branch_index = ((hour + 1) // 2) % 12
    day_stem_index = day_gz.tg
    hour_stem_index = (day_stem_index * 2 + hour_branch_index) % 10

    pillars = {
        "Year Pillar": (year_gz.tg, year_gz.dz),
        "Month Pillar": (month_gz.tg, month_gz.dz),
        "Day Pillar": (day_gz.tg, day_gz.dz),
        "Hour Pillar": (hour_stem_index, hour_branch_index)
    }

    result, element_count = {}, {"Wood":0,"Fire":0,"Earth":0,"Metal":0,"Water":0}

    for name, (stem, branch) in pillars.items():
        element = STEM_TO_ELEMENT[stem]
        pillar_name = pillar(stem, branch)
        ten_god = get_ten_god(day_stem_index, stem)
        result[name] = {"text": pillar_name, "element": element, "ten_god": ten_god}
        element_count[element] += 1

    # Day Master info
    day_master = STEMS[day_gz.tg]
    master_info = DAY_MASTER_INFO[day_master]
    
    # Element balance chart
    fig, ax = plt.subplots()
    elements = list(element_count.keys())
    values = list(element_count.values())
    colors = [ELEMENT_COLORS[e] for e in elements]
    bars=ax.bar(elements, values, color=colors)
    total = sum(values)
    for bar, value in zip(bars, values):
        percent = round((value / total) * 100, 1) if total > 0 else 0
        if value >= total * 0.1:  # if bar is tall enough
            ax.text(
                bar.get_x() + bar.get_width() / 2, 
                value / 2,  # inside the bar
                f"{percent}%", 
                ha="center", va="center", fontsize=10, fontweight="bold", color="white"
            )
        else:
            ax.text(
                bar.get_x() + bar.get_width() / 2, 
                value + 0.05,  # slightly above
                f"{percent}%", 
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="black"
            )
    ax.set_title("Element Balance in Your BaZi Chart")
    ax.set_ylabel("Count")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close()
    # Calculate percentages
    total = sum(element_count.values())
    element_percentages = {}
    for element, count in element_count.items():
        percent = round((count / total) * 100, 1) if total > 0 else 0
        element_percentages[element] = {
            "count": count,
            "percent": percent,
            "color": ELEMENT_COLORS[element]
        }
    return result, chart_base64, day_master, master_info,element_percentages

