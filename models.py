from peewee import *

database = SqliteDatabase("cache.db")


class Video(Model):
    vidId = CharField(unique=True)
    title = CharField()
    description = CharField()
    channel = CharField()
    publishDate = DateTimeField()
    thumbnail = CharField()

    class Meta:
        database = database


database.connect()
database.create_tables([Video])
