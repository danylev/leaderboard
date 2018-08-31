import uuid
import random
import datetime

from playhouse.db_url import connect
from peewee import Model, fn, SQL
from peewee import UUIDField, ForeignKeyField, IntegerField, DateTimeField

psql_db = connect('postgresql://postgres@localhost:5432/leaderboard_db')

class BaseModel(Model):
    class Meta:
        database = psql_db

class Game(BaseModel):
    uuid = UUIDField(primary_key=True)

class User(BaseModel):
    uuid = UUIDField(primary_key=True)

class Record(BaseModel):
    game = ForeignKeyField(Game, backref='records')
    user = ForeignKeyField(User, backref='records')
    score = IntegerField()
    created_at = DateTimeField(constraints=[SQL('DEFAULT now()')])

def init_tables():
    psql_db.create_tables([Game, User, Record], safe=True)

def generate_users(number_of_users):
    for i in range(number_of_users):
        User(uuid=uuid.uuid4()).save(force_insert=True)

def generate_games(number_of_games):
    for i in range(number_of_games):
        Game(uuid=uuid.uuid4()).save(force_insert=True)

def generate_records(number_of_records):
    users = User.select()
    games = Game.select()
    for i in range(number_of_records):
        user = users.order_by(fn.Random()).limit(1)[0]
        game = games.order_by(fn.Random()).limit(1)[0]
        score = random.randrange(100)
        record = Record(game=game, user=user, score=score).save(force_insert=True)
