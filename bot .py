import json,os,re
from datetime import datetime
from telegram import update,lnlineKeyboardButtom,lnlineKeyboardMarkup
from telegram.ext import Application,CommandHandler,MessageHandler,CallbackQueryHandeler,filters,ContextTypes
from apscheduler.schedulers.asyncio import AsynclOScheduler
TELEGRAM_TOKEN = "8736687534:AAEeV3-HTFweul4-mFboAvl157YRlqjm4KA"
DATA_FILE = "data.json"
DAYS ={"السبت":"sat","الاحد":"sun","الاثنين":"mon","الثلاثاء":"tue","الاربعاء":"wed","الخميس":"thu","الجمعة":"fri"}
def load():
  if os.path.exists(DATA_FILE):
      f= open(DATA_FILE,'r',encoding='utf-8')
      data=json.load(f)
      f.close()
      return data
  return{"studets":[],"attendance":[],"admins":{}}
def save(d):
  f= open(DATA_FILE,'w',encoding='utf-8') 
  json.dump(d,f,ensure_ascii=False,indent=2)
  f.close()
def what(text):
  text=text.strip()
  if "-" in text or "-" in text:
    p=text.replace("-","-").split("-")
    if len(p)>=2:
      n,ph=p[0].strip(),p[1].strip()
      if n and any(c.isdigit() for c in ph):return"reg",{"name":n,"phone":ph}
  if any(w in text for w in ["ضبط","خلي الاشعار","ظبط","غير المعاد","المعاد"]):return "time",text
  if any(w in text for w in ["ميعادي","الميعاد"]): return "mytime",None
  if any(w in text for w in ["جديد","اضيف","مخدوم","تسجيل","اسجل"]):return "want",None
  if any(w in text for w in ["مين انت","وظيفتك","انت بتعمل ايه"]):return "desc",None
  if any(w in text for w in ["حضر","غاب","نسبة","تقرير","احصائيات"]):return "ask",text
  if text.startswith("/start") or text.startswith("start"): return "hi",None
  return"?",None
async def hi(update:Update,context:ContextTypes.DEFAULT_TYPE):
  cid=str(update.effective_chat.id)
  d=load()
  if "admins" not in d: d["admins"]={}
  if cid not in d["admins"]: d["admins"][cid]={"day":"fri","hour":14};save(d)
  await update.message.reply_text("اهلا\n\nالرقم-الاسم:تسجيل\nاحصائيات:تقرير\nخلي الاشعار يوم الجمعة:ضبط4\nميعادي:معرفة الميعاد")
  async def msg(update:Update,context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    cid=str(update.effective_chat.id)
    act,val=what(text)
    if act=="time":
      day,hour=None,None
      for a,e in DAYS.items():
        if a in text: day=e
      nums=re.findall(r'\d+',text)
      if nums:
        h=int(nums[0])
        if 0<=h<=23: hour=h
      d=load()
      if "admins" not in d: d["admins"]={}
      if cid not in d["admins"]:d["admins"][cid]={"day":"fri","hour":14}
      if day:d["admins"][cid]["day"]=day
      if hour is not None:d["admins"][cid]["hour"]=hour
      save(d)
      rev={v:k for k,v in DAYS.items()}
      cd=rev.get(d["admins"][cid]["day"],"الجمعة")
      ch=d["admins"][cid]["hour"]
      await update.message.reply_text(f"تم!\n{cd}\n{ch}:00")
      return
    if act=="mytime":
      d=load()
      a=d.get("admins",{}).get(cid,{"day":"fri","hour":!4})
      rev={v:k for k,v in DAYS.items()}
      cd=rev.get(a["day"],"الجمعة")
      await update.message.reply_text(f"الميعاد:\n{cd}\n{a['hour']}:00")
      return
      if act=="desc":  
          await update.message.reply_text(" بوت مدارس الأحد الذكي.\n\n تسجيل: الاسم - الرقم\n تقرير: إحصائيات\n ضبط: خلي الإشعار يوم الأحد 4\n واتساب للغايبين") 
          return    
      if act=="reg":
          d=load()
          d["students"].append({"name":val["name"],"phone":val["phone"],"active":True})
          save(d) 
          await update.message.reply_text(f" تم!\n {val['name']}\n📱 {val['phone']}") 
          return
      if act=="want":
          await update.message.reply_text(" اكتب: الاسم - الرقم\nمثال: ماركو - 01234567890") 
          return
      if act=="ask":
          d=load()
          att=d.get("attendance",[]) 
          if not att: await update.message.reply_text(" مفيش بيانات."); return
          stats={}
          for r in att:
              n,s=r.get("student_name","?"),r.get("status","") 
              if n not in stats: stats[n]={"حضر":0,"غاب":0}
              if s in stats[n]: stats[n][s]+=1 
          rep=" تقرير:\n\n" 
          for n,s in stats.items():
              t=s["حضر"]+s["غاب"]
              p=round(s["حضر"]/t*100) if t>0 else 0   
              rep+=f" {n}: حضر {s['حضر']} | غاب {s['غاب']} | {p}%\n"
          await update.message.reply_text(rep)
          return
      if act=="hi":  
          await update.message.reply_text(" أهلاً!\n تسجيل: الاسم - الرقم\n تقرير: إحصائيات") 
          return
      await update.message.reply_text(" مش فاهم.\n• الاسم - الرقم\n• تقرير\n• خلي الإشعار يوم الجمعة 4")
    async def btn(update:Update,context:ContextTypes.DEFAULT_TYPE):
        q=update.callback_query
        await q.answer()
        a,n=q.data.split("_",1)
        s="حضر" if a=="present" else "غاب" 
        d=load()
        d["attendance"].append({"student_name":n,"date":datetime.now().strftime("%Y-%m-%d"),"status":s})
        save(d)
        e="" if a=="present" else "" 
        await q.edit_message_text(f"{e} {n}: {s}")
    async def weekly(context:ContextTypes.DEFAULT_TYPE): 
        d=load()
        students=[s for s in d.get("students",[]) if s.get("active",True)]  
        if not students: return
        now=datetime.now() 
        today_eng=now.strftime("%a").lower()[:3]
        hour_now=now.hour
        admins=d.get("admins",{})
        for cid,admin_data in admins.items():
            admin_day=admin_data.get("day","fri")
            admin_hour=admin_data.get("hour",14)
            if today_eng==admin_day and hour_now==admin_hour:
                for s in students:
                    kb=[[
                      InlineKeyboardButton(" حضر",callback_data=f"present_{s['name']}"),
                      InlineKeyboardButton(" غاب",callback_data=f"absent_{s['name']}")
                    ]]  
                    try:
                        await context.bot.send_message(chat_id=int(cid),text=f" {s['name']}",reply_markup=InlineKeyboardMarkup(kb))
                    except:
                        pass
    def main():
        print(" تشغيل...")
        app=Application.builder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start",hi))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,msg))  
        app.add_handler(CallbackQueryHandler(btn))
        sch=AsyncIOScheduler() 
        sch.add_job(weekly,'cron',minute=0)
        sch.start()
        print(" شغال!")
        app.run_polling()
    if __name__=="__main__":     main()
