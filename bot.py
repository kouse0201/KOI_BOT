import discord
from discord.ext import commands
import json
from datetime import datetime
import os

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

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
# 🔥 ステータス更新（追加）
# ------------------------
async def update_status():
    working = [u for u in data.values() if u.get("is_working")]
    count = len(working)

    if count > 0:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name=f"開店中({count}人)")
        )
    else:
        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Game(name="閉店中")
        )

# ------------------------
# メニュー（そのまま）
# ------------------------
MENU = {
    "全日メニュー":{
        "特製KOI定食":{"price":5900,"cost":2375},
        "特上うな重":{"price":5900,"cost":2750},
        "温玉うどん":{"price":6000,"cost":2175},
        "肉厚温玉牛丼":{"price":7000,"cost":2625},
        "KOI特選お寿司盛り合わせ":{"price":22500,"cost":8750},
        "KOI特製温泉プリン":{"price":5100,"cost":2500},
        "KOI印温泉饅頭":{"price":5100,"cost":2250},
        "おにぎりセット":{"price":3200,"cost":1500},
        "お子様ランチ":{"price":4000,"cost":1750},
        "KOIばななみるく":{"price":5100,"cost":2500},
        "KOI珈琲牛乳":{"price":5100,"cost":2000},
        "しゅわしゅわラムネ":{"price":3500,"cost":1500},
        "贅沢なKOIオロポ":{"price":5100,"cost":2125},
        "こいくん醸造の日本酒":{"price":6000,"cost":2125},
        "梅酒":{"price":6000,"cost":2125},
        "電動マッサージ機":{"price":60000,"cost":25000},
        "ろシあん闇鍋":{"price":6500,"cost":1750},
        "こいくん人形":{"price":6000,"cost":2250},
        "湯の花の瓶":{"price":6500,"cost":2200},
    },
    "日中限定メニュー":{
        "肉厚とんかつ定食":{"price":6500,"cost":2500},
        "こいくんケーキ":{"price":5100,"cost":1875},
        "山菜の天ぷら蕎麦":{"price":6500,"cost":2500},
        "こいくんの温玉ソフト":{"price":5100,"cost":2250},
        "イカ飯弁当":{"price":8600,"cost":3250},
    },
    "夜間限定メニュー":{
        "ほかほか湯豆腐スープ":{"price":6000,"cost":2375},
        "KOIの船盛り":{"price":8500,"cost":2500},
        "お子様プレミア定食":{"price":6500,"cost":2500},
        "贅沢かに御膳":{"price":8900,"cost":2750},
        "金目鯛の煮つけ":{"price":10000,"cost":3250},
    },
    "チル限定メニュー":{
        "KOI印のお守り・青":{"price":8000,"cost":2875},
        "KOI印のお守り・赤":{"price":8000,"cost":2500},
        "ちるいん":{"price":9500,"cost":3625},
    },
    "季節限定メニュー":{
        "春の桜づくしセット":{"price":16000,"cost":6625},
        "桜香る春御膳":{"price":6000,"cost":1500},
        "湯けむり桜ソーダ":{"price":7000,"cost":3125},
        "桜にごり酒":{"price":6000,"cost":2000},
    },
    "移動販売メニュー":{
        "いっぱい飲みにKOIよセット":{"price":13000,"cost":5250},
        "温泉麦酒KOI心":{"price":6000,"cost":2250},
        "焼き鳥盛り合わせ":{"price":9000,"cost":3000},
        "がつ盛り焼きそば":{"price":6500,"cost":1750},
        "すき焼き御膳":{"price":30000,"cost":12000},
        "濃い黒たまご":{"price":6500,"cost":2000},
    },
    "イベントメニュー":{
        "田中さんのりんご飴":{"price":7100,"cost":2375},
        "KOIいちごみるく":{"price":5900,"cost":2625},
        "温泉のお香":{"price":6300,"cost":2000},
        "よくばりプリンパフェ":{"price":10000,"cost":2500},
    }
}

CATEGORY_LIST=list(MENU.items())

def split_menu(page):
    return dict(CATEGORY_LIST[:4] if page==0 else CATEGORY_LIST[4:])

# ------------------------
# 勤務UI（ここに追記）
# ------------------------
class WorkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def embed(self):
        working=[u.get("name") for u in data.values() if u.get("is_working")]
        return discord.Embed(
            title="📋勤務パネル",
            description="\n".join(working) if working else "出勤者なし"
        )

    @discord.ui.button(label="出勤",style=discord.ButtonStyle.success,custom_id="start")
    async def start(self,interaction,button):
        init_user(interaction.user)
        uid=str(interaction.user.id)
        data[uid]["is_working"]=True
        data[uid]["start_time"]=datetime.now().isoformat()
        save_data(data)

        await update_status()  # 🔥追加

        await interaction.response.edit_message(embed=self.embed(),view=self)

    @discord.ui.button(label="退勤",style=discord.ButtonStyle.danger,custom_id="end")
    async def end(self,interaction,button):
        init_user(interaction.user)
        uid=str(interaction.user.id)

        start=datetime.fromisoformat(data[uid]["start_time"])
        diff=(datetime.now()-start).total_seconds()

        data[uid]["total_time"]+=diff
        data[uid]["history"].append({
            "start":data[uid]["start_time"],
            "end":datetime.now().isoformat()
        })

        data[uid]["is_working"]=False
        data[uid]["start_time"]=None
        save_data(data)

        await update_status()  # 🔥追加

        await interaction.response.edit_message(embed=self.embed(),view=self)

# ------------------------
# 起動
# ------------------------
@bot.event
async def on_ready():
    global work_view
    work_view=WorkView()
    bot.add_view(work_view)
    await tree.sync()

    await update_status()  # 🔥追加

    print("起動OK")

bot.run(os.getenv("TOKEN"))
