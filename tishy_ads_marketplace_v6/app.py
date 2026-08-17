from flask import Flask, render_template, jsonify, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, re, secrets, time
app=Flask(__name__); app.secret_key=os.environ.get('TISHY_SECRET_KEY','change-this-key'); DB=os.path.join(os.path.dirname(__file__),'tishy_ads.db')
CATEGORIES=['All','Phones & Tablets','Laptops & Computers','Vehicles','Electronics','Gaming','Fashion','Home & Furniture','Photography','Beauty','Jobs & Services','Property','Babies & Kids','Sports & Fitness','Books & Education','Food & Groceries','Accessories','Other']
LOCATIONS=['All','Lagos','Abuja','Ibadan','Port Harcourt','Benin City','Kano','Enugu','Kaduna','Ilorin','Abeokuta','Jos','Warri','Owerri','Akure','Uyo']
SEED=[
('iPhone 15 Pro',1250000,'Phones & Tablets','Lagos','Foreign Used','https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=900'),('PlayStation 5 Slim',850000,'Gaming','Abuja','Brand New','https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=900'),('HP EliteBook',680000,'Laptops & Computers','Ikeja','Refurbished','https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=900'),('Premium Sedan',18500000,'Vehicles','Abuja','Foreign Used','https://images.unsplash.com/photo-1502877338535-766e1452684a?w=900'),('Smart TV 55-inch',720000,'Electronics','Lekki','Brand New','https://images.unsplash.com/photo-1593784991095-a205069470b6?w=900'),('Running Sneakers',145000,'Fashion','Surulere','Brand New','https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=900'),('Modern Sofa',520000,'Home & Furniture','Gwarinpa','Brand New','https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=900'),('Digital Camera',950000,'Photography','Victoria Island','Foreign Used','https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=900'),('MacBook Air',1350000,'Laptops & Computers','Yaba','Brand New','https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=900'),('City SUV',22000000,'Vehicles','Wuse','Foreign Used','https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=900'),('Wireless Headphones',285000,'Electronics','Port Harcourt','Brand New','https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900'),('Gaming Desktop',1750000,'Gaming','Benin City','Brand New','https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=900'),('Smartwatch',180000,'Phones & Tablets','Abuja','Brand New','https://images.unsplash.com/photo-1544117519-31a4b719223d?w=900'),('Leather Handbag',190000,'Fashion','Lagos','Brand New','https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=900'),('Mountain Bicycle',410000,'Sports & Fitness','Abuja','Brand New','https://images.unsplash.com/photo-1485965120184-e220f721d03e?w=900')]
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init():
 c=db(); c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,password TEXT,phone TEXT,location TEXT);CREATE TABLE IF NOT EXISTS listings(id INTEGER PRIMARY KEY,user_id INTEGER,title TEXT,price INTEGER,category TEXT,location TEXT,condition TEXT,description TEXT,image_url TEXT,status TEXT DEFAULT 'active',views INTEGER DEFAULT 0);CREATE TABLE IF NOT EXISTS favourites(user_id INTEGER,listing_id INTEGER,PRIMARY KEY(user_id,listing_id));CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,sender_id INTEGER,listing_id INTEGER,message TEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
 if c.execute('SELECT COUNT(*) FROM listings').fetchone()[0]==0:
  for title,price,cat,loc,cond,img in SEED:c.execute('INSERT INTO listings(title,price,category,location,condition,description,image_url) VALUES(?,?,?,?,?,?,?)',(title,price,cat,loc,cond,f'Quality {title} available. Inspect before purchase and arrange a safe meeting.',img))
 c.commit(); c.close()
init()
def me():
 if not session.get('uid'):return None
 c=db();x=c.execute('SELECT id,name,email,phone,location FROM users WHERE id=?',(session['uid'],)).fetchone();c.close();return dict(x) if x else None
@app.context_processor
def context():return {'me':me(),'categories':CATEGORIES,'locations':LOCATIONS}
@app.route('/')
def home():return render_template('index.html')
@app.route('/browse')
def browse():return render_template('browse.html')
@app.route('/listing/<int:i>')
def listing(i):return render_template('listing.html',lid=i)
@app.route('/sell')
def sell():return render_template('sell.html')
@app.route('/account')
def account():return render_template('account.html') if me() else redirect('/login')
@app.route('/login')
def login():return render_template('auth.html',register=False)
@app.route('/register')
def register():return render_template('auth.html',register=True)
@app.route('/logout')
def logout():session.clear();return redirect('/')
@app.route('/contact')
def contact():return render_template('contact.html')
@app.route('/about')
def about():return render_template('about.html')
@app.get('/api/listings')
def listings():
 q=request.args.get('q','').lower();cat=request.args.get('category','All');loc=request.args.get('location','All');c=db();rows=c.execute('SELECT l.*,COALESCE(u.name,"Tishy Ads Seller") seller FROM listings l LEFT JOIN users u ON u.id=l.user_id WHERE l.status="active" ORDER BY l.id DESC').fetchall();c.close();out=[]
 for r in rows:
  d=dict(r);hay=(d['title']+' '+d['category']+' '+d['location']).lower()
  if q and q not in hay or cat!='All' and d['category']!=cat or loc!='All' and d['location']!=loc:continue
  d['alt']='Product image showing '+d['title'];d['is_favourite']=False
  if me():
   c=db();d['is_favourite']=bool(c.execute('SELECT 1 FROM favourites WHERE user_id=? AND listing_id=?',(session['uid'],d['id'])).fetchone());c.close()
  out.append(d)
 s=request.args.get('sort');out.sort(key=lambda x:x['price'],reverse=s=='high') if s in ('low','high') else None
 return jsonify(out)
@app.get('/api/listing/<int:i>')
def one(i):
 c=db();r=c.execute('SELECT l.*,COALESCE(u.name,"Seller") seller FROM listings l LEFT JOIN users u ON u.id=l.user_id WHERE l.id=?',(i,)).fetchone()
 if not r:return jsonify(error='Listing not found'),404
 c.execute('UPDATE listings SET views=views+1 WHERE id=?',(i,));c.commit();c.close();return jsonify(dict(r))
@app.post("/api/register")
def api_register():
    d=request.get_json() or {}
    if not all(str(d.get(k,"")).strip() for k in ["name","email","password"]):
        return jsonify(error="Complete all required fields"),400
    pw=d["password"]
    if len(pw)<8 or not re.search(r"[A-Z]",pw) or not re.search(r"[a-z]",pw) or not re.search(r"[^A-Za-z0-9]",pw):
        return jsonify(error="Password must have 8+ characters, an uppercase letter, a lowercase letter and a special character"),400
    try:
        c=db()
        c.execute("INSERT INTO users(name,email,password,phone,location) VALUES(?,?,?,?,?)",
                  (d["name"],d["email"].lower(),generate_password_hash(pw),d.get("phone",""),d.get("location","")))
        c.commit()
        uid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.close()
        code=send_demo_code(d["email"].lower(),make_code(),"registration")
        session["pending_uid"]=uid
        return jsonify(ok=True,requires_verification=True,demo_code=code)
    except sqlite3.IntegrityError:
        return jsonify(error="Email already registered"),400


@app.post("/api/login")
def api_login():
    d=request.get_json() or {}
    c=db()
    u=c.execute("SELECT * FROM users WHERE email=?",(d.get("email","").lower(),)).fetchone()
    c.close()
    if not u or not check_password_hash(u["password"],d.get("password","")):
        return jsonify(error="Incorrect email or password"),401
    code=send_demo_code(u["email"],make_code(),"login")
    session["pending_uid"]=u["id"]
    return jsonify(ok=True,requires_verification=True,demo_code=code)

@app.post("/api/verify")
def verify_code():
    d=request.get_json() or {}
    code=str(d.get("code","")).strip()
    if not session.get("pending_uid") or not session.get("demo_otp"):
        return jsonify(error="No verification request is active"),400
    if time.time()>session.get("demo_otp_expires",0):
        return jsonify(error="That code has expired. Request a new one."),400
    if code!=session.get("demo_otp"):
        return jsonify(error="Incorrect verification code"),400
    session["uid"]=session.pop("pending_uid")
    for k in ["demo_otp","demo_otp_email","demo_otp_purpose","demo_otp_expires"]:
        session.pop(k,None)
    return jsonify(ok=True)

@app.post("/api/resend-code")
def resend_code():
    if not session.get("pending_uid"):
        return jsonify(error="No verification request is active"),400
    c=db()
    u=c.execute("SELECT email FROM users WHERE id=?",(session["pending_uid"],)).fetchone()
    c.close()
    if not u: return jsonify(error="Account not found"),400
    code=send_demo_code(u["email"],make_code(),session.get("demo_otp_purpose","verification"))
    return jsonify(ok=True,demo_code=code)


@app.post('/api/listings')
def create():
 if not me():return jsonify(error='Sign in before publishing a listing'),401
 d=request.get_json();keys=['title','price','category','location','condition','description']
 if not all(str(d.get(k,'')).strip() for k in keys):return jsonify(error='Complete every field'),400
 try:p=int(float(d['price']))
 except:return jsonify(error='Invalid price'),400
 c=db();c.execute('INSERT INTO listings(user_id,title,price,category,location,condition,description,image_url) VALUES(?,?,?,?,?,?,?,?)',(session['uid'],d['title'],p,d['category'],d['location'],d['condition'],d['description'],d.get('image_url','')));c.commit();i=c.execute('SELECT last_insert_rowid()').fetchone()[0];c.close();return jsonify(ok=True,id=i)
@app.post('/api/favourite/<int:i>')
def favourite(i):
 if not me():return jsonify(error='Sign in to save listings'),401
 c=db();x=c.execute('SELECT 1 FROM favourites WHERE user_id=? AND listing_id=?',(session['uid'],i)).fetchone()
 if x:c.execute('DELETE FROM favourites WHERE user_id=? AND listing_id=?',(session['uid'],i));saved=False
 else:c.execute('INSERT INTO favourites VALUES(?,?)',(session['uid'],i));saved=True
 c.commit();c.close();return jsonify(saved=saved)
@app.get('/api/my-listings')
def mine():
 if not me():return jsonify([])
 c=db();r=c.execute('SELECT * FROM listings WHERE user_id=? ORDER BY id DESC',(session['uid'],)).fetchall();c.close();return jsonify([dict(x) for x in r])
@app.get('/api/favourites')
def favs():
 if not me():return jsonify([])
 c=db();r=c.execute('SELECT l.* FROM listings l JOIN favourites f ON f.listing_id=l.id WHERE f.user_id=?',(session['uid'],)).fetchall();c.close();return jsonify([dict(x) for x in r])
@app.post('/api/message')
def message():
 if not me():return jsonify(error='Sign in to message sellers'),401
 d=request.get_json();c=db();c.execute('INSERT INTO messages(sender_id,listing_id,message) VALUES(?,?,?)',(session['uid'],d['listing_id'],d['message']));c.commit();c.close();return jsonify(ok=True)
if __name__=='__main__':app.run(debug=True)
