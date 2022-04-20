import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase

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

class News(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'news'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String)
    content = sqlalchemy.Column(sqlalchemy.String)
    created_date = sqlalchemy.Column(sqlalchemy.String,
                                     default=get_date(datetime.datetime.now()))
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    comms = sqlalchemy.Column(sqlalchemy.String)
    user = orm.relation('User')