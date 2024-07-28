import sqlite3
from flask import g 

def connect_data():
    sql = sqlite3.connect('C:/Users/demoa/OneDrive/Desktop/ravali project/ravali p/grocery_1.db')
    sql.row_factory = sqlite3.Row
    return sql

def get_connect():
    if not hasattr(g, 'data_db'):
        g.data_db = connect_data()
    return g.data_db