import json
import os
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# تم وضع التوكن الخاص بك هنا
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
    if "خلي الاشعار" in text or "ضبط الميعاد" in text or "غير الميعاد" in text:
        return "time", text
    if "ميعادي" in text or "الميعاد" in text:
        return "mytime", None
    if "اسجل" in text or "تسجيل" in text or "مخدوم" in text or "اضيف" in text or "جديد" in text:
        return "want", None
    if "بتعمل ايه" in text or "وظيفتك" in text or "مين انت" in text:
        return "desc", None
    if "احصائيات" in text or "تقرير" in text or "نسبة" in text or "غاب" in text or "حضر" in text:
        return "ask", text
    if text == "/start" or text == "هاي" or text == "هالو" or text == "اهلا" or text == "سلام":
        return "hi", None
    return "?", None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.effective_chat.id)
    d = load()
    if "admins" not in d: d["admins"] = {}
    if cid not in d["admins"]: d["admins"][cid] = {"day":"fri","hour":14}; save(d)
    await update.message.reply_text(
        "اهلا بك في بوت مدارس الاحد!\n\n"
        "تسجيل مخدوم جديد:\n"
        "اكتب: الاسم - الرقم\n"
        "مثال: ماركو - 01234567890\n\n"
        "تقرير الحضور:\n"
        "اكتب: تقرير\n\n"
        "ضبط ميعاد الاشعار:\n"
        "اكتب: خلي الاشعار يوم الجمعة 4\n\n"
        "معرفة الميعاد:\n"
        "اكتب: ميعادي"
    )

async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    cid = str(update.effective_chat.id)
    act, val = what(text)
    
    if act == "time":
        day = None; hour = None
        for a, e in DAYS.items():
            if a in text: day = e
        nums = re.findall(r'\d+', text)
        if nums:
            h = int(nums[0])
            if 0 <= h <= 23: hour = h
        d = load()
        if "admins" not in d: d["admins"] = {}
        if cid not in d["admins"]: d["admins"][cid] = {"day":"fri","hour":14}
        if day: d["admins"][cid]["day"] = day
        if hour is not None: d["admins"][cid]["hour"] = hour
        save(d)
        rev = {v:k for k,v in DAYS.items()}
        cd = rev.get(d["admins"][cid]["day"], "الجمعة")
        ch = d["admins"][cid]["hour"]
        await update.message.reply_text(f"تم ضبط الاشعار!\nاليوم: {cd}\nالساعة: {ch}:00")
        return
    
    if act == "mytime":
        d = load()
        a = d.get("admins",{}).get(cid, {"day":"fri","hour":14})
        rev = {v:k for k,v in DAYS.items()}
        cd = rev.get(a["day"], "الجمعة")
        await update.message.reply_text(f"الميعاد الحالي:\nاليوم: {cd}\nالساعة: {a['hour']}:00")
        return
    
    if act == "desc":
        await update.message.reply_text("بوت مدارس الاحد الذكي.\n\nالتسجيل: الاسم - الرقم\nالتقارير: تقرير\nضبط الاشعار: خلي الاشعار يوم الجمعة 4")
        return
    
    if act == "reg":
        d = load()
        d["students"].append({"name":val["name"],"phone":val["phone"],"active":True})
        save(d)
        await update.message.reply_text(f"تم تسجيل المخدوم بنجاح!\nالاسم: {val['name']}\nالرقم: {val['phone']}")
        return
    
    if act == "want":
        await update.message.reply_text("اكتب: الاسم - الرقم\nمثال: ماركو - 01234567890")
        return
    
    if act == "ask":
        d = load()
        att = d.get("attendance", [])
        if not att: await update.message.reply_text("لا يوجد بيانات حضور."); return
        stats = {}
        for r in att:
            n = r.get("student_name","?"); s = r.get("status","")
            if n not in stats: stats[n] = {"حضر":0,"غاب":0}
            if s in stats[n]: stats[n][s] += 1
        rep = "تقرير الحضور:\n\n"
        for n, s in stats.items():
            t = s["حضر"] + s["غاب"]
            p = round(s["حضر"]/t*100) if t>0 else 0
            rep += f"{n}: حضر {s['حضر']} | غاب {s['غاب']} | {p}%\n"
        await update.message.reply_text(rep)
        return
    
    if act == "hi":
        await update.message.reply_text("اهلا بك!")
        return
    
    await update.message.reply_text("لم افهم. جرب:\n- الاسم - الرقم\n- تقرير\n- خلي الاشعار يوم الجمعة 4")

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    a, n = q.data.split("_", 1)
    s = "حضر" if a == "present" else "غاب"
    d = load()
    d["attendance"].append({"student_name":n,"date":datetime.now().strftime("%Y-%m-%d"),"status":s})
    save(d)
    e = "حضر" if a == "present" else "غاب"
    await q.edit_message_text(f"{n}: {e}")

async def weekly(context: ContextTypes.DEFAULT_TYPE):
    d = load()
    students = [s for s in d.get("students",[]) if s.get("active",True)]
    if not students: return
    now = datetime.now()
    today_eng = now.strftime("%a").lower()[:3]
    hour_now = now.hour
    for cid, admin_data in d.get("admins",{}).items():
        if admin_data.get("day","fri") == today_eng and admin_data.get("hour",14) == hour_now:
            for s in students:
                kb = [[InlineKeyboardButton("حضر", callback_data=f"present_{s['name']}"),
                       InlineKeyboardButton("غاب", callback_data=f"absent_{s['name']}")]]
                try:
                    await context.bot.send_message(chat_id=int(cid), text=f"حضور: {s['name']}", reply_markup=InlineKeyboardMarkup(kb))
                except: pass

def main():
    print("تشغيل...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))
    app.add_handler(CallbackQueryHandler(btn))
    
    from datetime import timezone
    sch = AsyncIOScheduler(timezone=timezone.utc)
    
    # تم تعديل هذا السطر لتمرير الـ context المناسب للوظيفة تلقائياً
    sch.add_job(weekly, 'cron', minute=0, kwargs={'context': ContextTypes.DEFAULT_TYPE(app)})
    sch.start()
    
    print("شغال!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
