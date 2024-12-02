from peewee import *

db = SqliteDatabase('tracks.db')

class Tracks(Model):
    id = AutoField(primary_key=True)
    title = TextField(null=True)
    author = TextField(null=True)
    duration = IntegerField()
    directory = TextField()

    class Meta:
        database = db

if __name__ == '__main__':
    db.create_tables([Tracks])