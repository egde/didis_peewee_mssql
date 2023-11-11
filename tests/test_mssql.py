#!/usr/bin/env python

"""Tests for `didis_peewee_mssql` package."""

from datetime import date
import pytest
from decouple import config

from didis_peewee_mssql.mssql import MSSQLServer
from peewee import Model, CharField, DateField, ForeignKeyField, BlobField, IdentityField, fn, JOIN

database = config('DB_DB')
user=config('DB_USER')
password=config('DB_PASSWORD')
host=config('DB_HOST')

def test_connect():
    sql_server = MSSQLServer(
        database=database,
        user=user,
        password=password,
        host=host,
        trustservercertificate='yes',

    )

    result = sql_server.connect()
    assert result is not None

def test_get_tables():
    sql_server = MSSQLServer(
        database=database,
        user=user,
        password=password,
        host=host,
        trustservercertificate='yes',

    )

    result = sql_server.get_tables()
    assert len(result) >= 0

    result = sql_server.get_tables(schema='ql')
    assert len(result) >= 0

def test_create_table_with_schema():
    db = MSSQLServer(
        database=database,
        user=user,
        password=password,
        host=host,
        trustservercertificate='yes',
        schema='mssql_test'
    )

    class Person(Model):
        name = CharField()
        birthday = DateField()

        class Meta:
            schema = 'mssql_test'
            database = db

    class Pet(Model):
        owner = ForeignKeyField(Person, backref='pets')
        name = CharField()
        animal_type = CharField()

        class Meta:
            schema = 'mssql_test'
            database = db
        
    db.create_tables([Person, Pet])
    db.create_tables([Person, Pet])

    db.execute_sql(sql='''
                   drop table mssql_test.pet
                   drop table mssql_test.person''', params=None)

def test_create_table():
    db = MSSQLServer(
        database=database,
        user=user,
        password=password,
        host=host,
        trustservercertificate='yes',
        schema='mssql_test'
    )

    class Person(Model):
        id = IdentityField()
        name = CharField()
        birthday = DateField()
        picture = BlobField()

        class Meta:
            database = db

    class Pet(Model):
        owner = ForeignKeyField(Person, backref='pets')
        tag = CharField(unique=True)
        name = CharField()
        animal_type = CharField()

        class Meta:
            database = db
        
    db.create_tables([Person, Pet])
    db.create_tables([Person, Pet])

    db.execute_sql(sql='''
                   drop table pet
                   drop table person''', params=None)
    

def test_select_table():
    db = MSSQLServer(
        database=database,
        user=user,
        password=password,
        host=host,
        trustservercertificate='yes',
        schema='mssql_test'
    )

    class Person(Model):
        id = IdentityField()
        name = CharField()
        birthday = DateField()
        picture = BlobField(null=True)

        class Meta:
            database = db

    class Pet(Model):
        owner = ForeignKeyField(Person, backref='pets')
        tag = CharField(unique=True)
        name = CharField()
        animal_type = CharField()

        class Meta:
            database = db
        
    db.create_tables([Person, Pet])

    person = Person.create(
        name='didi',
        birthday=date(year=1999, month=11, day=7)
    )

    assert person.id is not None, 'id is set'

    person2 = Person.create(
        name='dodo',
        birthday=date(year=1991, month=4, day=12)
    )

    assert person2.id is not None, 'id is set'

    pet = Pet.create(
        owner=person,
        tag='11ssa',
        name='Gagamel',
        animal_type='cat'
    )

    assert pet.id is not None, 'id is set'

    pets:list[Pet] = Pet.select().where(Pet.animal_type == 'cat')
    for pet in pets:
        assert pet.owner == person, "the right person is the owner"

    query = (Person
            .select(Person, fn.COUNT(Pet.id).alias('pet_count'))
            .join(Pet, JOIN.LEFT_OUTER)  # include people without pets.
            .group_by(Person)
            .order_by(Person.name)
            .limit(2)
            )

    for person in query:
        # "pet_count" becomes an attribute on the returned model instances.
        print(person.name, person.pet_count, 'pets')


    query = (Person
        .select(Person, fn.COUNT(Pet.id).alias('pet_count'))
        .join(Pet, JOIN.LEFT_OUTER)  # include people without pets.
        .group_by(Person)
        .order_by(Person.name)
        .limit(1)
        .offset(1)
        )

    for person in query:
        # "pet_count" becomes an attribute on the returned model instances.
        print(person.name, person.pet_count, 'pets')

    query = (Person
        .select(Person, fn.COUNT(Pet.id).alias('pet_count'))
        .join(Pet, JOIN.LEFT_OUTER)  # include people without pets.
        .group_by(Person)
        .order_by(Person.name)
        .offset(1)
        )

    for person in query:
        # "pet_count" becomes an attribute on the returned model instances.
        print(person.name, person.pet_count, 'pets')

    db.execute_sql(sql='''
                   drop table pet
                   drop table person''', params=None)

