from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import datetime
import locale

#SETTING_LANGUAGE
locale.setlocale(locale.LC_ALL,"turkish")

app = Flask(__name__,template_folder='C:/Users/mrnet/Desktop/BLOG/templates')
app.secret_key = "myblog"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////Users/mrnet/Desktop/BLOG/database/userdatabase.db"
db = SQLAlchemy(app)

class BlogUsers(db.Model):
   id = db.Column(db.Integer,primary_key = True)
   name = db.Column(db.String)
   username = db.Column(db.String)
   email = db.Column(db.String)
   password = db.Column(db.String)

class BlogArticles(db.Model):
   id = db.Column(db.Integer,primary_key=True)
   title = db.Column(db.String)
   author = db.Column(db.String)
   content = db.Column(db.String)

   now = datetime.datetime.now()
   date = datetime.datetime.strftime(now,"%x")

   created_date = db.Column(db.String,default= date)
   


#LOGIN CONTROL DECORATOR
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
       if "logged_in" in session:
          return f(*args,**kwargs)
       else:
          flash("Giriş yapmalısınız","danger")
          return redirect(url_for("login"))
    return decorated_function

#LOGOUT CONTROL DECORATOR
def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
       if not "logged_in" in session:
          return f(*args,**kwargs)
       else:
          flash("Çıkış yapmalısınız","danger")
          return redirect(url_for("home"))
    return decorated_function

# REGISTERING FORM
class RegisterForm(Form):
   name = StringField("İsim Soyisim",validators=[validators.Length(min=5,max=25,message="En az 5, en fazla 25 karakter uzunluğunda olmalı.")])
   username = StringField("Kullanıcı Adı",validators=[validators.Length(min=5,max=20,message="5 karakterden fazla,20 karakterden az olmalı")])
   email = StringField("Email Adresi",validators=[validators.Email(message = "Lütfen Geçerli Bir Email Adresi Girin...")])
   password = PasswordField("Parola",validators=[
      validators.DataRequired(message="Bu alan boş geçilemez."),
      validators.EqualTo(fieldname = "confirm",message="Parolanız uyuşmuyor!")
   ])
   confirm = PasswordField("Parola Doğrula")

# LOGIN FORM
class LoginForm(Form):
   username = StringField("Kullanıcı Adı",validators=[validators.Length(min=5,max=25,message="En az 5, en fazla 25 karakter uzunluğunda olmalı."),validators.DataRequired(message="Bu alan boş geçilemez.")])
   password = PasswordField("Parola",validators=[validators.DataRequired("Bu alan boş geçilemez.")])

#ARTICLE FORM
class ArticleForm(Form):
   title = StringField("Başlık",validators=[validators.DataRequired(),validators.Length(min=5,max=100,message="Başlık 5 harften büyük olmalı")])
   content = TextAreaField("Makale İçeriği",validators=[validators.Length(min=10,message="İçrik 10 karakterden az olmamalı!")])

"""
#DEFINE_DATABASE 
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "blog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
"""

#HOME
@app.route('/')
def home():
   return render_template("index.html")


#ABOUT
@app.route("/about")
def about():
   return render_template("about.html")

#LOGIN
@app.route("/login",  methods = ["GET","POST"])
@logout_required
def login():
   form = LoginForm(request.form)

   if request.method == "POST" and form.validate():
      username = form.username.data
      password_entered = form.password.data

      #Database connection
      """
      cursor = mysql.connection.cursor()
      sorgu = "Select * From users where username = %s"
      result = cursor.execute(sorgu,(username,))
      """

      result = BlogUsers.query.filter_by(username = username).first()

      if not result == None:
         #sözlük yapısında
         real_password = result.password
         name = result.name

         if sha256_crypt.verify(password_entered,real_password):
            flash("Hoşgeldin {}".format(name),"success")

            session["logged_in"] = True
            session["username"] = username


            return redirect(url_for("home"))
         else:
            flash("Parola Hatalı","danger")
            return redirect(url_for("login"))
         
      else:
         flash("Böyle bir kullanıcı yok","danger")
         return redirect(url_for("login"))
   else:
      return render_template("login.html",form=form)

#LOGOUT
@app.route("/logout")
@login_required
def logout():
   session.clear()
   flash("Çıkış yapıldı","success")
   return redirect(url_for("home"),)


#REGISTER
@app.route("/register", methods = ["GET","POST"])
@logout_required
def register():
   form = RegisterForm(request.form)

   if request.method == "POST" and form.validate():

      name = form.name.data
      username = form.username.data
      email = form.email.data
      password = sha256_crypt.encrypt(form.password.data)

      #Database connection
      """
      cursor = mysql.connection.cursor()
      sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
      cursor.execute(sorgu,(name,email,username,password))
      mysql.connection.commit()
      cursor.close()
      """

      user = BlogUsers(name = name,username = username,email = email,password = password)
      db.session.add(user)
      db.session.commit()

      

      #FLASH MESSAGE
      flash("Kaydınız Başarıyla Gerçekleşti...","success")

      return redirect(url_for("login"))
   else:
      return render_template("register.html",form = form)


#ARTICLES
@app.route("/articles")
def articles():
   """
   cursor = mysql.connection.cursor()
   sorgu = "Select * From articles"
   result = cursor.execute(sorgu)
   """

   result = BlogArticles.query.all()

   if not result == None:
      articles = list()
      for i,x in enumerate(result,start=1):
         articles.append([i,x])

      return render_template("articles.html",articles = articles)
   else:
      return render_template("articles.html")


#DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
   """
   cursor = mysql.connection.cursor()
   sorgu = "Select * From articles where author = %s"
   result = cursor.execute(sorgu,(session["username"],))
   """

   result = BlogArticles.query.filter_by(author = session["username"])


   if not result == None:
      articles = list()
      for i,x in enumerate(result,start=1):
         articles.append([i,x])

      return render_template("dashboard.html",articles = articles)
   else:
      flash("Makaleniz Bulunmuyor.","danger")
      return render_template("dashboard.html")

#ADDARTICLE
@app.route("/addarticle",methods=["GET","POST"])
@login_required
def addarticle():
   form = ArticleForm(request.form)

   if request.method == "POST" and form.validate():
      title = form.title.data
      content = form.content.data
      author = session["username"]
      """
      cursor = mysql.connection.cursor()
      sorgu = "Insert into articles(title,content,author) VALUES(%s,%s,%s)"
      cursor.execute(sorgu,(title,content,author,))
      mysql.connection.commit()
      cursor.close()
      """

      article = BlogArticles(title = title,author = author,content = content)
      db.session.add(article)
      db.session.commit()

      flash("Makaleniz Başarıyla Eklendi","success")
      return redirect(url_for("dashboard"))
   else:
      return render_template("addarticle.html",form = form)

#ARTICLE DETAIL
@app.route("/article/<string:id>")
def article(id):
   """
   cursor = mysql.connection.cursor()
   sorgu = "Select * From articles where id = %s"
   result = cursor.execute(sorgu,(id,))
   """

   article = BlogArticles.query.filter_by(id = id).first()

   if not article == None:
      return render_template("article.html",article = article)
   else:
      return render_template("article.html")

#ARTICLE DELETE
@app.route("/delete/<string:id>")
@login_required
def delete(id):
   """
   cursor = mysql.connection.cursor()
   sorgu = "Select * From articles where author = %s and id = %s"
   result = cursor.execute(sorgu,(session["username"],id,))
   """
   result = BlogArticles.query.filter_by(id = id,author = session["username"]).first()


   if not result == None:
      """
      sorgu2 = "Delete from articles where id = %s"
      cursor.execute(sorgu2,(id,))
      mysql.connection.commit()
      cursor.close()
      """

      db.session.delete(result)
      db.session.commit()

      flash("Makaleniz silindi...","success")
      return redirect(url_for("dashboard"))
   else:
      flash("Böyle bir makale yok veya sizin silme yetkiniz yok!","danger")
      return redirect(url_for("home"))

#EDIT ARTICLE
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def edit(id):
   if request.method == "GET":
      """
      cursor = mysql.connection.cursor()
      sorgu = "Select * From articles where author = %s and id = %s"
      result = cursor.execute(sorgu,(session["username"],id,))
      """

      result = BlogArticles.query.filter_by(id = id,author = session["username"]).first()

      if not result == None:
         form = ArticleForm()
         form.title.data = result.title
         form.content.data = result.content

         return render_template("edit.html",form = form)

      else:
         flash("Böyle bir makale yok ya da düzenleme yetkiniz yok!","danger")
         return redirect(url_for("home"))
   else:
      #POST REQUEST
      form = ArticleForm(request.form)
      newtitle = form.title.data
      newcontent = form.content.data
      now = datetime.datetime.now()
      date = datetime.datetime.strftime(now,"%x")

      """
      cursor = mysql.connection.cursor()
      sorgu2 = "Update articles set title = %s,content = %s where id = %s"
      cursor.execute(sorgu2,(newtitle,newcontent,id,))
      mysql.connection.commit()
      """

      result = BlogArticles.query.filter_by(id = id).first()
      result.title = newtitle
      result.content = newcontent
      result.created_date = date
      db.session.commit()

      flash("Güncellendi...","success")

      return redirect(url_for("dashboard"))

#SEARCHING
@app.route("/search",methods=["GET","POST"])
def search():
   if request.method == "GET":
      return redirect(url_for("home"))
   else:
      """
      keyword = request.form.get("keyword")
      cursor = mysql.connection.cursor()
      sorgu = "Select * From articles where title like '%"+ keyword +"%'"
      result = cursor.execute(sorgu)
      """

      keyword = request.form.get("keyword")
      tag = "%{}%".format(keyword)
      result = BlogArticles.query.filter(BlogArticles.title.like(tag)).all()
      print("Burda result degeri: ",result)

      if result == []:
         flash("Aradığınız kelimeye uygun sonuç bulunamadı...","danger")
         return redirect(url_for("articles"))
      else:
         articles = list()
         for i,x in enumerate(result,start=1):
            articles.append([i,x])

         return render_template("articles.html",articles = articles)

if __name__ == "__main__":
   db.create_all()
   app.run(debug = True)
