import os
import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

def init_db_engine():
    db_config = {
        "pool_size": 5,
        "max_overflow": 2,
        "pool_timeout": 30,
        "pool_recycle": 3600,
        "pool_pre_ping": True
    }
    
    db_uri = f"mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASS']}@{os.environ['DB_HOST']}/{os.environ['DB_NAME']}"
    return create_engine(db_uri, **db_config)

db = init_db_engine()

def init_db():
    with db.connect() as conn:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL
            )
        '''))
        
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                author VARCHAR(255) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                description TEXT,
                image_url VARCHAR(255)
            )
        '''))
        
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS cart (
                user_id INT NOT NULL,
                book_id INT NOT NULL,
                quantity INT DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (book_id) REFERENCES books (id),
                PRIMARY KEY (user_id, book_id)
            )
        '''))
        
        if not conn.execute(text('SELECT COUNT(*) FROM books')).scalar():
            sample_books = [
                {'title': 'The Great Gatsby', 'author': 'F. Scott Fitzgerald', 'price': 10.99, 
                 'description': 'A story of wealth and love in the Jazz Age', 'image_url': 'https://m.media-amazon.com/images/I/71FTb9X6wsL._AC_UF1000,1000_QL80_.jpg'},
                {'title': 'To Kill a Mockingbird', 'author': 'Harper Lee', 'price': 12.50,
                 'description': 'A powerful story of racial injustice', 'image_url': 'https://m.media-amazon.com/images/I/71FxgtFKcQL._AC_UF1000,1000_QL80_.jpg'},
                {'title': '1984', 'author': 'George Orwell', 'price': 9.99,
                 'description': 'Dystopian novel about totalitarianism', 'image_url': 'https://m.media-amazon.com/images/I/71kxa1-0mfL._AC_UF1000,1000_QL80_.jpg'}
            ]
            for book in sample_books:
                conn.execute(text('''
                    INSERT INTO books (title, author, price, description, image_url)
                    VALUES (:title, :author, :price, :description, :image_url)
                '''), book)
        conn.commit()

@app.before_first_request
def initialize_database():
    init_db()

def with_db_connection(f):
    def wrapper(*args, **kwargs):
        conn = db.connect()
        try:
            result = f(conn, *args, **kwargs)
            conn.commit()
            return result
        except SQLAlchemyError as e:
            conn.rollback()
            flash('Database error occurred', 'danger')
            app.logger.error(f"Database error: {str(e)}")
            return redirect(url_for('home'))
        finally:
            conn.close()
    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper

@app.route('/')
@with_db_connection
def home(conn):
    books = conn.execute(text('SELECT * FROM books LIMIT 3')).fetchall()
    return render_template('home.html', books=books)

@app.route('/books')
@with_db_connection
def books(conn):
    books = conn.execute(text('SELECT * FROM books')).fetchall()
    return render_template('books.html', books=books)

@app.route('/book/<int:id>')
@with_db_connection
def book_detail(conn, id):
    book = conn.execute(text('SELECT * FROM books WHERE id = :id'), {'id': id}).fetchone()
    if not book:
        flash('Book not found', 'danger')
        return redirect(url_for('books'))
    return render_template('book_detail.html', book=book)

@app.route('/search')
@with_db_connection
def search(conn):
    query = request.args.get('q', '')
    results = conn.execute(text('''
        SELECT * FROM books 
        WHERE title LIKE :query OR author LIKE :query
    '''), {'query': f'%{query}%'}).fetchall()
    return render_template('search_results.html', results=results, query=query)

@app.route('/cart')
@with_db_connection
def cart(conn):
    if 'user_id' not in session:
        flash('Please login to view your cart', 'warning')
        return redirect(url_for('login'))
    
    cart_items = conn.execute(text('''
        SELECT books.id, books.title, books.price, cart.quantity 
        FROM cart JOIN books ON cart.book_id = books.id
        WHERE cart.user_id = :user_id
    '''), {'user_id': session['user_id']}).fetchall()
    
    total = sum(item.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add-to-cart/<int:book_id>', methods=['POST'])
@with_db_connection
def add_to_cart(conn, book_id):
    if 'user_id' not in session:
        flash('Please login to add items to cart', 'warning')
        return redirect(url_for('login'))
    
    quantity = int(request.form.get('quantity', 1))
    book = conn.execute(text('SELECT id FROM books WHERE id = :id'), {'id': book_id}).fetchone()
    if not book:
        flash('Book not found', 'danger')
        return redirect(url_for('books'))
    
    existing = conn.execute(text('''
        SELECT quantity FROM cart 
        WHERE user_id = :user_id AND book_id = :book_id
    '''), {'user_id': session['user_id'], 'book_id': book_id}).fetchone()
    
    if existing:
        new_quantity = existing.quantity + quantity
        conn.execute(text('''
            UPDATE cart SET quantity = :quantity
            WHERE user_id = :user_id AND book_id = :book_id
        '''), {'quantity': new_quantity, 'user_id': session['user_id'], 'book_id': book_id})
    else:
        conn.execute(text('''
            INSERT INTO cart (user_id, book_id, quantity)
            VALUES (:user_id, :book_id, :quantity)
        '''), {'user_id': session['user_id'], 'book_id': book_id, 'quantity': quantity})
    
    flash('Item added to cart', 'success')
    return redirect(request.referrer or url_for('books'))

@app.route('/remove-from-cart/<int:book_id>')
@with_db_connection
def remove_from_cart(conn, book_id):
    if 'user_id' not in session:
        flash('Please login to modify your cart', 'warning')
        return redirect(url_for('login'))
    
    conn.execute(text('''
        DELETE FROM cart 
        WHERE user_id = :user_id AND book_id = :book_id
    '''), {'user_id': session['user_id'], 'book_id': book_id})
    
    flash('Item removed from cart', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout')
@with_db_connection
def checkout(conn):
    if 'user_id' not in session:
        flash('Please login to checkout', 'warning')
        return redirect(url_for('login'))
    
    conn.execute(text('''
        DELETE FROM cart 
        WHERE user_id = :user_id
    '''), {'user_id': session['user_id']})
    
    flash('Order placed successfully!', 'success')
    return redirect(url_for('orders'))

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash('Please login to view orders', 'warning')
        return redirect(url_for('login'))
    return render_template('orders.html')

@app.route('/register', methods=['GET', 'POST'])
@with_db_connection
def register(conn):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        try:
            conn.execute(text('''
                INSERT INTO users (username, password, email)
                VALUES (:username, :password, :email)
            '''), {
                'username': username,
                'password': generate_password_hash(password),
                'email': email
            })
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except SQLAlchemyError:
            flash('Username or email already exists', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@with_db_connection
def login(conn):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = conn.execute(text('''
            SELECT * FROM users WHERE username = :username
        '''), {'username': username}).fetchone()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)