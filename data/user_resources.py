from flask_restful import abort, Resource
from . import db_session
from .users import User
from flask import jsonify


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    polz = session.query(User).get(user_id)
    if not polz:
        abort(404, message=f"Пользова с id {user_id} не найдут")


class UsersResource(Resource):
    def get(self, users_id):
        abort_if_user_not_found(users_id)
        session = db_session.create_session()
        polz = session.query(User).get(users_id)
        return jsonify({'user': polz.to_dict(
            only=('id', 'name', 'surname', 'nickname', 'age', 'status', 'about', 'email',
                  'date', 'city_from'))})


class UsersListResource(Resource):
    def get(self):
        session = db_session.create_session()
        polz = session.query(User).all()
        return jsonify({'users': [item.to_dict(
            only=('id', 'name', 'surname', 'nickname', 'age', 'status', 'about', 'email',
                  'date', 'city_from')) for item in polz]})
