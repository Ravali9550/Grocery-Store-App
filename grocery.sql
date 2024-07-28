create table products (product_id INTEGER PRIMARY KEY , product_name text, price REAL , unit text , description text, category text);

create table checkout (id INTEGER PRIMARY KEY,order_id  INT ,product_name text,customer_id INT,QTY INT, product_id text, price REAL,
time TIMESTAMP DEFAULT CURRENT_TIMESTAMP );

create table customer (customer_id INTEGER PRIMARY KEY  , name text not null , age INT ,DOB DATE, address text,  phone text not null,
username text not null,password text not null );
