from flask import Flask,render_template,url_for,g,request,redirect,session,flash
from data_connect import get_connect
from werkzeug.security import check_password_hash, generate_password_hash
from random import randint
import os


app_g = Flask(__name__)

app_g.config['SECRET_KEY'] = os.urandom(20)

@app_g.teardown_appcontext
def close(error):
    if hasattr(g,'data_db'):
        g.data_db.close()

def generate_id():
    range_start = 10**(9-1)
    range_end = (10**9) - 1
    return str(randint(range_start, range_end))

def multiplier(qty,price):
    return float(qty) * float(price) 

def grand_total():
    user = current_user()
    
    db = get_connect()
    if user:
        total = db.execute('select SUM(price) as total from checkout where order_id =?',[user['customer_id']])
        total = total.fetchone()
        total = total['total'] if total['total'] is not None else 0.00
        return total
    else:
        total = db.execute('select SUM(price) as total from checkout where order_id =?',[1])
        total = total.fetchone()
        total = total['total'] if total['total'] is not None else 0.00
        return total
        
def current_user():
    user = None
    if 'user' in session:
        user = session['user']
        db = get_connect()
        user_details = db.execute('select * from customer where username = ?',[user])
        user = user_details.fetchone()
    return user

@app_g.route('/', methods = ["POST","GET"])
def home():
    
    db = get_connect()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = db.execute('select * from customer where username = ?',[username])
        user = user.fetchone()
        if user:
            if check_password_hash(user['password'], password):
                session['user'] = user['username']
                return redirect(url_for('products'))
            else:
                error = "password doesn't match"
                return render_template('html.html', error = error)
        else:
            error = "username not found"
            return render_template('html.html', error = error)
        
    return render_template('html.html')

def trans(item):
    items = list()
    for i in item:
        if i['category'] not in items:
            items.append(i['category'])
    return items
        
@app_g.route('/search',methods =["POST","GET"])
def search():
    user = current_user()
    
    db = get_connect()
    if request.method == "POST":
        search = request.form['search']
        search =f"%{search}%"
        search1 = f"%{search}"
        search2 = f"{search}%"
        search3 = f"__{search}__"
        search4 = f"__{search}"
        search5 = f"{search}__"
        items = db.execute('select * from products where product_name like ? or product_name like ? or product_name like ? or product_name like ? or product_name like ? or product_name like ?',\
            [search,search1,search2,search3,search4,search5])
        items = items.fetchall()
        cat = trans(items)

        return render_template('products.html',user = user,allpd = items,cat=cat)
    
    return redirect(url_for('products'))


@app_g.route('/register',methods = ["POST","GET"])
def register():
 
    db = get_connect()
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        dob = request.form['DOB']
        phone = request.form['phone']
        address = request.form['address']
        username = request.form['username']
        password = request.form['password']
        
        hased = generate_password_hash(password)
        
        if not name or not age or not dob or not phone or not address or not username or not password:
            error = "All the fields are mandatory"
            return render_template('register.html', error = error)
        
        existing = db.execute('select * from customer where username = ?',[username])
        existing = existing.fetchone()
        if existing:
            error = "username is already taken"
            return render_template('register.html', error = error )
        
        db.execute('insert into customer (name,age,DOB,phone,address,username,password)\
            values(?,?,?,?,?,?,?)',[name,age,dob,phone,address,username,hased]) 
        db.commit()
        return redirect(url_for('home'))
    
    return render_template('register.html')

@app_g.route('/products')
def products():
    
    user = current_user()
    
    db=get_connect()
    products = db.execute('select * from products')
    allpd =  products.fetchall() 
    cat = trans(allpd)
    return render_template('products.html', allpd = allpd, user = user,cat=cat)


    
@app_g.route('/addtocart', methods = ['POST','GET'])
def addtocart():
    user = current_user()
    
    if request.method == 'POST':
        qty = request.form['QTY']
        id = request.form['pid']
        
        db = get_connect()
        product = db.execute('select * from products where product_id = ?',[id])
        product = product.fetchone()
        
        try:
            amount = multiplier(qty,product['price'])
            amount = "{:.2f}".format(amount)
        except ValueError:
            return redirect(url_for('products'))
        
        if user:
            items_1 = db.execute('select * from checkout where product_id = ? and order_id =?',[id,user['customer_id']])
            items_1 = items_1.fetchone()

            user_order = user['customer_id']
            if items_1:
                try:
                    qty_add = float(items_1['QTY'])+float(qty)
                    amount_1 = multiplier(qty_add,product['price'])
                    amount_1 = round(amount_1,2)
                except ValueError:
                    return redirect(url_for('products'))
                
                db.execute('update checkout set (QTY,price )= (?,?) where order_id = ? and product_id = ?',\
                    [qty_add,amount_1,user_order,id])
                db.commit()
                return redirect(url_for('products'))
            else:
                db.execute('insert into checkout(order_id,customer_id,QTY,product_id,price,product_name) values(?,?,?,?,?,?)',\
                [user_order,user['customer_id'],qty,product['product_id'],amount,product['product_name']])
                db.commit()
                return redirect(url_for('products'))
        else:
            items = db.execute('select * from checkout where product_id = ? and order_id =?',[id,1])
            items = items.fetchone()
            orderid = 1
            if items:
                try:
                    qty_add = float(items['QTY'])+float(qty)
                    amount_1 = multiplier(qty_add,product['price'])
                    amount_1 = f"{amount_1:.2f}"
                except:
                    return redirect(url_for('products'))
                db.execute('update checkout set (QTY,price )= (?,?) where order_id = ? and product_id = ?',\
                    [qty_add,amount_1,orderid,id])
                db.commit()
                return redirect(url_for('products'))
            else:
                db.execute('insert into checkout(order_id,QTY,product_id,price,product_name) values(?,?,?,?,?)',\
                    [orderid,qty,product['product_id'],amount,product['product_name']])
                db.commit()
                return redirect(url_for('products'))
    return redirect(url_for('products'))
    

@app_g.route('/cart')
def cart():
    user = current_user()
    
    db = get_connect()
    total=grand_total()
    
    if user:
        items = db.execute('select * from checkout where order_id = ?',[user['customer_id']])
        items = items.fetchall()
        return render_template('cart.html' , a = None, user = user, items = items,total = total )
    else:
        items = db.execute('select * from checkout where order_id = ?',[1])
        items = items.fetchall()
        return render_template('cart.html' , a = None, user = user, items = items,total = total )
    

@app_g.route('/delete/<int:pro_id>', methods = ["POST","GET"])
def delete(pro_id):
    user = current_user()
    
    db = get_connect()
    total=grand_total()
    if request.method == 'GET':
        if user:
            db.execute('delete from checkout where product_id = ? and order_id = ?',[pro_id,user['customer_id']])
            db.commit()
            return redirect(url_for('cart'))
        else:
            db.execute('delete from checkout where product_id = ? and order_id = ?',[pro_id,1])
            db.commit()
            return redirect(url_for('cart'))
        
    return render_template('cart.html',  a = None, user = user,total = total)


@app_g.route('/edit/<int:pro_id>', methods = ["POST","GET"])
def edit(pro_id):
    user = current_user()
    
    db = get_connect()
    total=grand_total()
    if request.method == 'GET':
        if user:
            items = db.execute('select * from checkout where order_id = ?',[user['customer_id']])
            items = items.fetchall()
            return render_template('cart.html', user = user ,items=items, a= int(pro_id),total = total)  
        else:
            items = db.execute('select * from checkout where order_id = ?',[1])
            items = items.fetchall()
            return render_template('cart.html', user = user ,items=items, a= int(pro_id),total=total)  
  
    return render_template('cart.html', user = user ,items = items, a = int(pro_id),total = total)


@app_g.route('/edit1', methods = ["POST","GET"])
def edit1():
    user =current_user()
    
    db = get_connect()
    if request.method == "POST":
        qty = request.form['qty']
        id = request.form['id']
        items = db.execute('select * from products where product_id = ?',[id])
        items = items.fetchone() 
        amount = multiplier(qty,items['price'])
        
        if user:
            db.execute('update checkout set (QTY,price )= (?,?) where order_id = ? and product_id = ?',\
            [qty,amount,user['customer_id'],id])
            db.commit()
            return redirect(url_for('cart'))
        else:
            db.execute('update checkout set (QTY,price )= (?,?) where order_id = ? and product_id = ?',\
            [qty,amount,1,id])
            db.commit()
            return redirect(url_for('cart'))    
    return redirect(url_for('cart'))

    
@app_g.route('/checkout')
def checkout():
    user = current_user()
    
    db = get_connect()
    total=grand_total()
    if user:
        items = db.execute('select * from checkout where order_id = ?', [user['customer_id']])
        return render_template('checkout.html',user = user, items = items, total=total)
    else:
        items = db.execute('select * from checkout where order_id = ?', [1])
        return render_template('checkout.html',user = user, items = items, total=total)  


@app_g.route('/pay', methods=["POST","GET"])
def thank_you():
    user = current_user()
    
    id = generate_id()
    db = get_connect()
    
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']

        idu = request.form['uname']
        password = 'no-password'
        if not user:
            db.execute('update checkout set order_id = ? where order_id = ?',[id,1])
            db.execute('insert into customer (name,phone,address,username,password) values (?,?,?,?,?) ',\
                [name,phone,address,idu,password])
            cid = db.execute('select * from customer where phone = ?',[phone])
            cid = cid.fetchone()
            db.execute('update checkout set customer_id = ? where order_id =?',[cid['customer_id'],id])
            db.commit()
            flash('Thank you for shopping!')
            return render_template('checkout.html',user=user)
            
        else:
            db.execute('update customer set (name, phone, address) =(?,?,?) where username = ?',\
                [name,phone,address,idu])
            db.execute('update checkout set order_id = ? where order_id = ?',[id,user['customer_id']])
            db.commit()
            flash('Thank you for shopping!')
            return render_template('checkout.html',user=user)   
    
    return render_template('checkout.html')

@app_g.route("/cancel_order")
def cancel_order():
    db = get_connect()
    db.execute('delete from checkout where order_id = ?',[1])
    db.commit()
    return redirect(url_for('products'))

@app_g.route("/logout")
def logout():
    session.pop('user',None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app_g.run(debug=True)