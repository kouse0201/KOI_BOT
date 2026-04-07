import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta, timezone
import os
import random  # ★追加

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ------------------------
# JST
# ------------------------
JST = timezone(timedelta(hours=9))

# ------------------------
# データ
# ------------------------
def load_data():
    try:
        with open("data.json","r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open("data.json","w",encoding="utf-8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)

data = load_data()

def init_user(user):
    uid=str(user.id)
    if uid not in data:
        data[uid]={}

    data[uid]["name"] = user.display_name

    defaults={
        "name":user.display_name,
        "is_working":False,
        "start_time":None,
        "total_time":0,
        "history":[],
        "pay":0,
        "sales":0,
        "items":{}
    }

    for k,v in defaults.items():
        if k not in data[uid]:
            data[uid][k]=v

def yen(n):
    return f"{int(n):,}円"

# ------------------------
# ★京都ねぎらい
# ------------------------
def get_kyoto_message(seconds):
    minutes = seconds // 60

    if minutes < 60:
        msgs = [
            "あらあら、そないな短さでお仕事言わはるん？笑わせんといておくれやす。",
            "ほんまに働いたつもりどす？うちは認められへんわぁ。",
            "そないな時間で退勤やなんて、えらい気楽なお仕事どすなぁ。",
            "それ、出勤言うんやったら世の中ゆるすぎますえ？",
            "ちょっと席温めただけやのに、よう退勤押せましたなぁ。",
            "あんさんの中ではこれで働いたことになるんどす？不思議やわぁ。",
            "そら記録にも残したらあきませんえ、恥ずかしいさかい。",
            "ほんのご挨拶程度の出勤どしたなぁ、かわいらしいこと。",
            "それで給料出る思うてはるんやったら、だいぶおめでたいどすなぁ。",
            "まぁ…次はもうちょっと“お仕事”してから押しとくれやす。"
        ]

    elif 60 <= minutes <= 70:
        msgs = [
            "義務だけはちゃんと果たしはったんやねぇ、それだけはえらいどすなぁ。",
            "最低限だけやって帰らはるん、ほんま要領よろしおすなぁ。",
            "きっちり義務時間だけ、抜かりあらしまへんなぁ。",
            "それ以上は働かへんいう強い意志、見習いたいくらいやわぁ。",
            "まぁ決まりだけ守っとけば文句言われへんもんなぁ、賢いこと。",
            "あえてそれ以上はやらへんの、なかなかしたたかどすなぁ。",
            "義務ピッタリで帰るん、逆に感心してしまいますえ。",
            "その“ギリギリ精神”、よう貫いてはるわぁ。",
            "必要以上はせぇへん、ええスタイル持ってはりますなぁ。",
            "ほんま、損せぇへん働き方、ようご存じどすなぁ。"
        ]

    elif 70 < minutes < 110:
        msgs = [
            "ちょっとだけ頑張らはったんやねぇ、その中途半端さがまたよろしおすなぁ。",
            "義務よりちょい上、なんとも言えへん働きぶりどすなぁ。",
            "あとちょっと頑張ればええのに、そこ止まりなんがあんさんらしいわぁ。",
            "中途半端にようやらはりましたなぁ、ほんま絶妙どす。",
            "その微妙な頑張り、評価に困りますわぁ。",
            "頑張ったんかサボったんか、よう分からんええラインどすなぁ。",
            "なんとも言えへん時間やけど…まぁお疲れさんどす。",
            "そこまで来たらもうちょい行けたんと違います？ふふ。",
            "ええとこで止めはりましたなぁ、計算してはるんやろか。",
            "まぁ…“ちょっと頑張った感”は出てますえ。"
        ]

    elif 110 <= minutes < 120:
        msgs = [
            "ほぉ〜、そこそこやらはりましたなぁ。珍しいこともあるもんどす。",
            "思ったより働かはったやないの、びっくりしてしまいますえ。",
            "まぁまぁやってはりますやん、見直しましたわぁ。",
            "今日はちょっとだけ本気出さはったんどす？ええやないの。",
            "そこまでやる気あったん、初めて見ましたえ。",
            "ええ感じに働かはりましたなぁ、たまにはやるんやねぇ。",
            "ほんま、今日はちょっと違いますやん。",
            "そこそこ頑張ったんと違います？認めときますわぁ。",
            "あら、意外とやるときはやるんどすなぁ。",
            "まぁ…今日は許したげてもええどすえ。"
        ]

    elif 120 <= minutes < 180:
        msgs = [
            "よう頑張らはりましたなぁ、お疲れさまどす。",
            "しっかり働いてはりますやん、立派どすえ。",
            "今日はほんまにええ働きぶりどした。",
            "安心して任せられるお人どすなぁ。",
            "ようここまでやらはりました、感心しますえ。",
            "ええ仕事してはりますなぁ、お疲れさまどす。",
            "しっかり役目果たしてはりますやん。",
            "見てて気持ちええ働き方どしたえ。",
            "ほんま、頼りになるお人どすなぁ。",
            "ええ一日どしたなぁ、お疲れさま。"
        ]

    else:
        msgs = [
            "ほんまによう頑張らはりましたなぁ、心から尊敬しますえ。",
            "ここまで働かはるなんて、なかなかできることやあらしまへん。",
            "あんさんには頭上がりまへんわぁ、本当にお疲れさまどす。",
            "これほど尽くしてくれはるなんて、ありがたいことどす。",
            "見事な働きぶりどした、誇ってよろしおす。",
            "ほんま立派なお人やわぁ、感謝しかあらしまへん。",
            "ここまでやってくれる人、なかなかおりまへんえ。",
            "素晴らしい働きに、心打たれましたえ。",
            "あんさんがおってくれて助かってます、ほんまに。",
            "今日は最高の働きどした、ゆっくり休んどくれやす。"
        ]

    return random.choice(msgs)

# ------------------------
# UTC→JST
# ------------------------
def to_jst(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(JST)

# ------------------------
# ステータス更新
# ------------------------
def get_working_count():
    return sum(1 for u in data.values() if u.get("is_working"))

@tasks.loop(seconds=10)
async def update_status():
    count = get_working_count()
    if count > 0:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(f"開店中({count}人)")
        )
    else:
        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Game("閉店中")
        )

# ------------------------
# 勤務UI
# ------------------------
class WorkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def embed(self):
        working=[]
        for uid,u in data.items():
            if u.get("is_working"):
                name = u.get("name") or "不明"
                st = u.get("start_time")
                if st:
                    try:
                        t = to_jst(datetime.fromisoformat(st)).strftime("%H:%M")
                        working.append(f"{name}({t}~)")
                    except:
                        working.append(f"{name}(??:??~)")
                else:
                    working.append(f"{name}(??:??~)")

        return discord.Embed(
            title="📋勤務パネル",
            description="\n".join(working) if working else "出勤者なし"
        )

    @discord.ui.button(label="出勤", style=discord.ButtonStyle.success)
    async def start(self, interaction, button):
        init_user(interaction.user)
        uid=str(interaction.user.id)
        data[uid]["is_working"]=True
        data[uid]["start_time"]=datetime.now(timezone.utc).astimezone(JST).isoformat()
        save_data(data)
        await interaction.response.edit_message(embed=self.embed(),view=self)

    @discord.ui.button(label="退勤",style=discord.ButtonStyle.danger)
    async def end(self,interaction,button):
        init_user(interaction.user)
        uid=str(interaction.user.id)

        start = to_jst(datetime.fromisoformat(data[uid]["start_time"]))
        now = datetime.now(timezone.utc).astimezone(JST)

        diff=(now-start).total_seconds()

        # ★追加
        message = get_kyoto_message(diff)

        data[uid]["total_time"]+=diff
        data[uid]["history"].append({
            "start":data[uid]["start_time"],
            "end":now.isoformat()
        })

        data[uid]["is_working"]=False
        data[uid]["start_time"]=None
        save_data(data)

        await interaction.response.edit_message(embed=self.embed(),view=self)

        # ★追加
        await interaction.followup.send(message, ephemeral=True)

# ------------------------
# 起動
# ------------------------
@bot.event
async def on_ready():
    global work_view
    print("ログイン完了")

    work_view = WorkView()
    bot.add_view(work_view)
    await tree.sync()
    update_status.start()

    print("起動OK")

bot.run(os.getenv("TOKEN"))
