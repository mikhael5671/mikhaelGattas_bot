import json, os, re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler


TOKEN = "8736687534:AAHU6DrhmDGBKyJQMbDmmURpUlA6Ht-DaEE"
DATA_FILE = "data.json"

DAYS = {
    "السبت":"sat","الاحد":"sun","الأحد":"sun","الاثنين":"mon","الإثنين":"mon",
    "الثلاثاء":"tue","التلات":"tue","الاربعاء":"wed","الأربعاء":"wed",
    "الخميس":"thu","الجمعة":"fri","الجمعه":"fri"
}

def load():
    if os.path.exists(DATA_FILE):
        f = open(DATA_FILE, 'r', encoding='utf-8')
        data = json.load(f)
        f.close()
        return data
    return {"students":[],"attendance":[],"admins":{}}

def save(d):
    f = open(DATA_FILE, 'w', encoding='utf-8')
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.close()

def what(text):
    text = text.strip()
    if "-" in text:
        p = text.split("-")
        if len(p) >= 2:
            n = p[0].strip()
            ph = p[1].strip()
            if n and any(c.isdigit() for c in ph):
                return "reg", {"name":n,"phone":ph}
    if any(w in text for w in ["خلي الاشعار","ضبط الميعاد","غير الميعاد"]):
        return "time", text
    if any(w in text for w in ["ميعادي","الميعاد"]):
        return "mytime", None
    if any(w in text for w in ["اسجل","تسجيل","مخدوم","اضيف","جديد"]):
        return "want", None
    if any(w in text for w in ["انت بتعمل ايه","وظيفتك","مين انت"]):
        return "desc", None
    if any(w in text for w in ["احصائيات","تقرير","نسبة","غاب","حضر"]):
        return "ask", text
    if text in ["/start","هاي","هالو","اهلا","سلام"]:
        return "hi", None
    return "?", None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("اهلا!\n\nتسجيل: الاسم - الرقم\nتقرير: احصائيات\nضبط: خلي الاشعار يوم الجمعة 4\nميعادي: معرفة الميعاد")

async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    act, val = what(text)
    
    if act == "reg":
        d = load()
        d["students"].append({"name":val["name"],"phone":val["phone"],"active":True})
        save(d)
        await update.message.reply_text(f"تم!\nالاسم: {val['name']}\nالرقم: {val['phone']}")
        return
    
    if act == "want":
        await update.message.reply_text("اكتب: الاسم - الرقم\nمثال: ماركو - 01234567890")
        return
    
    if act == "ask":
        d = load()
        att = d.get("attendance", [])
        if not att:
            await update.message.reply_text("مفيش بيانات.")
            return
        stats = {}
        for r in att:
            n = r.get("student_name","?")
            s = r.get("status","")
            if n not in stats: stats[n] = {"حضر":0,"غاب":0}
            if s in stats[n]: stats[n][s] += 1
        rep = "تقرير:\n\n"
        for n, s in stats.items():
            t = s["حضر"] + s["غاب"]
            p = round(s["حضر"]/t*100) if t>0 else 0
            rep += f"{n}: حضر {s['حضر']} | غاب {s['غاب']} | {p}%\n"
        await update.message.reply_text(rep)
        return
    
    if act == "desc":
        await update.message.reply_text("بوت مدارس الاحد الذكي.\n\nتسجيل: الاسم - الرقم\nتقرير: احصائيات\nضبط: خلي الاشعار يوم الجمعة 4")
        return
    
    if act == "hi":
        await update.message.reply_text("اهلا!")
        return
    
    await update.message.reply_text("اكتب: الاسم - الرقم للتسجيل\nتقرير للاحصائيات")

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    a, n = q.data.split("_", 1)
    s = "حضر" if a == "present" else "غاب"
    d = load()
    d["attendance"].append({"student_name":n,"date":datetime.now().strftime("%Y-%m-%d"),"status":s})
    save(d)
    await q.edit_message_text(f"{n}: {s}")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))
    app.add_handler(CallbackQueryHandler(btn))
    
    print("البوت الذكي يعمل الآن...")
    app.run_polling(drop_pending_updates=True)
