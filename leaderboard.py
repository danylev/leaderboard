from gevent import monkey, pywsgi
monkey.patch_all()
from uuid import uuid4, UUID
import json 

import falcon 
from playhouse.shortcuts import model_to_dict

from models import User, Game, Record, psql_db

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)

class LeaderBoardResource(object):
    def __init__(self, limit=None):
        self.limit = limit

    def on_get(self, req, resp):
        """ Handles GET request """
        query = req.params
        records = Record.select().order_by(Record.game).order_by(Record.score.desc())
        if 'version' in query:
            records = records.where(Record.game == query['version'])
        if self.limit:
            records = records.limit(self.limit)
        if 'limit' in query:
            records = records.limit(query['limit'])
        resp.status = falcon.HTTP_200
        resp.body = json.dumps([model_to_dict(record, recurse=False) for record in records], cls=UUIDEncoder, default=str)

    def on_post(self, req, resp):
        try:
            data = req.media
        except KeyError:
            raise falcon.HTTPBadRequest('Missing data')
        resp.status = falcon.HTTP_201
        data['game'] = data['version']
        del data['version']
        record, _ = Record.get_or_create(**data)
        query = ("SELECT x.position,x.id " 
                    "FROM" 
                        "(SELECT id, rank() over(order by record.score DESC) as position "
                        "FROM record WHERE game_id = '{uuid}') x "
                    "WHERE x.id = {id};").format(uuid =record.game, id=record.id)
        cursor = psql_db.execute_sql(query)
        data = cursor.fetchone()
        resp.body = json.dumps({'position': data[0]})

class UserListResourse(object):
    def on_get(self, req, resp):
        users = User.select()
        resp.status = falcon.HTTP_200
        resp.body = json.dumps([model_to_dict(user) for user in users], cls=UUIDEncoder, default=str)

class GameListResourse(object):
    def on_get(self, req, resp):
        games = Game.select()
        resp.status = falcon.HTTP_200
        resp.body = json.dumps([model_to_dict(game) for game in games], cls=UUIDEncoder)

app = falcon.API()

leaderboard = LeaderBoardResource()
users = UserListResourse()
games = GameListResourse()
leaderboardtop10 = LeaderBoardResource(limit=10)
leaderboardtop100 = LeaderBoardResource(limit=100)

app.add_route('/leaderboard', leaderboard)
app.add_route('/leaderboard/top10', leaderboardtop10)
app.add_route('/leaderboard/top100', leaderboardtop100)
app.add_route('/users', users)
app.add_route('/games', games)

port = 8000
server = pywsgi.WSGIServer(("", port), app)
server.serve_forever()
