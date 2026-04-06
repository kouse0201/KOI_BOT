import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta, timezone
import os

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

    # ★名前を毎回更新
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
# UTC→JST変換関数（重要）
# ------------------------
def to_jst(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(JST)

# ------------------------
# ★過去データ補正
# ------------------------
def fix_to_jst():
    changed = False

    for uid, u in data.items():

        st = u.get("start_time")
        if st:
            try:
                dt = to_jst(datetime.fromisoformat(st))
                u["start_time"] = dt.isoformat()
                changed = True
            except:
                pass

        for h in u.get("history", []):
            for key in ["start", "end"]:
                t = h.get(key)
                if t:
                    try:
                        dt = to_jst(datetime.fromisoformat(t))
                        h[key] = dt.isoformat()
                        changed = True
                    except:
                        pass

    if changed:
        save_data(data)

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
        "ちらし寿司(販売停止)":{"price":10000,"cost":3500},
        "本つげ櫛(販売停止)":{"price":10000,"cost":2500},
        "恋したあの人(販売停止)":{"price":7000,"cost":1500},
    },
    "移動販売メニュー":{
        "いっぱい飲みにKOIよセット":{"price":13000,"cost":5250},
        "温泉麦酒KOI心":{"price":6000,"cost":2250},
        "焼き鳥盛り合わせ":{"price":9000,"cost":3000},
        "がつ盛り焼きそば":{"price":6500,"cost":1750},
        "すき焼き御膳":{"price":30000,"cost":12000},
        "濃い黒たまご":{"price":6500,"cost":2000},
        "ブレンド珈琲饅頭(PIPEDOWN-South-)":{"price":100000,"cost":27500},
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
# 注文UI（そのまま）
# ------------------------
class AmountModal(discord.ui.Modal):
    def __init__(self,view,item):
        super().__init__(title=f"{item} 数量")
        self.view_ref=view
        self.item=item
        self.amount=discord.ui.TextInput(label="数量",default="1")
        self.add_item(self.amount)

    async def on_submit(self,interaction):
        try:
            qty=int(self.amount.value)
            if qty<=0: raise
        except:
            await interaction.response.send_message("数字入れて",ephemeral=True)
            return

        self.view_ref.cart[self.item]=qty
        await self.view_ref.update(interaction)

class CategorySelect(discord.ui.Select):
    def __init__(self, view, cat, items):
        options=[
            discord.SelectOption(label=k, description=yen(v["price"]))
            for k,v in items.items()
        ]
        super().__init__(placeholder=f"▼ {cat}", options=options)
        self.view_ref=view

    async def callback(self, interaction):
        await interaction.response.send_modal(
            AmountModal(self.view_ref, self.values[0])
        )

class RemoveButton(discord.ui.Button):
    def __init__(self, item, view):
        super().__init__(label=f"❌ {item}", style=discord.ButtonStyle.danger)
        self.item=item
        self.view_ref=view

    async def callback(self, interaction):
        self.view_ref.cart.pop(self.item,None)
        await self.view_ref.update(interaction)

class OrderView(discord.ui.View):
    def __init__(self, page=0, cart=None):
        super().__init__(timeout=None)
        self.page=page
        self.cart=cart or {}

        for cat, items in split_menu(page).items():
            self.add_item(CategorySelect(self,cat,items))

        for i,item in enumerate(self.cart.keys()):
            if i>=3: break
            self.add_item(RemoveButton(item,self))

        if page>0:
            self.add_item(discord.ui.Button(label="←戻る",style=discord.ButtonStyle.secondary,custom_id="prev"))

        if page<1:
            self.add_item(discord.ui.Button(label="次へ→",style=discord.ButtonStyle.secondary,custom_id="next"))

        self.add_item(discord.ui.Button(label="確定",style=discord.ButtonStyle.success,custom_id="confirm"))

    def calc_total(self):
        total=0
        for cat in MENU:
            for item,qty in self.cart.items():
                if item in MENU[cat]:
                    total+=MENU[cat][item]["price"]*qty
        return total

    async def update(self,interaction):
        text="【注文中】\n"
        for k,v in self.cart.items():
            text+=f"{k} ×{v}\n"
        text+=f"\n💰合計：{yen(self.calc_total())}"

        await interaction.response.edit_message(content=text,view=OrderView(self.page,self.cart))

    async def interaction_check(self,interaction):
        cid=interaction.data.get("custom_id")

        if cid=="next":
            await interaction.response.edit_message(view=OrderView(1,self.cart))
            return False

        if cid=="prev":
            await interaction.response.edit_message(view=OrderView(0,self.cart))
            return False

        if cid=="confirm":
            await interaction.response.defer()  # ←絶対必要

            uid=str(interaction.user.id)
            init_user(interaction.user)

            total=0
            cost=0
            worker=0
            text=""

            for cat in MENU:
                for item,qty in self.cart.items():
                    if item in MENU[cat]:
                        d=MENU[cat][item]
                        total+=d["price"]*qty
                        cost+=d["cost"]*qty
                        worker+=int((d["price"]-d["cost"])*0.7)*qty
                        text+=f"{item} ×{qty}\n"

            profit=total-cost-worker

            data[uid]["sales"]+=(total-cost)
            data[uid]["pay"]+=worker

            for item,qty in self.cart.items():
                data[uid]["items"][item]=data[uid]["items"].get(item,0)+qty

            save_data(data)

            ch=discord.utils.get(interaction.guild.text_channels,name="💹売上報告")
            if ch:
                await ch.send(
                    f"```\n📊売上報告\n販売者:{interaction.user.display_name}\n{text}\n"
                    f"請求:{yen(total)}\n原価:{yen(cost)}\n利益:{yen(profit)}\n給料:{yen(worker)}\n```"
                )

    # ------------------------
    # ★ここがポイント（リセット）
    # ------------------------
    self.cart = {}

    await interaction.edit_original_response(
        content="✅ 注文を確定しました\n\n🛒 カートをリセットしました",
        view=OrderView(self.page, self.cart)
    )

    return False

        return True

# ------------------------
# 勤務UI（修正済）
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

    @discord.ui.button(label="出勤", style=discord.ButtonStyle.success, custom_id="start")
    async def start(self, interaction, button):
        init_user(interaction.user)
        uid = str(interaction.user.id)
        data[uid]["is_working"] = True
        data[uid]["start_time"] = datetime.now(timezone.utc).astimezone(JST).isoformat()
        save_data(data)
        await interaction.response.edit_message(embed=self.embed(), view=self)
        await update_status()

    @discord.ui.button(label="退勤",style=discord.ButtonStyle.danger,custom_id="end")
    async def end(self,interaction,button):
        init_user(interaction.user)
        uid=str(interaction.user.id)

        start = to_jst(datetime.fromisoformat(data[uid]["start_time"]))
        now = datetime.now(timezone.utc).astimezone(JST)

        diff=(now-start).total_seconds()

        data[uid]["total_time"]+=diff
        data[uid]["history"].append({
            "start":data[uid]["start_time"],
            "end":now.isoformat()
        })

        data[uid]["is_working"]=False
        data[uid]["start_time"]=None
        save_data(data)

        await interaction.response.edit_message(embed=self.embed(),view=self)

    @discord.ui.button(label="オーダー",style=discord.ButtonStyle.primary,custom_id="order")
    async def order(self,interaction,button):
        await interaction.response.send_message("注文👇",view=OrderView(),ephemeral=True)

    @discord.ui.button(label="勤務時間",style=discord.ButtonStyle.secondary,custom_id="time_btn")
    async def time_btn(self,interaction,button):
        uid=str(interaction.user.id)
        u=data.get(uid,{})
        total=u.get("total_time",0)
        h=int(total//3600)
        m=int((total%3600)//60)

        history=u.get("history",[])
        text=f"{h}時間{m}分\n"
        for hst in history[-5:]:
            try:
                start = to_jst(datetime.fromisoformat(hst.get("start"))).strftime("%Y/%m/%d %H:%M")
                end = to_jst(datetime.fromisoformat(hst.get("end"))).strftime("%Y/%m/%d %H:%M")
                text += f"{start} → {end}\n"
            except:
                text += f"{hst.get('start')} → {hst.get('end')}\n"

        await interaction.response.send_message(text,ephemeral=True)

    @discord.ui.button(label="給料確認",style=discord.ButtonStyle.secondary,custom_id="pay_btn")
    async def pay_btn(self,interaction,button):
        uid=str(interaction.user.id)
        u=data.get(uid,{})
        await interaction.response.send_message(
            f"給料:{yen(u.get('pay',0))}\n売上:{yen(u.get('sales',0))}",
            ephemeral=True
        )

# ------------------------
# コマンド（そのまま）
# ------------------------
work_view=None

@tree.command(name="panel")
async def panel(interaction):
    await interaction.response.send_message(embed=work_view.embed(),view=work_view)

@tree.command(name="time")
async def time(interaction, member:discord.Member):
    uid = str(member.id)
    u = data.get(uid, {})

    total = u.get("total_time", 0)
    h = int(total // 3600)
    m = int((total % 3600) // 60)

    history = u.get("history", [])

    text = f"⏱ {member.display_name}\n合計：{h}時間{m}分\n\n"

    if history:
        text += "【出退勤履歴】\n"
        for hst in history[-5:]:
            try:
                start = to_jst(datetime.fromisoformat(hst.get("start"))).strftime("%Y/%m/%d %H:%M")
                end = to_jst(datetime.fromisoformat(hst.get("end"))).strftime("%Y/%m/%d %H:%M")
                text += f"{start} → {end}\n"
            except:
                text += f"{hst.get('start','?')} → {hst.get('end','?')}\n"
    else:
        text += "履歴なし"

    await interaction.response.send_message(text, ephemeral=True)

@tree.command(name="paying")
async def paying(interaction,member:discord.Member):
    u=data.get(str(member.id),{})
    await interaction.response.send_message(
        f"給料:{yen(u.get('pay',0))} 売上:{yen(u.get('sales',0))}",
        ephemeral=True
    )

@tree.command(name="edittime")
async def edittime(interaction,member:discord.Member,minutes:int):
    init_user(member)
    uid=str(member.id)
    data[uid]["total_time"]=max(0,data[uid]["total_time"]+minutes*60)
    save_data(data)
    await interaction.response.send_message("OK",ephemeral=True)

@tree.command(name="editpaying")
async def editpaying(interaction,member:discord.Member,target:str,amount:int):
    init_user(member)
    uid=str(member.id)
    if target=="給料":
        data[uid]["pay"]=max(0,data[uid]["pay"]+amount)
    elif target=="売上":
        data[uid]["sales"]=max(0,data[uid]["sales"]+amount)
    save_data(data)
    await interaction.response.send_message("OK",ephemeral=True)

@tree.command(name="resettime")
async def resettime(interaction,member:discord.Member):
    init_user(member)
    uid=str(member.id)
    data[uid]["total_time"]=0
    data[uid]["history"]=[]
    save_data(data)
    await interaction.response.send_message("OK",ephemeral=True)

@tree.command(name="resetpaying")
async def resetpaying(interaction,member:discord.Member):
    init_user(member)
    uid=str(member.id)
    data[uid]["pay"]=0
    save_data(data)
    await interaction.response.send_message("OK",ephemeral=True)

@tree.command(name="backup")
async def backup(interaction):
    try:
        await interaction.response.send_message(
            "📦 バックアップファイル👇",
            file=discord.File("data.json"),
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"エラー: {e}", ephemeral=True)

# ------------------------
# ★追加：全体商品ランキング（同順位対応）
# ------------------------
@tree.command(name="buy")
async def buy(interaction):
    all_items = {}
    for cat in MENU.values():
        for item in cat.keys():
            all_items[item] = 0

    for u in data.values():
        for item, qty in u.get("items", {}).items():
            if item in all_items:
                all_items[item] += qty
            else:
                all_items[item] = qty

    ranking = sorted(all_items.items(), key=lambda x: x[1], reverse=True)

    text = "📊【全体商品ランキング】\n\n"

    prev_qty = None
    rank = 0
    display_rank = 0

    for item, qty in ranking:
        rank += 1

        if qty != prev_qty:
            display_rank = rank
            prev_qty = qty

        text += f"{display_rank}位：{item} ×{qty}個\n"

    await interaction.response.send_message(text)

# ------------------------
# 起動
# ------------------------
@bot.event
async def on_ready():
    global work_view
    print("ログイン完了")

    fix_to_jst()

    work_view = WorkView()
    bot.add_view(work_view)
    await tree.sync()
    await update_status()
    update_status.start()

    print("起動OK2")

bot.run(os.getenv("TOKEN"))
