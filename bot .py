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
    WITH OPEN(DATA_FILE,'r',encoding='utf-8') as f:return jsno.load(f)
    return{"studets":(),"attendance":(),"admins":{}}
def save(d):
  with open(DATA_FILE,'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
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
  if text in ["/start","سلام","اهلا","هالو","هاي"]):return "hi",None
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
      
