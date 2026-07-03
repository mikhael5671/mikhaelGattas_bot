import json
import os
import re
import time
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import Conflict

logging.basicConfig(level=logging.INFO)
logging.getLogger("telegram").setLevel(logging.WARNING)

# ضع التوكن الخاص بك هنا
TOKEN = "8736687534:AAHU6DrhmDGBKyJQMbDmmURpUlA6Ht-DaEE"
DATA_FILE = "data.json"

def load_all():
    if os.path.exists(DATA_FILE):
        f = open(DATA_FILE, 'r', encoding='utf-8')
        data = json.load(f)
        f.close()
        return data
    return {}

def save_all(data):
    f = open(DATA_FILE, 'w', encoding='utf-8')
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.close()

def get_admin_data(cid):
    all_data = load_all()
    if cid not in all_data:
        all_data[cid] = {"students": [], "attendance": []}
        save_all(all_data)
    return all_data[cid]

def save_admin_data(cid, admin_data):
    all_data = load_all()
    all_data[cid] = admin_data
    save_all(all_data)

def what(text):
    text = text.strip()
    if "-" in text:
        p = text.split("-")
        if len(p) >= 2:
            n = p[0].strip()
            ph = p[1].strip()
            if n and any(c.isdigit() for c in ph):
                return "reg", {"name":n,"phone":ph}
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
    get_admin_data(str(update.effective_chat.id))
    await update.message.reply_text(
        "اهلا بك في بوت مدارس الاحد!\n\n"
        "تسجيل مخدوم جديد:\n"
        "اكتب: الاسم - الرقم\n"
        "مثال: ماركو - 01234567890\n\n"
        "تقرير الحضور:\n"
        "اكتب: تقرير\n\n"
        "طلب إشعار الحضور:\n"
        "اكتب: /check\n\n"
        "لمسح كل بياناتك:\n"
        "اكتب: /reset"
    )

async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    cid = str(update.effective_chat.id)
    act, val = what(text)
    admin_data = get_admin_data(cid)

    if act == "desc":
        await update.message.reply_text("بوت مدارس الاحد الذكي.\n\nالتسجيل: الاسم - الرقم\nالتقارير: تقرير")
        return

    if act == "reg":
        admin_data["students"].append({"name":val["name"],"phone":val["phone"],"active":True})
        save_admin_data(cid, admin_data)
        await update.message.reply_text(f"تم تسجيل المخدوم بنجاح!\nالاسم: {val['name']}\nالرقم: {val['phone']}")
        return

    if act == "want":
        await update.message.reply_text("اكتب: الاسم - الرقم\nمثال: ماركو - 01234567890")
        return

    if act == "ask":
        att = admin_data.get("attendance", [])
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

    await update.message.reply_text("لم افهم. جرب:\n- الاسم - الرقم\n- تقرير\n- /check")

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    a, n = q.data.split("_", 1)
    s = "حضر" if a == "present" else "غاب"
    cid = str(update.effective_chat.id)
    admin_data = get_admin_data(cid)
    admin_data["attendance"].append({"student_name":n,"date":datetime.now().strftime("%Y-%m-%d"),"status":s})
    save_admin_data(cid, admin_data)
    await q.edit_message_text(f"{n}: {s}")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.effective_chat.id)
    admin_data = get_admin_data(cid)
    students = [s for s in admin_data.get("students",[]) if s.get("active",True)]
    if not students:
        await update.message.reply_text("لا يوجد مخدومين مسجلين.")
        return
    for s in students:
        kb = [[
            InlineKeyboardButton("حضر", callback_data=f"present_{s['name']}"),
            InlineKeyboardButton("غاب", callback_data=f"absent_{s['name']}")
        ]]
        await update.message.reply_text(text=f"حضور: {s['name']}", reply_markup=InlineKeyboardMarkup(kb))

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.effective_chat.id)
    all_data = load_all()
    if cid in all_data:
        del all_data[cid]
        save_all(all_data)
    await update.message.reply_text("تم مسح جميع بياناتك وبدأ التشغيل من جديد.")

def main():
    print("البوت يعمل...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("reset", reset))
    
    # تم تعديل الفلتر هنا لمنع التداخل مع الأوامر المباشرة
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))
    app.add_handler(CallbackQueryHandler(btn))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    while True:
        try:
            main()
        except Conflict:
            print("هناك نسخة أخرى تعمل، جاري المحاولة بعد ثانيتين...")
            time.sleep(2)
        except Exception as e:
            print(f"خطأ غير متوقع: {e}")
            time.sleep(5)
