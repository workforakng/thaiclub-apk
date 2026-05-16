
# ThaiClub Auto-Bet App — Kivy Android v3.2
# API: api.01.versedkh.online  /  api.thaiclub1.us.cc (login)

import json, hashlib, random, threading, time, os, re
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex
from kivy.uix.widget import Widget
import urllib.request, urllib.error

# ── Palette ──────────────────────────────────────────────────────────────────
BG       = get_color_from_hex("#0a0c12")
SURFACE  = get_color_from_hex("#12151f")
SURF2    = get_color_from_hex("#1a1e2e")
SURF3    = get_color_from_hex("#222840")
ACCENT   = get_color_from_hex("#00d4aa")
ACCENT2  = get_color_from_hex("#7c3aed")
RED      = get_color_from_hex("#f43f5e")
GREEN    = get_color_from_hex("#10b981")
YELLOW   = get_color_from_hex("#f59e0b")
BLUE     = get_color_from_hex("#3b82f6")
TEXT     = get_color_from_hex("#e2e8f0")
TEXTD    = get_color_from_hex("#64748b")

Window.clearcolor = BG

# ── Constants ─────────────────────────────────────────────────────────────────
THAI_LOGIN_API = "https://api.thaiclub1.us.cc"
THAI_API       = "https://api.01.versedkh.online"
DRAW_API       = "https://draw.01.versedkh.online"
UA = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36"
AR_ORIGIN      = "https://thaiclub1.us.cc"

# ── Crypto helpers ────────────────────────────────────────────────────────────
def md5sig(data: dict) -> str:
    clean = {k: v for k, v in data.items() if v != ""}
    sd    = dict(sorted(clean.items()))
    j     = json.dumps(sd, separators=(",", ":"), ensure_ascii=False)
    return hashlib.md5(j.encode()).hexdigest().upper()

def rnd_hex(n=32):
    return "".join(random.choices("abcdef0123456789", k=n))

def rnd_num():
    return random.randint(100_000_000_000, 999_999_999_999)

def device_id():
    return rnd_hex(32)

# ── HTTP helpers ──────────────────────────────────────────────────────────────
def http_get(url, token=None, timeout=8):
    req = urllib.request.Request(url, headers={
        "Accept": "application/json, text/plain, */*",
        "User-Agent": UA,
    })
    if token: req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def http_post(url, payload, token=None, extra_headers=None, timeout=8):
    body = json.dumps(payload, separators=(",", ":")).encode()
    req  = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": UA,
    })
    if token:          req.add_header("Authorization", f"Bearer {token}")
    if extra_headers:
        for k, v in extra_headers.items(): req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

# ── API functions ─────────────────────────────────────────────────────────────
def api_login(username, password):
    """Login with username+password, returns token"""
    ts  = int(time.time())
    rnd = rnd_hex(32)
    sig_data = {
        "username": username, "pwd": password,
        "phonetype": 1, "logintype": "mobile",
        "packId": "", "deviceId": device_id(),
        "language": 0, "random": rnd,
    }
    sig = md5sig(sig_data)
    payload = {**sig_data, "signature": sig, "timestamp": ts}
    payload = json.loads(
        json.dumps(payload, separators=(",", ":")))
    d = http_post(f"{THAI_LOGIN_API}/api/webapi/Login", payload,
                  extra_headers={"Ar-Origin": AR_ORIGIN})
    if d.get("code") != 0:
        raise Exception(d.get("msg", "Login failed"))
    return d["data"]["token"]

def api_get_balance(token, game_code="WinGo_30S"):
    ts  = int(time.time())
    rn  = rnd_num()
    sig = md5sig({"language": "en", "random": rn, "timestamp": ts})
    url = (f"{THAI_API}/api/Lottery/GetBalance"
           f"?language=en&random={rn}&signature={sig}&timestamp={ts}")
    d = http_get(url, token=token)
    if d.get("code") != 0:
        raise Exception(d.get("msg", "Balance error"))
    return float(d["data"]["balance"])

def api_get_next_issue(token, game_code):
    url = f"{DRAW_API}/WinGo/{game_code}/GetHistoryIssuePage.json?ts={int(time.time()*1000)}"
    d   = http_get(url, token=token)
    latest = d["data"]["list"][0]["issueNumber"]
    return str(int(latest) + 1)

def api_get_daman(game_code):
    url = f"{DRAW_API}/WinGo/{game_code}/GetHistoryIssuePage.json?ts={int(time.time()*1000)}"
    d   = http_get(url)
    row = d["data"]["list"][0]
    return int(row["number"]), row["color"], row["issueNumber"]

def api_place_bet(token, issue, bet_content, amount, game_code):
    ts  = int(time.time())
    rn  = rnd_num()
    sig = md5sig({
        "amount": amount, "betContent": bet_content, "betMultiple": 1,
        "gameCode": game_code, "issueNumber": issue,
        "language": "en", "random": rn, "timestamp": ts,
    })
    payload = {
        "gameCode": game_code, "issueNumber": issue,
        "amount": amount, "betMultiple": 1,
        "betContent": bet_content, "language": "en",
        "random": rn, "signature": sig, "timestamp": ts,
    }
    ref = f"{AR_ORIGIN}/#/saasLottery/WinGo?gameCode={game_code}&lottery=WinGo"
    d = http_post(f"{THAI_API}/api/Lottery/WinGoBet", payload, token=token,
                  extra_headers={"Referer": ref})
    if d.get("code") != 0:
        raise Exception(d.get("msg", "Bet failed"))

def decide_bet(daman_num, strategy, rng_rate=20):
    is_big = daman_num >= 5
    if strategy == "mirror":     big = is_big
    elif strategy == "opposite": big = not is_big
    else:                        big = (not is_big) if random.randint(1,100) <= rng_rate else is_big
    return ("BigSmall_Big", "BIG") if big else ("BigSmall_Small", "SMALL")

def calc_progressive_bet(base, max_bet, streak, mode):
    if mode == "martingale" and streak > 0:
        return min(base * (2 ** streak), max_bet)
    elif mode == "anti_martingale" and streak > 0:
        return min(base * (2 ** streak), max_bet)
    return base

# ── Reusable Widgets ──────────────────────────────────────────────────────────
class Card(BoxLayout):
    def __init__(self, bg=None, radius=12, **kw):
        super().__init__(**kw)
        self._bg = bg or SURFACE
        self._r  = radius
        self.bind(pos=self._draw, size=self._draw)
    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self._r])

class Btn(Button):
    def __init__(self, bg=None, fg=None, radius=10, **kw):
        super().__init__(**kw)
        self.bg = bg or ACCENT; self.fg = fg or BG
        self._r = radius
        self.background_normal = ""; self.background_color = (0,0,0,0)
        self.color = self.fg; self.font_size = sp(14); self.bold = True
        self.bind(pos=self._draw, size=self._draw)
    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self._r])

class Lbl(Label):
    def __init__(self, **kw):
        kw.setdefault("color", TEXT); kw.setdefault("font_size", sp(13))
        super().__init__(**kw)

def sep(h=1):
    w = Widget(size_hint_y=None, height=dp(h))
    with w.canvas:
        Color(*SURF3); RoundedRectangle(pos=w.pos, size=w.size)
    return w

def field(hint, password=False, val="", input_filter=None):
    ti = TextInput(
        hint_text=hint, text=val, multiline=False,
        password=password, input_filter=input_filter,
        size_hint_y=None, height=dp(44),
        background_color=SURF2, foreground_color=TEXT,
        hint_text_color=TEXTD, cursor_color=ACCENT,
        padding=[dp(12), dp(10)], font_size=sp(13))
    return ti

def section_label(txt):
    return Lbl(text=txt, color=ACCENT, bold=True, font_size=sp(12),
               size_hint_y=None, height=dp(26), halign="left")

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))

        # Header
        hbox = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(100), spacing=dp(4))
        hbox.add_widget(Lbl(text="🎰 ThaiClub AutoBet", font_size=sp(24), bold=True,
                            color=ACCENT, size_hint_y=None, height=dp(40), halign="center"))
        hbox.add_widget(Lbl(text="versedkh API · v3.2", font_size=sp(12), color=TEXTD,
                            size_hint_y=None, height=dp(20), halign="center"))
        root.add_widget(hbox)

        # Tab selector
        tab_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.tab_jwt  = Btn(text="JWT Token", bg=ACCENT, fg=BG)
        self.tab_cred = Btn(text="Username / Password", bg=SURF3, fg=TEXT)
        self.tab_jwt.bind(on_press=lambda _: self.show_tab("jwt"))
        self.tab_cred.bind(on_press=lambda _: self.show_tab("cred"))
        tab_row.add_widget(self.tab_jwt)
        tab_row.add_widget(self.tab_cred)
        root.add_widget(tab_row)

        # ── JWT panel ────────────────────────────────────────────────────────
        self.jwt_panel = Card(orientation="vertical", padding=dp(14),
                              spacing=dp(10), size_hint_y=None, height=dp(130))
        self.jwt_panel.add_widget(section_label("JWT Bearer Token"))
        self.jwt_input = TextInput(
            hint_text="Paste full JWT token here…", multiline=True,
            size_hint_y=None, height=dp(80),
            background_color=SURF2, foreground_color=TEXT,
            hint_text_color=TEXTD, cursor_color=ACCENT,
            padding=[dp(10), dp(8)], font_size=sp(10))
        self.jwt_panel.add_widget(self.jwt_input)
        root.add_widget(self.jwt_panel)

        # ── Credential panel ─────────────────────────────────────────────────
        self.cred_panel = Card(orientation="vertical", padding=dp(14),
                               spacing=dp(10), size_hint_y=None, height=dp(130))
        self.cred_panel.add_widget(section_label("Phone Number (with country code)"))
        self.uname_input = field("e.g. 918102516848")
        self.cred_panel.add_widget(self.uname_input)
        self.cred_panel.add_widget(section_label("Password"))
        self.pass_input  = field("Password", password=True)
        self.cred_panel.add_widget(self.pass_input)
        self.cred_panel.opacity = 0
        self.cred_panel.disabled = True
        root.add_widget(self.cred_panel)

        # ── Config card ──────────────────────────────────────────────────────
        cfg = Card(orientation="vertical", padding=dp(14), spacing=dp(10),
                   size_hint_y=None, height=dp(240))

        cfg.add_widget(section_label("Game Mode"))
        self.game_sp = Spinner(
            text="WinGo_30S  (30 sec)", size_hint_y=None, height=dp(42),
            values=["WinGo_30S  (30 sec)", "WinGo_1M   (1 min)"],
            background_color=SURF2, color=TEXT, font_size=sp(13))
        cfg.add_widget(self.game_sp)

        cfg.add_widget(section_label("Strategy"))
        self.strat_sp = Spinner(
            text="Mirror  (copy Daman)", size_hint_y=None, height=dp(42),
            values=["Mirror  (copy Daman)", "Opposite  (flip Daman)",
                    "Random Opposite  (20% flip)"],
            background_color=SURF2, color=TEXT, font_size=sp(13))
        cfg.add_widget(self.strat_sp)

        row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        b1 = BoxLayout(orientation="vertical", spacing=dp(4))
        b1.add_widget(Lbl(text="Bet Amount", color=TEXTD, font_size=sp(11),
                          size_hint_y=None, height=dp(16)))
        self.bet_in = field("10", val="10", input_filter="float")
        b1.add_widget(self.bet_in)
        b2 = BoxLayout(orientation="vertical", spacing=dp(4))
        b2.add_widget(Lbl(text="Rounds", color=TEXTD, font_size=sp(11),
                          size_hint_y=None, height=dp(16)))
        self.rounds_in = field("10", val="10", input_filter="int")
        b2.add_widget(self.rounds_in)
        row.add_widget(b1); row.add_widget(b2)
        cfg.add_widget(row)
        root.add_widget(cfg)

        # Login btn
        self.login_btn = Btn(text="🚀  CONNECT", size_hint_y=None, height=dp(52))
        self.login_btn.bind(on_press=self.do_connect)
        root.add_widget(self.login_btn)

        self.status = Lbl(text="", color=TEXTD, font_size=sp(12),
                          size_hint_y=None, height=dp(26), halign="center")
        root.add_widget(self.status)
        root.add_widget(Widget())

        sv = ScrollView(); sv.add_widget(root)
        self.add_widget(sv)
        self._tab = "jwt"

    def show_tab(self, tab):
        self._tab = tab
        if tab == "jwt":
            self.jwt_panel.opacity = 1;  self.jwt_panel.disabled  = False
            self.cred_panel.opacity = 0; self.cred_panel.disabled = True
            self.tab_jwt.bg  = ACCENT;   self.tab_jwt.fg  = BG
            self.tab_cred.bg = SURF3;    self.tab_cred.fg = TEXT
        else:
            self.jwt_panel.opacity = 0;  self.jwt_panel.disabled  = True
            self.cred_panel.opacity = 1; self.cred_panel.disabled = False
            self.tab_cred.bg = ACCENT;   self.tab_cred.fg = BG
            self.tab_jwt.bg  = SURF3;    self.tab_jwt.fg  = TEXT
        self.tab_jwt._draw(); self.tab_cred._draw()

    def set_status(self, msg, col=None):
        self.status.text  = msg
        self.status.color = col or TEXTD

    def do_connect(self, *_):
        game_code = "WinGo_30S" if "30S" in self.game_sp.text else "WinGo_1M"
        strategy  = ("mirror" if "Mirror" in self.strat_sp.text
                     else "opposite" if "Opposite" in self.strat_sp.text and "Random" not in self.strat_sp.text
                     else "random_opposite")
        bet_amt  = float(self.bet_in.text or "10")
        rounds   = int(self.rounds_in.text or "10")

        self.login_btn.text = "Connecting…"
        self.set_status("⏳ Verifying…", YELLOW)

        if self._tab == "jwt":
            token = self.jwt_input.text.strip()
            if not token:
                self.set_status("⚠️ Paste JWT token first", RED)
                self.login_btn.text = "🚀  CONNECT"; return
            threading.Thread(target=self._bg_jwt,
                args=(token, game_code, strategy, bet_amt, rounds), daemon=True).start()
        else:
            uname = self.uname_input.text.strip()
            pwd   = self.pass_input.text.strip()
            if not uname or not pwd:
                self.set_status("⚠️ Enter username and password", RED)
                self.login_btn.text = "🚀  CONNECT"; return
            threading.Thread(target=self._bg_cred,
                args=(uname, pwd, game_code, strategy, bet_amt, rounds), daemon=True).start()

    def _bg_jwt(self, token, *args):
        try:
            bal = api_get_balance(token)
            Clock.schedule_once(lambda dt: self._success(token, bal, *args))
        except Exception as e:
            Clock.schedule_once(lambda dt, err=str(e): self._fail(err))

    def _bg_cred(self, uname, pwd, *args):
        try:
            token = api_login(uname, pwd)
            bal   = api_get_balance(token)
            Clock.schedule_once(lambda dt: self._success(token, bal, *args))
        except Exception as e:
            Clock.schedule_once(lambda dt, err=str(e): self._fail(err))

    def _success(self, token, bal, game_code, strategy, bet_amt, rounds):
        app = App.get_running_app()
        app.state.update(token=token, game_code=game_code, strategy=strategy,
                         bet_amount=bet_amt, max_rounds=rounds,
                         balance=bal, initial_balance=bal, running=False, paused=False,
                         # timing defaults
                         trigger_sec=26 if "30S" in game_code else 57,
                         trigger_sec_2=57 if "30S" in game_code else -1,
                         fetch_sec=20  if "30S" in game_code else 40,
                         fetch_sec_2=50 if "30S" in game_code else -1,
                         bal_check_sec=10 if "30S" in game_code else 20,
                         bal_check_sec_2=40 if "30S" in game_code else -1,
                         settle_delay=10,
                         # progressive
                         prog_mode="none", prog_base=bet_amt, prog_max=bet_amt*10,
                         stop_profit=0, stop_loss=0,
                         rng_rate=20)
        self.login_btn.text = "🚀  CONNECT"
        self.login_btn.bg   = ACCENT
        app.root.transition = SlideTransition(direction="left")
        app.root.current    = "dashboard"

    def _fail(self, err):
        self.login_btn.text = "🚀  CONNECT"
        self.set_status(f"❌ {err[:70]}", RED)

# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS POPUP
# ══════════════════════════════════════════════════════════════════════════════
def open_settings(state, on_save=None):
    sv = ScrollView(size_hint=(1,1))
    box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10),
                    size_hint_y=None)
    box.bind(minimum_height=box.setter("height"))

    fields_map = {}

    def add_row(label, key, filt=None, pw=False):
        row = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(6),
                        orientation="vertical")
        row.add_widget(Lbl(text=label, color=TEXTD, font_size=sp(11),
                           size_hint_y=None, height=dp(18), halign="left"))
        ti = field("", val=str(state.get(key, "")), input_filter=filt, password=pw)
        row.add_widget(ti)
        box.add_widget(row)
        fields_map[key] = ti

    def add_spinner(label, key, values, cur_map):
        row = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(6),
                        orientation="vertical")
        row.add_widget(Lbl(text=label, color=TEXTD, font_size=sp(11),
                           size_hint_y=None, height=dp(18), halign="left"))
        cur_val = cur_map.get(state.get(key, ""), values[0])
        sp_w = Spinner(text=cur_val, values=values, size_hint_y=None, height=dp(40),
                       background_color=SURF2, color=TEXT, font_size=sp(13))
        box.add_widget(row)
        box.add_widget(sp_w)
        fields_map[key] = sp_w

    # ── Timing ───────────────────────────────────────────────────────────────
    box.add_widget(section_label("⏱  Timing Settings"))
    add_row("Trigger Second #1 (default 26)", "trigger_sec", "int")
    add_row("Trigger Second #2 (default 57 for 30S)", "trigger_sec_2", "int")
    add_row("Pre-fetch Issue At #1", "fetch_sec", "int")
    add_row("Pre-fetch Issue At #2", "fetch_sec_2", "int")
    add_row("Balance Check At #1", "bal_check_sec", "int")
    add_row("Balance Check At #2", "bal_check_sec_2", "int")
    add_row("Settlement Delay (seconds)", "settle_delay", "int")

    # ── Bet settings ─────────────────────────────────────────────────────────
    box.add_widget(section_label("💰  Bet Settings"))
    add_row("Bet Amount", "bet_amount", "float")
    add_row("Max Rounds", "max_rounds", "int")
    add_row("Stop Profit (0=off)", "stop_profit", "float")
    add_row("Stop Loss   (0=off)", "stop_loss", "float")

    # ── Progressive ──────────────────────────────────────────────────────────
    box.add_widget(section_label("📈  Progressive Mode"))
    add_spinner("Progressive Mode", "prog_mode",
                ["none", "martingale  (double on loss)",
                 "anti_martingale  (double on win)"],
                {"none": "none",
                 "martingale": "martingale  (double on loss)",
                 "anti_martingale": "anti_martingale  (double on win)"})
    add_row("Progressive Base Bet", "prog_base", "float")
    add_row("Progressive Max Bet", "prog_max", "float")

    # ── Strategy ─────────────────────────────────────────────────────────────
    box.add_widget(section_label("🎯  Strategy"))
    add_spinner("Strategy", "strategy",
                ["mirror  (copy Daman)", "opposite  (flip)",
                 "random_opposite  (flip %)"],
                {"mirror": "mirror  (copy Daman)",
                 "opposite": "opposite  (flip)",
                 "random_opposite": "random_opposite  (flip %)"})
    add_row("Random Flip Rate % (for Random Opposite)", "rng_rate", "int")

    sv.add_widget(box)

    def save_all(*_):
        for key, widget in fields_map.items():
            val = widget.text if hasattr(widget, "text") else ""
            # for Spinners pick first word
            if hasattr(widget, "values"):
                val = widget.text.split()[0]
            try:
                if key in ("trigger_sec","trigger_sec_2","fetch_sec","fetch_sec_2","bal_check_sec","bal_check_sec_2",
                           "settle_delay","max_rounds","rng_rate"):
                    state[key] = int(val)
                elif key in ("bet_amount","stop_profit","stop_loss",
                             "prog_base","prog_max"):
                    state[key] = float(val)
                else:
                    state[key] = val
            except: pass
        if on_save: on_save()
        p.dismiss()

    save_btn = Btn(text="💾  Save Settings", size_hint_y=None, height=dp(48))
    save_btn.bind(on_press=save_all)
    box.add_widget(save_btn)

    p = Popup(title="⚙️  Settings", content=sv, size_hint=(0.97, 0.94),
              background_color=SURFACE, title_color=ACCENT,
              separator_color=ACCENT)
    p.open()

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class DashboardScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._log  = []   # list of dicts: time,tag,msg,color
        self._hist = []   # list of dicts: round,issue,daman,bet,amt,result,pl,balance
        self._stats = dict(rounds=0, wins=0, losses=0, wagered=0.0, pl=0.0,
                           win_streak=0, loss_streak=0, best_win=0, worst_loss=0)
        self._running = False

        # ── Root layout ──────────────────────────────────────────────────────
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))

        # ── Top bar ──────────────────────────────────────────────────────────
        top = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        back = Btn(text="←", bg=SURF3, fg=TEXT, size_hint_x=None, width=dp(42))
        back.bind(on_press=self.go_back)
        top.add_widget(back)
        title = Lbl(text="ThaiClub AutoBet", bold=True, color=ACCENT, font_size=sp(17))
        top.add_widget(title)
        self.bal_lbl = Lbl(text="💰 --", color=GREEN, font_size=sp(14),
                           size_hint_x=None, width=dp(120), halign="right")
        top.add_widget(self.bal_lbl)
        root.add_widget(top)

        # ── Stats strip ──────────────────────────────────────────────────────
        self.stat_cards = {}
        stats_row = BoxLayout(size_hint_y=None, height=dp(76), spacing=dp(6))
        for key, label, col in [
                ("rounds", "Rounds",  ACCENT),
                ("wins",   "Wins",    GREEN),
                ("losses", "Losses",  RED),
                ("pl",     "P / L",   YELLOW)]:
            c = Card(orientation="vertical", padding=dp(6), bg=SURF2)
            c.add_widget(Lbl(text=label, font_size=sp(10), color=TEXTD,
                             size_hint_y=None, height=dp(18), halign="center"))
            lbl = Lbl(text="0", font_size=sp(20), bold=True, color=col,
                      halign="center")
            c.add_widget(lbl)
            self.stat_cards[key] = lbl
            stats_row.add_widget(c)
        root.add_widget(stats_row)

        # ── Streak row ───────────────────────────────────────────────────────
        self.streak_lbl = Lbl(text="Streak: --  |  Best W: --  |  Worst L: --",
                              font_size=sp(11), color=TEXTD, size_hint_y=None,
                              height=dp(22), halign="center")
        root.add_widget(self.streak_lbl)

        # ── Progress / status ─────────────────────────────────────────────────
        prog_box = BoxLayout(orientation="vertical", size_hint_y=None,
                             height=dp(46), spacing=dp(4))
        self.prog_lbl = Lbl(text="Idle", color=TEXTD, font_size=sp(11),
                            size_hint_y=None, height=dp(20), halign="left")
        self.prog_bar = ProgressBar(max=100, value=0,
                                    size_hint_y=None, height=dp(18))
        prog_box.add_widget(self.prog_lbl)
        prog_box.add_widget(self.prog_bar)
        root.add_widget(prog_box)

        # ── Live log ─────────────────────────────────────────────────────────
        log_card = Card(padding=dp(8), bg=SURF2)
        self.log_sv  = ScrollView()
        self.log_box = BoxLayout(orientation="vertical", size_hint_y=None,
                                 spacing=dp(2))
        self.log_box.bind(minimum_height=self.log_box.setter("height"))
        self.log_sv.add_widget(self.log_box)
        log_card.add_widget(self.log_sv)
        root.add_widget(log_card)

        # ── Control buttons ───────────────────────────────────────────────────
        ctrl = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        self.start_btn = Btn(text="▶  START", bg=ACCENT)
        self.pause_btn = Btn(text="⏸  PAUSE", bg=SURF3, fg=TEXT)
        self.start_btn.bind(on_press=self.toggle_run)
        self.pause_btn.bind(on_press=self.toggle_pause)
        ctrl.add_widget(self.start_btn)
        ctrl.add_widget(self.pause_btn)
        root.add_widget(ctrl)

        # ── Bottom action bar ─────────────────────────────────────────────────
        bot = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        for txt, cb in [("💰 Balance", self.refresh_balance),
                        ("📊 History", self.show_history),
                        ("⚙️ Settings", self.show_settings),
                        ("🔄 Refresh", self.refresh_balance)]:
            b = Btn(text=txt, bg=SURF3, fg=TEXT, radius=8)
            b.bind(on_press=cb)
            bot.add_widget(b)
        root.add_widget(bot)

        self.add_widget(root)
        Clock.schedule_interval(self._tick, 0.5)

    # ── Clock tick ────────────────────────────────────────────────────────────
    def _tick(self, dt):
        app  = App.get_running_app()
        s    = app.state
        sec  = int(time.time()) % 60
        game = s.get("game_code", "--")
        trig = s.get("trigger_sec", "?")
        trig2 = s.get("trigger_sec_2", -1)
        fetch= s.get("fetch_sec", "?")
        fetch2= s.get("fetch_sec_2", -1)
        status = "🔴 Stopped" if not s.get("running") else ("⏸ Paused" if s.get("paused") else "🟢 Running")
        extra = f" / Bet@{trig2}s Fetch@{fetch2}s" if trig2 != -1 else ""
        self.prog_lbl.text = (f"{status}  |  ⏱ {sec}s  |  {game}  "
                              f"|  Bet@{trig}s  Fetch@{fetch}s{extra}")

    # ── Logging ───────────────────────────────────────────────────────────────
    def log(self, tag, msg, color=None):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.append({"t": ts, "tag": tag, "msg": msg})
        full = f"[{ts}] [{tag}] {msg}"
        lbl  = Lbl(text=full, color=color or TEXTD, font_size=sp(10.5),
                   size_hint_y=None, height=dp(20),
                   text_size=(Window.width - dp(40), None),
                   halign="left", valign="middle")
        self.log_box.add_widget(lbl)
        if len(self.log_box.children) > 300:
            self.log_box.remove_widget(self.log_box.children[-1])
        Clock.schedule_once(lambda dt: setattr(self.log_sv, "scroll_y", 0), 0.05)

    # ── Balance update ────────────────────────────────────────────────────────
    def update_balance(self, new_bal, old_bal=None):
        app = App.get_running_app()
        app.state["balance"] = new_bal
        self.bal_lbl.text = f"💰 {new_bal:.2f}"
        # P/L vs session start
        init = float(app.state.get("initial_balance", new_bal))
        pl   = new_bal - init
        self._stats["pl"] = pl
        self.stat_cards["pl"].text  = f"{pl:+.2f}"
        self.stat_cards["pl"].color = GREEN if pl >= 0 else RED
        # Round P/L
        if old_bal is not None:
            rpl = new_bal - old_bal
            return rpl
        return None

    def refresh_stats(self):
        s = self._stats
        self.stat_cards["rounds"].text  = str(s["rounds"])
        self.stat_cards["wins"].text    = str(s["wins"])
        self.stat_cards["losses"].text  = str(s["losses"])
        # streak label
        streak_txt = ("🔥" if s["win_streak"] > 0 else "❄️")
        val = s["win_streak"] if s["win_streak"] > 0 else -s["loss_streak"]
        self.streak_lbl.text = (
            f"Streak: {val:+d}  |  Best W: {s['best_win']}  |  "
            f"Worst L: {s['worst_loss']}")

    # ── Controls ──────────────────────────────────────────────────────────────
    def toggle_run(self, *_):
        app = App.get_running_app()
        if app.state.get("running"):
            app.state["running"] = False
            self.start_btn.text = "▶  START"; self.start_btn.bg = ACCENT
            self.log("System", "Stopped by user", YELLOW)
        else:
            # Reset per-session stats
            for k in self._stats: self._stats[k] = 0 if isinstance(self._stats[k],int) else 0.0
            app.state["running"] = True; app.state["paused"] = False
            self.start_btn.text = "⏹  STOP"; self.start_btn.bg = RED
            self.log("System", f"Started | {app.state['game_code']} | "
                               f"{app.state['strategy']}", GREEN)
            threading.Thread(target=self._loop, daemon=True).start()

    def toggle_pause(self, *_):
        app = App.get_running_app()
        p = not app.state.get("paused", False)
        app.state["paused"] = p
        self.pause_btn.text = "▶ RESUME" if p else "⏸  PAUSE"
        self.pause_btn.bg   = GREEN if p else SURF3
        self.pause_btn.fg   = BG if p else TEXT
        Clock.schedule_once(lambda dt: self.log("System",
            "Paused" if p else "Resumed", YELLOW if p else GREEN))

    def go_back(self, *_):
        App.get_running_app().state["running"] = False
        App.get_running_app().root.transition = SlideTransition(direction="right")
        App.get_running_app().root.current    = "login"

    def show_settings(self, *_):
        open_settings(App.get_running_app().state,
                      on_save=lambda: self.log("Settings", "Saved ✅", ACCENT))

    def show_history(self, *_):
        if not self._hist:
            self._popup_msg("📊 History", "No bets placed yet.")
            return
        sv  = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4), padding=dp(8))
        box.bind(minimum_height=box.setter("height"))
        headers = ["#","Issue","Daman","Bet","Amt","Result","P/L","Bal"]
        hrow = BoxLayout(size_hint_y=None, height=dp(22))
        for h in headers:
            hrow.add_widget(Lbl(text=h, font_size=sp(10), bold=True, color=ACCENT,
                                size_hint_x=1/len(headers), halign="center"))
        box.add_widget(hrow)
        for h in reversed(self._hist):
            row = BoxLayout(size_hint_y=None, height=dp(22))
            for val in [h["round"],h["issue"][-4:],h["daman"],h["bet"],
                        h["amt"],h["result"],f"{h['pl']:+.2f}",f"{h['bal']:.2f}"]:
                col = GREEN if h["result"]=="WIN" else (RED if h["result"]=="LOSS" else TEXTD)
                row.add_widget(Lbl(text=str(val), font_size=sp(10), color=col,
                                   size_hint_x=1/len(headers), halign="center"))
            box.add_widget(row)
        sv.add_widget(box)
        p = Popup(title="📊 Bet History", content=sv,
                  size_hint=(0.98, 0.92), background_color=SURFACE, title_color=ACCENT)
        p.open()

    def _popup_msg(self, title, msg):
        p = Popup(title=title, content=Lbl(text=msg, halign="center"),
                  size_hint=(0.8, 0.3), background_color=SURFACE, title_color=ACCENT)
        p.open()

    def refresh_balance(self, *_):
        app = App.get_running_app()
        def bg():
            try:
                b = api_get_balance(app.state["token"])
                Clock.schedule_once(lambda dt: self.update_balance(b))
                Clock.schedule_once(lambda dt: self.log("Balance", f"{b:.2f}", GREEN))
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e):
                    self.log("Balance", f"Error: {err}", RED))
        threading.Thread(target=bg, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # CORE BETTING LOOP
    # ══════════════════════════════════════════════════════════════════════════
    def _loop(self):
        app   = App.get_running_app()
        st    = app.state

        def gs(k, d): return st.get(k, d)

        token      = gs("token", "")
        game_code  = gs("game_code", "WinGo_30S")
        strategy   = gs("strategy", "mirror")
        max_rounds = int(gs("max_rounds", 10))

        rounds_done = 0
        cached_issue = None
        last_bet_key = ""
        last_bal_key = ""

        Clock.schedule_once(lambda dt: self.log("Loop",
            f"Game={game_code}  Trig1={st.get('trigger_sec')}s  Trig2={st.get('trigger_sec_2')}s  "
            f"Fetch1={st.get('fetch_sec')}s  Fetch2={st.get('fetch_sec_2')}s  Settle={st.get('settle_delay')}s",
            ACCENT))

        while st.get("running") and rounds_done < max_rounds:
            if st.get("paused"):
                time.sleep(0.5); continue

            # re-read live settings each iteration
            trigger_sec   = int(gs("trigger_sec", 26))
            trigger_sec_2 = int(gs("trigger_sec_2", 57 if "30S" in game_code else -1))
            fetch_sec     = int(gs("fetch_sec", 20))
            fetch_sec_2   = int(gs("fetch_sec_2", 50 if "30S" in game_code else -1))
            bal_check_sec = int(gs("bal_check_sec", 10))
            bal_check_sec_2 = int(gs("bal_check_sec_2", 40 if "30S" in game_code else -1))
            settle_delay  = int(gs("settle_delay", 10))
            bet_amount    = float(gs("bet_amount", 10))
            prog_mode     = gs("prog_mode", "none")
            prog_base     = float(gs("prog_base", bet_amount))
            prog_max      = float(gs("prog_max", bet_amount * 10))
            stop_profit   = float(gs("stop_profit", 0))
            stop_loss     = float(gs("stop_loss", 0))
            rng_rate      = int(gs("rng_rate", 20))

            now_sec = int(time.time()) % 60
            now_min = int(time.time()) // 60
            min_key = f"{now_min}"

            # ── Stop conditions ───────────────────────────────────────────────
            if stop_profit > 0 and self._stats["pl"] >= stop_profit:
                Clock.schedule_once(lambda dt: self.log("Stop",
                    f"🎯 Profit target reached! P/L={self._stats['pl']:+.2f}", GREEN))
                break
            if stop_loss > 0 and self._stats["pl"] <= -abs(stop_loss):
                Clock.schedule_once(lambda dt: self.log("Stop",
                    f"🛑 Stop-loss hit! P/L={self._stats['pl']:+.2f}", RED))
                break

            # ── Pre-fetch issue ───────────────────────────────────────────────
            if (now_sec == fetch_sec or now_sec == fetch_sec_2) and cached_issue is None:
                try:
                    cached_issue = api_get_next_issue(token, game_code)
                    issue_snap   = cached_issue
                    Clock.schedule_once(lambda dt, i=issue_snap:
                        self.log("Fetch", f"Issue {i}", ACCENT))
                except Exception as e:
                    Clock.schedule_once(lambda dt, err=str(e):
                        self.log("Fetch", f"Failed: {err}", RED))
                time.sleep(0.4); continue

            # ── Balance check ─────────────────────────────────────────────────
            if (now_sec == bal_check_sec or now_sec == bal_check_sec_2) and last_bal_key != f"{min_key}-{now_sec}":
                last_bal_key = f"{min_key}-{now_sec}"
                try:
                    b = api_get_balance(token)
                    Clock.schedule_once(lambda dt, bal=b: self.update_balance(bal))
                    Clock.schedule_once(lambda dt, bal=b:
                        self.log("Bal", f"{bal:.2f}", BLUE))
                except: pass

            # ── Reset cached issue ────────────────────────────────────────────
            if now_sec < min(fetch_sec, fetch_sec_2 if fetch_sec_2 != -1 else fetch_sec):
                if cached_issue and last_bet_key == min_key:
                    cached_issue = None   # clear after successful round

            # ── Betting window ────────────────────────────────────────────────
            if (now_sec == trigger_sec or now_sec == trigger_sec_2) and last_bet_key != f"{min_key}-{now_sec}":
                last_bet_key = f"{min_key}-{now_sec}"

                # Late fetch if pre-fetch missed
                if cached_issue is None:
                    try:
                        cached_issue = api_get_next_issue(token, game_code)
                        Clock.schedule_once(lambda dt, i=cached_issue:
                            self.log("Fetch", f"Late-fetch {i}", YELLOW))
                    except Exception as e:
                        Clock.schedule_once(lambda dt, err=str(e):
                            self.log("Fetch", f"Late-fail: {err}", RED))
                        cached_issue = None
                        time.sleep(0.5); continue

                # Daman result
                try:
                    daman_num, daman_color, _ = api_get_daman(game_code)
                except Exception as e:
                    Clock.schedule_once(lambda dt, err=str(e):
                        self.log("Daman", f"Error: {err}", RED))
                    time.sleep(0.5); continue

                # Calculate bet amount
                if prog_mode != "none":
                    ws = self._stats["win_streak"]
                    ls = self._stats["loss_streak"]
                    streak = ws if "anti" in prog_mode else ls
                    actual_bet = calc_progressive_bet(prog_base, prog_max, streak, prog_mode.split()[0])
                else:
                    actual_bet = bet_amount

                bet_content, bet_name = decide_bet(daman_num, strategy, rng_rate)
                issue_to_bet = cached_issue
                d_type = "BIG" if daman_num >= 5 else "SMALL"

                Clock.schedule_once(lambda dt,
                    n=daman_num, dc=daman_color, dt2=d_type, bn=bet_name,
                    r=rounds_done+1, mr=max_rounds, iss=issue_to_bet, a=actual_bet:
                    self.log("Round",
                        f"#{r}/{mr}  Daman={n}({dt2},{dc})  "
                        f"→ Bet {bn}  Issue={iss[-6:]}  Amt={a:.2f}", ACCENT))

                # Snapshot balance BEFORE bet for accurate P/L
                old_bal = float(st.get("balance", 0))

                # Place bet
                try:
                    api_place_bet(token, issue_to_bet, bet_content, actual_bet, game_code)
                    rounds_done += 1
                    self._stats["rounds"] = rounds_done
                    self._stats["wagered"] += actual_bet
                    Clock.schedule_once(lambda dt: self.log("Bet", "✅ Placed", GREEN))
                    Clock.schedule_once(lambda dt: self.refresh_stats())
                except Exception as e:
                    Clock.schedule_once(lambda dt, err=str(e):
                        self.log("Bet", f"❌ {err}", RED))
                    cached_issue = None
                    time.sleep(0.5); continue

                # Settlement countdown
                for i in range(settle_delay, 0, -1):
                    if not st.get("running"): break
                    Clock.schedule_once(lambda dt, s=i:
                        setattr(self, "_settle_txt", s))
                    Clock.schedule_once(lambda dt, s=i, tot=settle_delay:
                        setattr(self.prog_bar, "value",
                                (1 - s/tot) * 100))
                    Clock.schedule_once(lambda dt, s=i:
                        setattr(self.prog_lbl, "text",
                                f"⏳ Settling…  {s}s"))
                    time.sleep(1)

                # Get NEW balance (P/L computed accurately)
                try:
                    new_bal = api_get_balance(token)
                    rpl     = new_bal - old_bal
                    won     = rpl > 0
                    result  = "WIN" if won else "LOSS"

                    # Update streaks
                    if won:
                        self._stats["win_streak"]  += 1
                        self._stats["loss_streak"]  = 0
                        self._stats["wins"]        += 1
                        self._stats["best_win"] = max(
                            self._stats["best_win"], self._stats["win_streak"])
                    else:
                        self._stats["loss_streak"] += 1
                        self._stats["win_streak"]   = 0
                        self._stats["losses"]      += 1
                        self._stats["worst_loss"] = max(
                            self._stats["worst_loss"], self._stats["loss_streak"])

                    Clock.schedule_once(lambda dt, b=new_bal, r=rpl, w=won:
                        self._on_result(b, old_bal, r, w))

                    self._hist.append(dict(
                        round=rounds_done, issue=issue_to_bet,
                        daman=f"{daman_num}({daman_color})",
                        bet=bet_name, amt=f"{actual_bet:.2f}",
                        result=result, pl=rpl,
                        bal=new_bal))
                except Exception as e:
                    Clock.schedule_once(lambda dt, err=str(e):
                        self.log("Bal", f"Post-bet error: {err}", RED))

                cached_issue = None
                Clock.schedule_once(lambda dt: self.refresh_stats())
                Clock.schedule_once(lambda dt:
                    setattr(self.prog_bar, "value",
                            rounds_done / max_rounds * 100))
                time.sleep(1)
            else:
                time.sleep(0.3)

        Clock.schedule_once(lambda dt: self._done())

    def _on_result(self, new_bal, old_bal, rpl, won):
        tag = "WIN ✅" if won else "LOSS ❌"
        col = GREEN if won else RED
        self.log("Result", f"{tag}  Round P/L={rpl:+.2f}  Bal={new_bal:.2f}", col)
        self.update_balance(new_bal, old_bal)
        self.refresh_stats()

    def _done(self):
        app = App.get_running_app()
        app.state["running"] = False
        self.start_btn.text = "▶  START"; self.start_btn.bg = ACCENT
        s = self._stats
        self.log("Done",
            f"Rounds={s['rounds']}  W={s['wins']}  L={s['losses']}  "
            f"P/L={s['pl']:+.2f}  Wagered={s['wagered']:.2f}", ACCENT)

    def on_enter(self):
        app = App.get_running_app()
        b = app.state.get("balance", "--")
        self.bal_lbl.text = f"💰 {b}"
        self.log("System",
            f"Ready | {app.state.get('game_code')} | "
            f"Bet@{app.state.get('trigger_sec')}s/{app.state.get('trigger_sec_2')}s | "
            f"Strategy: {app.state.get('strategy')}", ACCENT)

# ══════════════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════════════
class ThaiClubApp(App):
    def build(self):
        self.state = {}
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(DashboardScreen(name="dashboard"))
        return sm

    def get_application_name(self): return "ThaiClub AutoBet"
    def get_application_icon(self):  return ""

if __name__ == "__main__":
    ThaiClubApp().run()
