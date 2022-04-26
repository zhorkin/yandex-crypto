# -*- coding: utf-8 -*-

import datetime
import os
import random
from data.news import News
from data.users import User
from forms.CommentForm import ComForm
from forms.RegisterForm import RegisterForm
from forms.AddNews import AddNewsForm
from forms.Profile import ProfileForm
from flask import Flask, render_template, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_restful import abort
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from wtforms import PasswordField, BooleanField, SubmitField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired
from data import db_session, user_resources, news_resources, comments_resources
from data.comments import Comments
import json
from flask_restful import Api, abort
from requests import Session


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
api = Api(app)
api.add_resource(user_resources.UsersResource, '/api/v1/users/<int:users_id>')
api.add_resource(user_resources.UsersListResource, '/api/v1/users')
api.add_resource(news_resources.NewsResource, '/api/v1/news/<int:news_id>')
api.add_resource(news_resources.NewsListResource, '/api/v1/news')
api.add_resource(comments_resources.CommentsResource, '/api/v1/comments/<int:comments_id>')
api.add_resource(comments_resources.CommentsListResource, '/api/v1/comments')
db_session.global_init("db/user.db")
db_sess = db_session.create_session()
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form, title='Авторизация')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/")
def index():
    return render_template("index.html", title='Главная')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(nickname=form.nickname.data,
            name=form.name.data,
            email=form.email.data,
            about=form.about.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


def info_coin(name_coin, currency, do, nums):
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
    parameters = {
        'slug': name_coin,
        'convert': currency
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': '6c350f8c-fcba-45ff-be4c-62dec7f2a697',
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        return data['data'][nums]['quote'][currency][do]
    except (ConnectionError) as e:
        print(e)


@app.route("/catalog")
def catalog():
    price_btc = info_coin('bitcoin', 'USD', 'price', '1')
    value_btc = info_coin('bitcoin', 'USD', 'volume_24h', '1')

    price_eth = info_coin('ethereum', 'USD', 'price', '1027')
    value_eth = info_coin('ethereum', 'USD', 'volume_24h', '1027')

    price_usdt = info_coin('tether', 'RUB', 'price', '825')
    value_usdt = info_coin('tether', 'RUB', 'volume_24h', '825')

    return render_template("catalog.html", title='Каталог', price_btc=price_btc, value_btc=value_btc,
                           price_eth=price_eth, value_eth=value_eth, price_usdt=price_usdt, value_usdt=value_usdt)


@app.route("/news", methods=['GET', 'POST'])
def news():
    db_sess = db_session.create_session()
    rec_news = db_sess.query(News).all()
    top_news = []
    news_index = 0
    path = 'static/img/photo/default.jpg'
    for news in rec_news:
        path = ''
        news_index += 1
        creator_nickname = (db_sess.query(User).filter(User.id == news.user_id).first()).nickname
        for images in os.listdir('static/img/photo'):
            if images.split('.')[0] == creator_nickname:
                path = 'static/img/photo/' + images
        if path == '':
            path = 'static/img/photo/default.jpg'
        comments = []
        if news.comms:
            if ';' in news.comms:
                for com_id in news.comms.split(';'):
                    comments.append(db_sess.query(Comments).filter(Comments.id == com_id).first())
            elif len(news.comms) == 1:
                com_id = news.comms
                comments = [db_sess.query(Comments).filter(Comments.id == com_id).first()]
        else:
            comments = []
        if len(comments) > 1:
            comments = sorted(comments, key=lambda x: x.created_date)
        comments_main = []
        for com in comments:
            comentor_nickname = db_sess.query(User).filter(User.id == com.user_id).first().nickname
            comments_main.append({'id': com.id,
                                  'content': com.content,
                                  'created_date': com.created_date,
                                  'creator': comentor_nickname})
        comments = comments_main
        top_news.append({'id': news.id,
                         'title': news.title,
                         'content': news.content,
                         'created_date': news.created_date,
                         'comms': comments,
                         'creator': creator_nickname,
                         'path': path})
    return render_template("news.html", top_news=top_news, path=path, random_id=random.randint(1, 2 ** 16),
                           title='Лента')


@app.route("/catalog/bitcoin")
def bitcoin():
    return render_template("bitcoin.html", title='Bitcoin')


@app.route("/catalog/ethereum")
def ethereum():
    return render_template("ethereum.html", title='Ethereum')


@app.route("/catalog/tether")
def tether():
    return render_template("tether.html", title='USDT')


@app.route("/faq")
def faq():
    return render_template("faq.html", title='Часто задаваемые вопросы.')


@app.route("/com_add/<int:new_id>", methods=['GET', 'POST'])
def comm_add(new_id):
    form = ComForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        to_new = db_sess.query(News).filter(News.id == new_id).first()
        id1 = len(db_sess.query(Comments).all()) + 1
        try:
            if len(to_new.comms) > 0:
                to_new.comms = str(to_new.comms) + ';{}'.format(id1)
        except:
                to_new.comms = id1
        com = Comments()
        com.user_id = current_user.id
        com.content = form.content.data
        com.created_date = get_date(datetime.datetime.now())
        db_sess.add(com)
        db_sess.add(to_new)
        db_sess.commit()
        return redirect('/news')
    return render_template("add_com.html", form=form, title='Добавить комментарий')


def get_date(date):
    day_list = ['Первое', 'Второе', 'Третье', 'Четвёртое',
        'Пятое', 'Шестое', 'Седьмое', 'Восьмое',
        'Девятое', 'Десятое', 'Одиннадцатое', 'Двенадцатое',
        'Тринадцатое', 'Четырнадцатое', 'Пятнадцатое', 'Шестнадцатое',
        'Семнадцатое', 'Восемнадцатое', 'Девятнадцатое', 'Двадцатое',
        'Двадцать первое', 'Двадцать второе', 'Двадцать третье',
        'Двадацать четвёртое', 'Двадцать пятое', 'Двадцать шестое',
        'Двадцать седьмое', 'Двадцать восьмое', 'Двадцать девятое',
        'Тридцатое', 'Тридцать первое']
    month_list = ['Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня',
           'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря']
    date = str(date)[:10]
    date_list = date.split('-')
    return (day_list[int(date_list[2]) - 1] + ' ' +
            month_list[int(date_list[1]) - 1] + ' ' +
            date_list[0] + ' года')


@app.route("/profile", methods=['GET', 'POST'])
@login_required
def my_profile():
    pathu = ''
    form = ProfileForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if user:
            form.name.data = user.name
            form.surname.data = user.surname
            form.nickname.data = user.nickname
            form.age.data = user.age
            form.status.data = user.status
            form.email.data = user.email
            form.city_from.data = user.city_from
        else:
            abort(404)
    if form.validate_on_submit():
        if '.jpg' in str(request.files['file']) or '.png' in str(request.files['file']):
            input_file = request.files['file']
            new_img = open("static/img/photo/" + str(current_user.nickname) + ".jpg", 'wb')
            new_img.write(input_file.read())
            new_img.close()
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if user:
            user.name = form.name.data
            user.surname = form.surname.data
            user.age = form.age.data
            user.status = form.status.data
            user.email = form.email.data
            user.city_from = form.city_from.data
            db_sess.commit()
            return redirect('/profile')
        else:
            abort(404)
    for images in os.listdir('static/img/photo'):
        if images.split('.')[0] == current_user.nickname:
            pathu = 'static/img/photo/' + images
    if pathu == '':
        pathu = 'static/img/photo/default.jpg'
    db_sess = db_session.create_session()
    unews = db_sess.query(News).filter(News.user_id == current_user.id).all()
    users_news = []
    for news in unews:
        path = ''
        creator_nickname = (db_sess.query(User).filter(User.id == news.user_id).first()).nickname
        for images in os.listdir('static/img/photo'):
            if images.split('.')[0] == creator_nickname:
                path = 'static/img/photo/' + images
        if path == '':
            path = 'static/img/photo/default.jpg'
        comments = []
        if news.comms:
            if ';' in news.comms:
                for com_id in news.comms.split(';'):
                    comments.append(db_sess.query(Comments).filter(Comments.id == com_id).first())
            elif len(news.comms) == 1:
                com_id = news.comms
                comments = [db_sess.query(Comments).filter(Comments.id == com_id).first()]
        else:
            comments = []
        if len(comments) > 1:
            comments = sorted(comments, key=lambda x: x.created_date)
        comments_main = []
        for com in comments:
            comentor_nickname = db_sess.query(User).filter(User.id == com.user_id).first().nickname
            comments_main.append({'id': com.id,
                                  'content': com.content,
                                  'created_date': com.created_date,
                                  'creator': comentor_nickname})
        comments = comments_main
        users_news.append({'id': news.id,
                           'title': news.title,
                           'content': news.content,
                           'created_date': news.created_date,
                           'comms': comments,
                           'creator': creator_nickname,
                           'path': path})
    return render_template('profile.html',
                           form=form, path=pathu, random_id=random.randint(1, 2 ** 16),
                           users_news=users_news, title='Профиль')


@app.route("/add_news", methods=['GET', 'POST'])
def add_news():
    form = AddNewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.user_id = current_user.id
        news.title = form.news_name.data
        news.content = form.news_content.data
        db_sess.add(news)
        db_sess.commit()
        return redirect('/news')
    return render_template("add_news.html", form=form, title='Добавить новость')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
