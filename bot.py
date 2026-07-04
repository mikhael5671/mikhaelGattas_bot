
import json
import os
import time
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import Conflict

logging.basicConfig(level=logging.INFO)
logging.getLogger("telegram").setLevel(logging.WARNING)


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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_admin_data(str(update.effective_chat.id))
    await update.message.reply_text(
        "اهلا بك في بوت مدارس الاحد!\n\n"
        "تسجيل: اكتب الاسم فقط\n"
        "تقرير: اكتب تقرير\n"
        "حضور: /check\n"
        "مسح: /reset"
    )

async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    cid = str(update.effective_chat.id)
    admin_data = get_admin_data(cid)

    if text in ["تقرير", "احصائيات"]:
        att = admin_data.get("attendance", [])
        if not att:
            await update.message.reply_text("لا يوجد بيانات حضور.")
            return
        stats = {}
        for r in att:
            n = r.get("student_name","?")
            s = r.get("status","")
            if n not in stats:
                stats[n] = {"حضر":0,"غاب":0}
            if s in stats[n]:
                stats[n][s] += 1
        rep = "تقرير الحضور:\n\n"
        for n, s in stats.items():
            t = s["حضر"] + s["غاب"]
            p = round(s["حضر"]/t*100) if t>0 else 0
            rep += f"{n}: حضر {s['حضر']} | غاب {s['غاب']} | {p}%\n"
        await update.message.reply_text(rep)
        return

    if text in ["هاي","هالو","اهلا","سلام"]:
        await update.message.reply_text("اهلا بك!")
        return

    if text == "بتعمل ايه":
        await update.message.reply_text("بوت مدارس الاحد.\nتسجيل: اكتب الاسم\nتقرير: تقرير\nحضور: /check")
        return

    if len(text) > 1:
        admin_data["students"].append({"name":text,"active":True})
        save_admin_data(cid, admin_data)
        await update.message.reply_text(f"تم تسجيل: {text}")
        return

    await update.message.reply_text("اكتب اسم للتسجيل او تقرير للاحصائيات")

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

    if s == "غاب":
        await context.bot.send_message(chat_id=int(cid), text=f"تنبيه: {n} غاب اليوم.")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.effective_chat.id)
    admin_data = get_admin_data(cid)
    students = [s for s in admin_data.get("students",[]) if s.get("active",True)]
    if not students:
        await update.message.reply_text("لا يوجد مخدومين.")
        return
    
    await update.message.reply_text(f"عدد المخدومين: {len(students)}")
    
    for s in students:
        kb = [[
            InlineKeyboardButton("حضر", callback_data=f"present_{s['name']}"),
            InlineKeyboardButton("غاب", callback_data=f"absent_{s['name']}")
        ]]
        await update.message.reply_text(text=f"{s['name']}", reply_markup=InlineKeyboardMarkup(kb))

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.effective_chat.id)
    all_data = load_all()
    if cid in all_data:
        del all_data[cid]
        save_all(all_data)
    await update.message.reply_text("تم مسح جميع بياناتك.")

def main():
    print("شغال...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("reset", reset))
    
 
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))
    app.add_handler(CallbackQueryHandler(btn))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    while True:
        try:
            main()
        except Conflict:
            time.sleep(2)
        except Exception as e:
            print(f"خطأ: {e}")
            time.sleep(5)
