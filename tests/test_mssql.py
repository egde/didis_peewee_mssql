#!/usr/bin/env python

"""Tests for `didis_peewee_mssql` package."""

import pytest
from decouple import config

from didis_peewee_mssql.mssql import MSSQLServer
from peewee import Model, CharField, DateField, ForeignKeyField, BlobField, IdentityField

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

