from flask import Flask, render_template, flash, request, redirect, session, url_for, abort, g
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_login import login_user , logout_user , current_user , login_required

import os, sys
import requests
import json
import array
import math
import time


from datetime import datetime

from iexfinance.stocks import Stock


from flask_wtf import Form
from wtforms import StringField, BooleanField, FloatField, IntegerField
from wtforms.validators import DataRequired

from operator import itemgetter
from operator import attrgetter

app = Flask(__name__)
app.config.from_object('settings')

def format_datetime(value, format="%B %d %Y %I:%M %p"):
    """Format a date time to (Default): Month d YYYY HH:MM P"""
    if value is None:
        return ""
    return value.strftime(format)

app.jinja_env.filters['datetime'] = format_datetime

db = SQLAlchemy(app)
Bootstrap(app)

# LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Models

class strikes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idtext = db.Column(db.String(26), index=True)
    symbol = db.Column(db.String(12), index=True)
    putorcall = db.Column(db.String(1), index=True)
    expirationdate = db.Column(db.String(11), index=True)
    strike = db.Column(db.Float, index=True)
    premium = db.Column(db.Float)
    volume = db.Column(db.Float)
    numdays = db.Column(db.Integer)
    updatedon = db.Column(db.DateTime)
    oai = db.Column(db.String(1))  #Out of the Money / At the Money / In The Money
    oi = db.Column(db.Float) # Open Interest
    opti = db.Column(db.Float) #OPTI

    _mapper_args__ = {"order_by":symbol}

    def __init__(self, symbol,putorcall,expirationdate,strike,premium,volume,numdays,idtext, oi, opti, oai):
        self.symbol = symbol
        self.putorcall = putorcall
        self.strike = strike
        self.expirationdate = expirationdate
        self.premium = premium
        self.volume = volume
        self.numdays = numdays
        self.updatedon = datetime.utcnow()
        self.idtext = idtext
        self.oi = oi
        self.opti = opti
        self.oai = oai

    def __repr__(self):
        return "<strikes(symbol='%s', putorcall='%s', expirationdate='%s',numdays='%i', strike='%f', premium='%f')>" % (self.symbol,self.putorcall,self.expirationdate,self.numdays,self.strike,self.premium)

    def as_dict(self):
        return {c.symbol: getattr(self,c.symbol) for c in self.__table__.columns}

class Crypto(db.Model):
    __tablename__ = "Crypto"
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(7), unique=True)
    qty = db.Column(db.Integer)
    price = db.Column(db.Float)
    addyto = db.Column(db.String(50))
    addyfrom = db.Column(db.String(50))
    yieldcalc = db.Column(db.Float)
    _mapper_args__ = {"order_by":symbol}
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))

    def __init__(self, symbol, userid):
        self.symbol = symbol
        self.addyto = "NONE"
        self.addyfrom = "NONE"
        self.user_id = userid
        self.qty = 0
        yieldcalc = 0
        self.price = 0

    def __repr__(self):
        return '<Symbol %r>' % self.crsymbol

class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class SymbolForm(Form):
    symbolenter = StringField('Symbol', validators=[DataRequired()])

class RankingForm(Form):
    rankenter = FloatField('Ranking', validators=[DataRequired()])

class Ticker(db.Model):
    __tablename__ = "Ticker"
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(7), index=True)
    notes = db.Column(db.String(250))
    category = db.Column(db.String(30), index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    _mapper_args__ = {"order_by":symbol}
    nextearnings = db.Column(db.String(11), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    priceobj = db.Column(db.Float)
    earnsurprise = db.Column(db.Float)
    tprice = db.Column(db.Float)
    tvol = db.Column(db.Float)
    tdesc = db.Column(db.String(50))
    ttype = db.Column(db.String(30))

    def __init__(self, symbol, tprice, user_id, tvol, tdesc, ttype,):
        self.symbol = symbol
        self.timestamp = datetime.utcnow()
        self.notes = "None"
        self.category = "None"
        self.user_id = user_id
        self.nextearnings = "No Data"
        self.tprice = tprice
        self.priceobj = 0
        self.earnsurpise = 0.0
        self.tdesc = tdesc
        self.ttype = ttype
        self.tvol = tvol

    def __repr__(self):
        return '<Symbol %r>' % self.symbol


class Trade(db.Model):
    __tablename__ = "Trade"
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(12), index=True)
    putorcall = db.Column(db.String(1), index=True)
    note = db.Column(db.String(20))
    strat = db.Column(db.Integer, index=True)
    expirationdate = db.Column(db.String(11), index=True)
    strike1 = db.Column(db.Float)
    strike2 = db.Column(db.Float)
    initprem = db.Column(db.Float)
    initnumdays = db.Column(db.Integer)
    daysleft = db.Column(db.Integer)
    currprem = db.Column(db.Float)
    premclosed = db.Column(db.Float)
    premcap = db.Column(db.Float)
    status = db.Column(db.Integer)
    initqty = db.Column(db.Integer)
    ror = db.Column(db.Float)
    otm = db.Column(db.Float)
    opti = db.Column(db.Float) #OPTI
    _mapper_args__ = {"order_by":symbol}
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))

    def __init__(self, symbol,putorcall,expirationdate,strike1,strike2,initprem, numdays, opti, strat, ror, user_id):
        self.note = "initiated"
        self.symbol = symbol
        self.putorcall = putorcall
        self.ror = ror
        self.otm = 0
        self.premclosed = 0
        self.premcap = 0
        self.strike1 = strike1
        self.strike2 = strike2
        self.expirationdate = expirationdate
        self.initprem = initprem
        self.currprem = initprem
        self.initnumdays = numdays
        self.initqty = 1
        self.strat = strat
        self.daysleft = numdays
        self.status = 1
        self.user_id = user_id
        self.opti = opti

        def __repr__(self):
            return '<Symbol %r>' % self.symbol


class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer , primary_key=True)
    username = db.Column(db.String(15), unique=True , index=True)
    password = db.Column(db.String(15))
    email = db.Column(db.String(50),unique=True , index=True)
    registered_on = db.Column(db.DateTime)
    accesslevel = db.Column(db.Integer)
    statuscode = db.Column(db.Integer)
    invitedby = db.Column(db.String(15))
    totaltrades = db.Column(db.Integer)
    opentrades = db.Column(db.Integer)
    ranking = db.Column(db.Integer)
    tickers = db.relationship('Ticker', backref='user', lazy='dynamic')
    trades = db.relationship('Trade', backref='user', lazy='dynamic')
    cryptos = db.relationship('Crypto', backref='user', lazy='dynamic')

    def __init__(self , username ,password , email, invitedby, tickers = [], trades = []):
        self.username = username
        self.password = password
        self.email = email
        self.invitedby =  invitedby
        self.registered_on = datetime.utcnow()
        self.accesslevel = 0
        self.statuscode = 0
        self.totaltrades = 0
        self.opentrades = 0
        self.ranking = 0
        self.tickers = tickers
        self.trades = trades

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_admin(self):
        if self.id == 1:
            g.user.is_admin = True
            return True
        else:
            if self.accesslevel > 200:
                return True
            else:
                 return False

    def get_id(self):
        return str(self.id)

    def is_founder(self):
        if self.id == 1:
            return True
        else:
            return False

    def __repr__(self):
        return '<User %r>' % (self.username)
#

db.create_all()
db.session.commit()

class CSPR(object):
    def __init__(self,LSym,LPrice,LExp,LDays,LStrike,LPrem,LROR,LCost):
        self.LSym = LSym
        self.LPrice = LPrice
        self.LExp = LExp
        self.LDays = LDays
        self.LStrike = LStrike
        self.LPrem = LPrem
        self.LROR = LROR
        self.LCost = LCost

# Config info for Tradier
baseurl = "https://sandbox.tradier.com/v1/"
authy = app.config['MYAUTHY']

# Config info for Intrinio
intuser = app.config['IAUTHUSER']
intpass = app.config['IAUTHPASS']

# LOGIN MANAGER ROUTES

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/register' , methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    # user = User(request.form['username'] , request.form['password'],request.form['email'])
    #user = User(request.form['username'].capitalize() , request.form['password'],request.form['email'])
    username = request.form['username']
    username = username.lower()
    userpass = request.form['password']
    useremail = request.form['email']
    usermail = useremail.lower()
    # username = username.capitalize()
    user = User(username=username,password=userpass,email=useremail,invitedby="OPENCALCADD")
    reqkeyget = request.form['regkey']
    # username.capitalize() - need to capitalize username
    if reqkeyget == app.config['REGKEY']:
        db.session.add(user)
        db.session.commit()
        flash('User successfully registered')
        return redirect(url_for('login'))
    else:
        flash('Incorrect Registration Key')
        return redirect(url_for('index'))

#@app.route('/admin' , methods=['GET','POST'])
@app.route('/admin')
@login_required
def admin():

   if g.user.is_admin:
        return render_template('admin.html', tickers = Ticker.query.order_by(Ticker.symbol).all(), users = User.query.all() )
   else:
        return redirect(url_for('index'))

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    username = username.lower()
    password = request.form['password']
    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True
    registered_user = User.query.filter_by(username=username,password=password).first()
    if registered_user is None:
        flash('Username or Password is invalid' , 'error')
        return redirect(url_for('login'))
    login_user(registered_user, remember = remember_me)
    username = str(registered_user.username)
    username = username.capitalize()
    admintag = " "
    if registered_user.is_admin():
        g.user.is_admin = True
        admintag = " ADMIN "
    else:
        g.user_is_admin = False
    if registered_user.is_founder():
        founder = " SUPER "
    else:
        founder = ""
    welcomemsg = "Welcome " + username + "!" + " (User # " + str(g.user.id) + ")" + founder + admintag
    flash(welcomemsg)
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
#

@app.route("/", methods=['POST', 'GET'])
def index():
   if request.method == 'POST':
      return render_template("index.html")
   else:
      return render_template("index.html")

@app.route('/posit', methods=['POST', 'GET'])
@login_required
def posit():
   form = SymbolForm()

   if form.validate_on_submit():
      currsym = form.symbolenter.data
      currsym = format(currsym)
      return redirect(url_for('getquotes',sym=currsym))
   return render_template('posit.html', tickers = Ticker.query.order_by(Ticker.symbol).filter_by(user_id=g.user.id), form=form )

# UPDATE RANK
@app.route('/updaterank/<sym>&<rank>')
@login_required
def updaterank(sym,rank):
    currsym = format(sym)
    currsym = currsym.upper()
    db.session.query(Ticker.id).filter_by(symbol=currsym).update({"earnsurprise": rank})
    db.session.commit()
    newmsg = "Updated " + currsym + " to rank of " + format(rank)
    flash('%s' % newmsg)
    return redirect(url_for('stocknotes',sym=currsym))

# NOTES
@app.route('/stocknotes/<sym>', methods=['POST', 'GET'])
@login_required
def stocknotes(sym):
   form = RankingForm()
   currsym = format(sym)
   currsym = currsym.upper()

   if form.validate_on_submit():
      rank = form.rankenter.data
      return redirect(url_for('updaterank',sym=currsym,rank=rank))

   return render_template('stocknotes.html', form=form, ticker = Ticker.query.filter_by(symbol=currsym).filter_by(user_id=g.user.id).scalar())
  # return render_template('stocknotes.html', ticker = Ticker.query.filter_by(symbol=currsym).filter_by(user_id=g.user.id).scalar())

@app.route('/info/<sym>')
@login_required
def infocalc(sym):
   currsym = format(sym)
   currsym = currsym.upper()
   form = SymbolForm()
   IEX_TOKEN = app.config['IEX_TOKEN']
   stockdata = Stock(currsym, token=IEX_TOKEN)
   data2=stockdata.get_key_stats()
   data4=stockdata.get_price_target()
  # week52high=data2["week52high"]
  # week52low=data2["week52low"]
 #  day200MovingAvg=data2["day200MovingAvg"]
 #  day50MovingAvg=data2["day50MovingAvg"]
 #  ttmDividendRate=data2["ttmDividendRate"]
  # ytdChangePercent=data2["ytdChangePercent"]
 #  nextDividendDate=data2["nextDividendDate"]
 #  dividendYield=data2["dividendYield"]
 #  nextEarningsDate=data2["nextEarningsDate"]
 #  exDividendDate=data2["exDividendDate"]
#   beta=data2["beta"]
 #  peRatio=data2["peRatio"]
 #  priceTargetAverage = data4["priceTargetAverage"]
#   priceTargetHigh = data4["priceTargetHigh"]
#   priceTargetLow = data4["priceTargetLow"]
 #  numberOfAnalysts = data4["numberOfAnalysts"]
#


   if form.validate_on_submit():
      currsym = form.symbolenter.data
      currsym = format(currsym)
      return redirect(url_for('infocalc',sym=currsym))
   return render_template('info.html', currsym=currsym,data2=data2,data4=data4, form=form )

@app.route('/del/<sym>')
@login_required
def delquote(sym):
   currsym = format(sym)
   currsym = currsym.upper()
   exists = db.session.query(Ticker.id).filter_by(symbol=currsym).filter_by(user_id=g.user.id).scalar() is not None
   if exists:
      db.session.query(Ticker.id).filter_by(symbol=currsym).filter_by(user_id=g.user.id).delete()
      db.session.query(strikes).filter(strikes.symbol==currsym).delete()
      db.session.commit()
      flash('%s removed' % sym)
      return redirect(url_for('posit'))

   flash('error - unabled to process request')
   return redirect(url_for('posit'))

@app.route('/q/<sym>')
@login_required
def getquotes(sym):
   urlhome = "<a href=" + url_for('posit') + "><img src='http://www.clker.com/cliparts/b/4/b/S/d/t/square-back-text-black-md.png' width='75' height='75'></a></br>"
   currsym = format(sym)


   url = baseurl + "markets/quotes?symbols=" + currsym
   headers = {"Accept":"application/json",
           "Authorization": authy}
   resp = requests.get(url, headers=headers)
   status = resp.status_code
   data = resp.json()
   testy = data["quotes"]["quote"]
   getvol = data["quotes"]["quote"]["volume"]
   getsym = data["quotes"]["quote"]["symbol"]
   getdesc = data["quotes"]["quote"]["description"]
   getlast = data["quotes"]["quote"]["last"]
   gettype = data["quotes"]["quote"]["type"]
   testz = "Symbol: " + str(getsym) + " Description: " + str(getdesc) + " Last Price: " + str(getlast) + " Volume: " + str(getvol) + " Type: " + str(gettype)
   ticker = getsym.upper()
   uid = g.user.id
   exists = db.session.query(Ticker.id).filter_by(symbol=ticker).filter_by(user_id=g.user.id).scalar() is not None
   if not exists:
      flash('%s' % testz)
      newticker = Ticker(symbol=ticker, user_id=uid, tprice=getlast, tvol = getvol, tdesc = getdesc, ttype = gettype)
      db.session.add(newticker)
      db.session.commit()
      return redirect(url_for('posit'))
   testz = "Already added"
   flash('%s' % testz)
   return redirect(url_for('posit'))

# Get Expiration Dates MANUAL - STRIKES
@app.route('/e/<sym>')
@login_required
def getoptex(sym):
   url = baseurl + "markets/options/expirations?symbol=" + format(sym)
   headers = {"Accept":"application/json",
           "Authorization": authy}
   resp = requests.get(url, headers=headers)
   currsym = format(sym)
   data = resp.json()
   allexps = data["expirations"]["date"]
   sdate = []

   for expdate in allexps:
       #testthis = {"strike":strike["strike"],"mid":mid, "ror":ror, "otm":otm, "opti":opti}
       newone = {"date":expdate}
       sdate.append(newone)
   return render_template('expdates.html', edates = sdate, symbol=currsym)

# TRADE - ADD NEW POSITION
@app.route('/tradeadd/<sym>&<putorcall>&<exp>&<strike1>&<strike2>&<initprem>&<numdays>&<opti>&<strat>&<ror>')
@login_required
def tradeadd(sym,putorcall,exp,strike1,strike2,initprem,numdays,opti,strat,ror):

    sym = sym.upper()
    uid = g.user.id
    newtrade = Trade(symbol = sym,putorcall=putorcall,expirationdate=exp,strike1=strike1,strike2=strike2,initprem=initprem, numdays=numdays, opti=opti, strat=strat, ror=ror, user_id=uid)
    db.session.add(newtrade)
    db.session.commit()
    notice = "Trade Added"
    flash('%s' % notice)
    return render_template('trades.html', trades = Trade.query.order_by(Trade.premcap).filter_by(user_id=g.user.id).filter_by(status=1))

@app.route('/tradeview')
@login_required
def tradeview():
    return render_template('trades.html', viewtype = "TRADES", trades = Trade.query.order_by(Trade.premcap).filter_by(user_id=g.user.id).filter_by(status=1))

@app.route('/tradearch')
@login_required
def tradearch():
    return render_template('trades.html', viewtype = "ARCHIVES", trades = Trade.query.order_by(Trade.premcap).filter_by(user_id=g.user.id).filter_by(status=2))

@app.route('/tradedel/<tradeid>')
def tradedel(tradeid):
    db.session.query(Trade.id).filter_by(id=tradeid).delete()
    db.session.commit()
    flash('Removed')
    return render_template('trades.html', viewtype = "TRADES", trades = Trade.query.order_by(Trade.premcap).filter_by(user_id=g.user.id).filter_by(status=1))

@app.route('/trademod/<tradeid>')
def trademod(tradeid):
    db.session.query(Trade.id).filter_by(id=tradeid).update({"status": 2})
    db.session.commit()
    return render_template('trades.html', viewtype = "TRADES", trades = Trade.query.order_by(Trade.premcap).filter_by(user_id=g.user.id).filter_by(status=1))

@app.route('/traderefresh')
def traderefresh():
    trades = Trade.query.filter_by(user_id=g.user.id).filter_by(status=1)
    for trade in trades:

        tradetickupdate(trade.symbol)
        ticker = db.session.query(Ticker.tprice).filter_by(symbol=trade.symbol).first()
        currprice = ticker.tprice
        expdate = trade.expirationdate
        updatestrikes(trade.symbol)
        # calculate new # of days
        datety = time.strftime("%Y-%m-%d")
        datetoday = datetime.strptime(datety,'%Y-%m-%d').date()
        dateexp = datetime.strptime(format(expdate),'%Y-%m-%d').date()
        numdays = (dateexp - datetoday).days

# REFRESH TRACKING STATS
        if trade.strat == 1:     # cash-secured puts
            strike1info = strikes.query.filter_by(symbol=trade.symbol).filter_by(putorcall=trade.putorcall).filter_by(expirationdate=trade.expirationdate).filter_by(strike=trade.strike1).first()
            newprem = strike1info.premium
            targetstrike = strike1info.strike
            if targetstrike == currprice:
                otm = 0
            else:
                otm = ((currprice - targetstrike) / currprice) * 100
            initprem = trade.initprem
            premcap = (initprem - newprem) / initprem
            premcap = round(round(premcap / 0.05) * 0.05, -int(math.floor(math.log10(0.05))))
            premcap = premcap * 100
            db.session.query(Trade.id).filter_by(id=trade.id).update({"daysleft": numdays})
            db.session.query(Trade.id).filter_by(id=trade.id).update({"premcap": premcap})
            db.session.query(Trade.id).filter_by(id=trade.id).update({"currprem": newprem})
            db.session.query(Trade.id).filter_by(id=trade.id).update({"otm": otm})
        elif trade.strat == 2:    # put-spreads
            strike1info = strikes.query.filter_by(symbol=trade.symbol).filter_by(putorcall=trade.putorcall).filter_by(expirationdate=trade.expirationdate).filter_by(strike=trade.strike1).first()
            strike2info = strikes.query.filter_by(symbol=trade.symbol).filter_by(putorcall=trade.putorcall).filter_by(expirationdate=trade.expirationdate).filter_by(strike=trade.strike2).first()

            strikeshort = strike1info.premium
            strikelong = strike2info.premium
            newprem = (strikeshort - strikelong)
            initprem = trade.initprem
            premcap = (initprem - newprem) / initprem
            premcap = round(round(premcap / 0.05) * 0.05, -int(math.floor(math.log10(0.05))))
            premcap = premcap * 100
            targetstrike = strike1info.strike
            if targetstrike == currprice:
                otm = 0
            else:
                otm = ((currprice - targetstrike) / currprice) * 100
            db.session.query(Trade.id).filter_by(id=trade.id).update({"currprem": newprem})
            db.session.query(Trade.id).filter_by(id=trade.id).update({"daysleft": numdays})
            db.session.query(Trade.id).filter_by(id=trade.id).update({"premcap": premcap})
            db.session.query(Trade.id).filter_by(id=trade.id).update({"otm": otm})
    db.session.commit()
    return render_template('trades.html', viewtype = "TRADES", trades = Trade.query.order_by(Trade.premcap).filter_by(user_id=g.user.id).filter_by(status=1))

    # strikeitems = strikes.query.filter_by(symbol=symbol)
    #

@app.route('/tradetickupdate/<sym>')
@login_required
def tradetickupdate(sym):
   refsymbol = format(sym)
   sym = sym.upper()
   uid = g.user.id
   headers = {"Accept":"application/json",
           "Authorization": authy}
   url2 = baseurl + "markets/quotes?symbols=" + refsymbol
   # Get Stock Data
   resp2 = requests.get(url2, headers=headers)
   data2 = resp2.json()
   getvol = data2["quotes"]["quote"]["volume"]
   getsym = data2["quotes"]["quote"]["symbol"]
   getdesc = data2["quotes"]["quote"]["description"]
   currprice = data2["quotes"]["quote"]["last"]
   gettype = data2["quotes"]["quote"]["type"]
   #
   if (gettype == "stock"):
     IEX_TOKEN = app.config['IEX_TOKEN']
     stockdata = Stock(sym, token=IEX_TOKEN)
     data2=stockdata.get_key_stats()
     data4=stockdata.get_price_target()
   # week52high=data2["week52high"]
   # week52low=data2["week52low"]
   #  day200MovingAvg=data2["day200MovingAvg"]
   #  day50MovingAvg=data2["day50MovingAvg"]
   #  ttmDividendRate=data2["ttmDividendRate"]
   # ytdChangePercent=data2["ytdChangePercent"]
   #  nextDividendDate=data2["nextDividendDate"]
   #  dividendYield=data2["dividendYield"]
   #  exDividendDate=data2["exDividendDate"]
   #   beta=data2["beta"]
   #  peRatio=data2["peRatio"]

  # week52high=data2["week52high"]
  # week52low=data2["week52low"]
 #  day200MovingAvg=data2["day200MovingAvg"]
 #  day50MovingAvg=data2["day50MovingAvg"]
 #  ttmDividendRate=data2["ttmDividendRate"]
  # ytdChangePercent=data2["ytdChangePercent"]
 #  nextDividendDate=data2["nextDividendDate"]
 #  dividendYield=data2["dividendYield"]
 #  nextEarningsDate=data2["nextEarningsDate"]
 #  exDividendDate=data2["exDividendDate"]
#   beta=data2["beta"]
 #  peRatio=data2["peRatio"]
 #  priceTargetAverage =
#   priceTargetHigh = data4["priceTargetHigh"]
#   priceTargetLow = data4["priceTargetLow"]
 #  numberOfAnalysts = data4["numberOfAnalysts"]
   #addnotes = "High:" + format(truncate(data2["week52high"]),1) + " Low: " + format(data2["week52low"])
   addnotes = " 200 DMA is $" + format(data2["day200MovingAvg"])
   addnextearnings = format(data2["nextEarningsDate"])
   addnotes += " and P/E:" + format(data2["peRatio"])
   addpricetarget =  data4["priceTargetAverage"]
   #
   db.session.query(Ticker.id).filter_by(symbol=refsymbol).update({"tprice": currprice})
   db.session.query(Ticker.id).filter_by(symbol=refsymbol).update({"tvol": getvol})
   db.session.query(Ticker.id).filter_by(symbol=refsymbol).update({"category": gettype})
   if (gettype == "stock"):

     db.session.query(Ticker.id).filter_by(symbol=refsymbol).update({"nextearnings": addnextearnings})
     db.session.query(Ticker.id).filter_by(symbol=refsymbol).update({"priceobj": addpricetarget})
     db.session.query(Ticker.id).filter_by(symbol=refsymbol).update({"notes": addnotes})
   db.session.commit()
   return

@app.route('/updatestrikes/<sym>')
@login_required
def updatestrikes(sym):
    currsym = format(sym)
    # opti multiplier to increase shorter term puts
    optimult = 1
    #Delete previous strike records
    #
    db.session.query(strikes).filter(strikes.symbol==currsym).delete()
    db.session.commit()
    #
    datety = time.strftime("%Y-%m-%d")
    datetoday = datetime.strptime(datety,'%Y-%m-%d').date()
    headers = {"Accept":"application/json","Authorization": authy}

    urlsymbol = baseurl + "markets/quotes?symbols=" + currsym
    # Get Stock Data
    resp2 = requests.get(urlsymbol, headers=headers)
    data2 = resp2.json()
    currprice = data2["quotes"]["quote"]["last"]
    roundedprice = round(round(currprice / 0.05) * 0.05, -int(math.floor(math.log10(0.05))))
    tradetickupdate(currsym)
    # End of Stock Data


    # Get Expiration Dates
    url = baseurl + "markets/options/expirations?symbol=" + currsym
    resp = requests.get(url, headers=headers)
    data = resp.json()
    allexps = data["expirations"]["date"]
    # End of Expiration Dates

    # Symbol with all Expiration Dates loop
    for expdate in allexps:
        # For Each Expiration Date - pull data
        currexpdate = format(expdate)
        # expiration -> currexpdate
        dateexp = datetime.strptime(format(expdate),'%Y-%m-%d').date()
        numdays = (dateexp - datetoday).days


        if (13 < numdays < 61):
            # number of days -> numdays
            if numdays < 30:
               timemult = numdays / 30
            else:
               timemult = 30 / numdays
               optimult = 1
            url = baseurl + "markets/options/chains?symbol=" + currsym + "&expiration=" + currexpdate
            resp = requests.get(url, headers=headers)
            data = resp.json()
            allopts = data["options"]["option"]
            # For Each Strike for the expiration date
            for strike in allopts:
                asksize = strike["asksize"]
                bidsize = strike["bidsize"]
                oi = strike["open_interest"]
                # update later to get real volume
                currvolume = strike["average_volume"]
                if (((asksize * bidsize) > 1) & (oi > 1)):
                    currstrike = format(strike["strike"])
                    mid = (strike["bid"] + strike["ask"])/2
                    mid = round(round(mid / 0.05) * 0.05, -int(math.floor(math.log10(0.05))))
                    mid = round(mid,2)
                    # premium -> mid
                    currpremium = format(mid)
                    if (mid > 0):
                        if strike["option_type"] == "put":
                            # Put Option
                            putorcall = "P"
                            if (roundedprice * 0.80 <= round(strike["strike"],2) <= roundedprice*1.05):
                               oai = "O"
                               ror = ((mid / strike["strike"]) * 100) * timemult
                               ror = round(round(ror / 0.01) * 0.01, -int(math.floor(math.log10(0.01))))
                               otm = ((currprice - strike["strike"]) / currprice) * 100
                               otm = round(round(otm / 0.01) * 0.01, -int(math.floor(math.log10(0.01))))
                               opti = (otm * ror) / 10
                               opti = round(round(opti / 0.0001) * 0.0001, -int(math.floor(math.log10(0.0001))))
                            else:
                                oai = "I"
                                opti = 0
                                ror = 0
                        else:
                            # Call Option
                             putorcall = "C"
                             opti = 0
                             oai = "I"

                         # idtext = [SYMBOL] + [P/C] + EXPDATE +STRIKE
                        curridtext = currsym + putorcall + currexpdate + currstrike
                        curridtext = curridtext.upper()

                        # (symbol,putorcall,expirationdate,strike,premium,volume,numdays,idtext, oi, opti, oai)
                        addstrike = strikes(currsym,putorcall,currexpdate,currstrike,currpremium,currvolume,numdays,curridtext,oi,opti,oai)
                        db.session.add(addstrike)
    db.session.commit()
    flashmsg = "UPDATED " + currsym.upper() + " WITH MOST RECENT DATA"
    flash(flashmsg)
    return redirect(url_for('posit'))
# END


#working here now
# New Auto-Calc for nears out of the money cash secured put and hedged put
@app.route('/new', methods=['POST', 'GET'])
@login_required
def newposit():
    tickernum = 0
    symbols = []
    ListCSPs = []

    tickers = Ticker.query.filter_by(user_id=g.user.id).order_by(Ticker.symbol).with_entities(Ticker.symbol).all()
    for ticker in tickers:
       symbols += list(ticker)

    #symbols = list(symbols)
    for sym in symbols:
         # Looping for each symbol
         symbol = format(sym)
         #updatestrikes(symbol)
         strike = strikes.query.filter_by(symbol=symbol).filter(strikes.opti > 0).filter_by(putorcall="P").order_by(strikes.opti.desc(),strikes.strike.desc()).limit(1)
         short = strike.first()
         ticker = Ticker.query.filter_by(symbol=symbol).first()
         tickerprice = round(ticker.tprice, 1)
         expdate = short.expirationdate
         shortstrike = float(short.strike)
         opti = short.opti
         shortpremium = short.premium
         numdays = short.numdays
         if numdays < 30:
             timemult = numdays / 30
         else:
             timemult = 30 / numdays
         acqcost = (round(round(shortstrike / 0.01) * 0.01, -int(math.floor(math.log10(0.01)))))
         creditprem = shortpremium
         creditprem = (round(round(creditprem / 0.01) * 0.01, -int(math.floor(math.log10(0.01)))))
         ror = (creditprem / acqcost) * timemult
         ror = round(round(ror / 0.001) * 0.001, -int(math.floor(math.log10(0.001))))
         ror = ror * 100
         ror = round(ror,3)
         acqcost = acqcost * 100
         tickernum += 1
         ListCSPs.append(CSPR(LSym=str(symbol),LPrice=str(tickerprice),LExp=str(expdate),LDays=str(numdays),LStrike=str(shortstrike),LPrem=str(creditprem),LROR=str(ror),LCost=str(acqcost)))
         # end of loop

    return render_template('bestone.html', tickers=tickers, numsymbols = tickernum, lists = ListCSPs)
#


# END

# Cash-Secured Puts CSP Cash Secured Puts
@app.route('/csp/<sym>')
@login_required
def csp(sym):
    symbol = format(sym)
    strike = strikes.query.filter_by(symbol=symbol).filter(strikes.opti > 0).filter_by(putorcall="P").order_by(strikes.opti.desc(),strikes.strike.desc()).limit(1)
    short = strike.first()
    ticker = Ticker.query.filter_by(symbol=symbol).first()
    tickerprice = ticker.tprice
    expdate = short.expirationdate
    shortstrike = float(short.strike)
    opti = short.opti
    shortpremium = short.premium
    numdays = short.numdays
    if numdays < 30:
        timemult = numdays / 30
    else:
        timemult = 30 / numdays
    #Long Strike
    acqcost = (round(round(shortstrike / 0.01) * 0.01, -int(math.floor(math.log10(0.01)))))
    creditprem = shortpremium
    creditprem = (round(round(creditprem / 0.01) * 0.01, -int(math.floor(math.log10(0.01)))))
    ror = (creditprem / acqcost) * timemult
    ror = round(round(ror / 0.01) * 0.01, -int(math.floor(math.log10(0.01))))
    ror = ror * 100
    acqcost = acqcost * 100
    return render_template('csp.html', tprice = tickerprice,opti = opti, symbol = symbol, shortstrike = shortstrike, expdate = expdate, initnumdays = numdays, ror = ror, acqcost = acqcost, creditprem = creditprem)
#


#

# Put Spreads
@app.route('/ps/<sym>')
@login_required
def putspread(sym):
    symbol = format(sym)
    #updatestrikes(symbol)  # newly added to refresh strikes

    strike = strikes.query.filter_by(symbol=symbol).filter(strikes.opti > 0).filter_by(putorcall="P").order_by(strikes.opti.desc(),strikes.strike.desc()).limit(1)
    short = strike.first()
    expdate = short.expirationdate
    strike = strikes.query.filter_by(symbol=symbol).filter(strikes.opti > 0).filter_by(expirationdate=expdate).filter_by(putorcall="P").order_by(strikes.strike.desc()).limit(1)
    short = strike.first()
    shortstrike = float(short.strike)
    opti = short.opti
    shortpremium = short.premium
    numdays = short.numdays
    if numdays < 30:
        timemult = numdays / 30
    else:
        timemult = 30 / numdays
    #Long Strike
    if shortstrike < 5:
        minstrike = 0
    elif shortstrike < 20:
        minstrike = shortstrike - 1
    elif shortstrike < 50:
        minstrike = shortstrike - 5
    elif shortstrike < 100:
        minstrike = shortstrike - 5
    elif shortstrike < 300:
        minstrike = shortstrike - 10
    else:
        minstrike = shortstrike - 15
    longstrike = strikes.query.filter_by(symbol=symbol).filter_by(putorcall="P").filter_by(expirationdate=expdate).filter(strikes.strike < shortstrike).filter(strikes.strike > minstrike).order_by(strikes.strike.asc()).limit(5)
    longst = longstrike.first()
    longstrk = float(longst.strike)
    longprem = longst.premium
    margin = shortstrike - longstrk
    margin = (round(round(margin / 0.01) * 0.01, -int(math.floor(math.log10(0.01))))) * 100
    acqcost = (round(round(shortstrike / 0.01) * 0.01, -int(math.floor(math.log10(0.01)))))
    creditprem = shortpremium - longprem
    creditprem = (round(round(creditprem / 0.01) * 0.01, -int(math.floor(math.log10(0.01)))))
    ror = (creditprem / acqcost) * timemult
    ror = round(round(ror / 0.01) * 0.01, -int(math.floor(math.log10(0.01))))
    ror = ror * 100
    ticker = Ticker.query.filter_by(symbol=symbol).first()
    tprice = ticker.tprice
    acqcost = acqcost * 100
    return render_template('putspreads.html', opti = opti, strike = longstrike, longstrk = longstrk, longprem = longprem, symbol = symbol, shortstrike = shortstrike, expdate = expdate, initnumdays = numdays, shortprem = shortpremium, ror = ror, acqcost = acqcost, margin = margin, creditprem = creditprem, tprice = tprice)
#
#
# AUTO CALC
@app.route('/auto/<sym>')
@login_required
def autocalc(sym):
   curropticsp = 0
   curroptipss = 0
   curroptipsl = 0
   curropticspstrike = 0
   curroptipssstrike = 0
   curroptipslstrike = 0
   curropticspprem = 0
   curroptipssprem = 0
   curroptipslprem = 0
   curropticspror = 0
   curropticspotm = 0

   currprdayopticsp = 0
   currpropticspstrike = 0
   currpropticspprem = 0
   currpropticspror = 0
   currpropticspotm = 0
   currpropticspexp = " "
   curropticspexp = " "

   refsymbol = format(sym)

    #
   tagitem = "zacks_target_price_mean"
   url = "https://api.intrinio.com/data_point?identifier="+refsymbol+"&item="+tagitem
   resp = requests.get(url, auth=(intuser, intpass))
   status = resp.status_code
   data = resp.json()
   if str(data["value"]) == "na":
      targetprice = "Zack's Target Price: Not Followed"
   else:
      targetprice = "Zack's Target Price: " + str(data["value"])
   #

   datety = time.strftime("%Y-%m-%d")
   datetoday = datetime.strptime(datety,'%Y-%m-%d').date()
   headers = {"Accept":"application/json",
           "Authorization": authy}

   urlsymbol = baseurl + "markets/quotes?symbols=" + refsymbol
   # Get Stock Data
   resp2 = requests.get(urlsymbol, headers=headers)
   data2 = resp2.json()
   getvol = data2["quotes"]["quote"]["volume"]
   getdesc = data2["quotes"]["quote"]["description"]
   currprice = data2["quotes"]["quote"]["last"]
   gettype = data2["quotes"]["quote"]["type"]
   # End of Stock Data
   roundedprice = round(round(currprice / 0.05) * 0.05, -int(math.floor(math.log10(0.05))))

   # Get Expiration Dates
   url = baseurl + "markets/options/expirations?symbol=" + refsymbol
   resp = requests.get(url, headers=headers)
   data = resp.json()
   allexps = data["expirations"]["date"]
   # End of Expiration Dates

   gobackheading = "<a href=" + url_for('posit') + "><img src='http://www.clker.com/cliparts/b/4/b/S/d/t/square-back-text-black-md.png' width='75' height='75'></a></br>"

   #
   # Symbol with all Expiration Dates loop
   #
   for expdate in allexps:
      #
      # For Each Expiration Date - pull data
      #
      currexpdate = format(expdate)
      dateexp = datetime.strptime(format(expdate),'%Y-%m-%d').date()
      numdays = (dateexp - datetoday).days
      if numdays < 30:
         timemult = numdays / 30
      else:
         timemult = 30 / numdays

      if (numdays > 6) and (numdays < 62):
            url = baseurl + "markets/options/chains?symbol=" + format(sym) + "&expiration=" + currexpdate
            resp = requests.get(url, headers=headers)
            data = resp.json()
            allopts = data["options"]["option"]

            for strike in allopts:
               if (strike["open_interest"] > 2) and (strike["asksize"] > 1) and (strike["bidsize"] > 1):
                  mid = (strike["bid"] + strike["ask"])/2
                  mid = round(round(mid / 0.05) * 0.05, -int(math.floor(math.log10(0.05))))

                  if mid > 0:
                     # PUT SPREADS
                     if strike["option_type"] == "put":
                          if strike["strike"] <= roundedprice:
                           ror = ((mid / strike["strike"]) * 100) * timemult
                           ror = round(round(ror / 0.01) * 0.01, -int(math.floor(math.log10(0.01))))

                           otm = ((currprice - strike["strike"]) / currprice) * 100
                           otm = round(round(otm / 0.01) * 0.01, -int(math.floor(math.log10(0.01))))
                           opti = (otm * ror) / 10
                           opti = round(round(opti / 0.0001) * 0.0001, -int(math.floor(math.log10(0.0001))))


                           if opti > curropticsp:
                              curropticsp = opti
                              curropticspstrike = strike["strike"]
                              curropticspprem = mid
                              curropticspror = ror
                              curropticspotm = otm
                              curropticspexp = currexpdate

                           if ror >= 0.30:
                              if ((opti+ror*2)/3) > ((currprdayopticsp+currpropticspror*2)/3):
                                 currprdayopticsp = opti
                                 currpropticspstrike = strike["strike"]
                                 currpropticspprem = mid
                                 currpropticspror = ror
                                 currpropticspotm = otm
                                 currpropticspexp = currexpdate


            #
            # End of Expiration Data Calcs
            #
   statustext = "</br><b> " + str(getdesc) + " (" + str(refsymbol) + ")"
   statustext = statustext + "</br>Current " + str(gettype) + " Price: $" + str(currprice)  + " and " + targetprice + "</b></br></br>"
   statustext = statustext.upper()


   cashsecuredput = "<b>Option Strategy - Cash Secured Put (Optimized): </b> </br> Expiration Date: " + str(curropticspexp) + "</br>Strike Price: $" + str(curropticspstrike) + "</br>Premium Price: $" + str(curropticspprem) + "</br>Rate of Return: " + str(curropticspror) + "%</br>Out of the Money by " + str(curropticspotm) +"%</br></br>"
   if currpropticspror == 0:
      cashsecuredput = cashsecuredput + "<b>Option Strategy - Cash Secured Put (Increased Rate of Return): </b> </br> None Found</br>"
   else:
      cashsecuredput = cashsecuredput + "<b>Option Strategy - Cash Secured Put (Increased Rate of Return): </b> </br> Expiration Date: " + str(currpropticspexp) + "</br>Strike Price: $" + str(currpropticspstrike) + "</br>Premium Price: $" + str(currpropticspprem) + "</br>Rate of Return: " + str(currpropticspror) + "%</br>Out of the Money by " + str(currpropticspotm) +"%</br>"

   fulltext = gobackheading + statustext + cashsecuredput
   return fulltext




# ORIGINAL FUNCTIONS
@app.route('/manual/oi/<sym>&<exp>')
@login_required
def getorigoptinf(sym,exp):
   symb = format(sym)
   url = baseurl + "markets/options/chains?symbol=" + symb + "&expiration=" + format(exp)
   url2 = baseurl + "markets/quotes?symbols=" + symb

   datety = time.strftime("%Y-%m-%d")
   datetoday = datetime.strptime(datety,'%Y-%m-%d').date()
   dateexp = datetime.strptime(format(exp),'%Y-%m-%d').date()
   exptxtdate = str(dateexp)
   numdays = (dateexp - datetoday).days
   if numdays < 30:
      timemult = numdays / 30
   else:
      timemult = 30 / numdays
   # Number of Days: numdays
   # Today's Date: datetoday
   # Expiration Date: exptxtdate
   # Symbol: symb
   # Current Price: currprice
   backref =  url_for('getoptex',sym=format(sym))


   headers = {"Accept":"application/json",
           "Authorization": authy}
   resp = requests.get(url, headers=headers)
   # Get Stock Data
   resp2 = requests.get(url2, headers=headers)
   data2 = resp2.json()
   tarvol = data2["quotes"]["quote"]["volume"]
   getsym = data2["quotes"]["quote"]["symbol"]
   getdesc = data2["quotes"]["quote"]["description"]
   currprice = data2["quotes"]["quote"]["last"]
   gettype = data2["quotes"]["quote"]["type"]
   #
   data = resp.json()
   allopts = data["options"]["option"]
   puts = []
   calls = []

   for strike in allopts:
      if (strike["open_interest"] > 0 and strike["asksize"] > 0 and strike["bidsize"] > 0):
         mid = (strike["bid"] + strike["ask"])/2
         mid = round(round(mid / 0.05) * 0.05, -int(math.floor(math.log10(0.05))))

         if mid > 0.01:
            # PUT SPREADS
            if strike["option_type"] == "put":
                 ror = ((mid / strike["strike"]) * 100) * timemult
                 ror = round(round(ror / 0.01) * 0.01, -int(math.floor(math.log10(0.01))))
                 otm = ((currprice - strike["strike"]) / currprice) * 100
                 otm = round(round(otm / 0.01) * 0.01, -int(math.floor(math.log10(0.01))))
                 opti = (otm * ror) / 10
                 opti = round(round(opti / 0.0001) * 0.0001, -int(math.floor(math.log10(0.0001))))
                 vol = strike["volume"]
                 testthis = {"strike":strike["strike"],"mid":mid, "ror":ror, "otm":otm, "opti":opti, "vol":vol}

                 puts.append(testthis)



            else:
            # LONG CALLS
                 breakeven = mid + strike["strike"]
                 vol = strike["volume"]
                 testthis = {"strike":strike["strike"],"mid":mid,"breakeven":breakeven,"vol":vol}
                 calls.append(testthis)
   puts = sorted(puts, key=itemgetter('strike'))
   calls = sorted(calls, key=itemgetter('strike'),reverse=True)
   return render_template('mstrikes.html', backref = backref, todaydate = datetoday, tarvol = tarvol, symbol = symb, expdate = exptxtdate, numdays = numdays, currprice = currprice, puts = puts, calls=calls)

  # return testz




# END ORIGINAL FUNCTIONS

# API - CRYPTO
@app.route('/api')
@login_required
def cryptoapi():
   printtext = " "
   # url = 'https://api.coinmarketcap.com/v2/listings/'
   url = "https://api.coinmarketcap.com/v2/ticker/?start=1&limit=100"
   params = None
   resp = requests.get(url,params)
   data = resp.json()
   allids = data["data"]

   printtext = printtext + str(allids)

   return printtext

#

#

if __name__ == "__main__":
    app.run(host='0.0.0.0')
