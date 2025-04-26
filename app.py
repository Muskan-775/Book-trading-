from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import uuid
from functools import wraps
from datetime import datetime

app = Flask(_name_)
CORS(app, supports_credentials=True)
app.secret_key = os.urandom(24).hex()  # In production, use a stable secret key

# Database setup
def setup_database():
    conn = sqlite3.connect('bookstore.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_admin BOOLEAN DEFAULT 0
    )
    ''')
    
    # Create books table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        price REAL NOT NULL,
        condition TEXT NOT NULL,
        description TEXT,
        category TEXT,
        seller_id INTEGER NOT NULL,
        image_path TEXT,
        status TEXT DEFAULT 'available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (seller_id) REFERENCES users (id)
    )
    ''')
    
    # Create orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create order_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (book_id) REFERENCES books (id)
    )
    ''')
    
    # Create cart table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (book_id) REFERENCES books (id)
    )
    ''')
    
    # Create reviews table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (book_id) REFERENCES books (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Insert some sample data
    # Sample users
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Sample admin user
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
            ("Admin", "admin@bookstore.com", generate_password_hash("admin123"), 1)
        )
        
        # Sample regular users
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("John Doe", "john@example.com", generate_password_hash("password123"))
        )
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Jane Smith", "jane@example.com", generate_password_hash("password123"))
        )
        
        # Sample books
        cursor.execute(
            "INSERT INTO books (title, author, price, condition, description, category, seller_id, image_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("To Kill a Mockingbird", "Harper Lee", 8.99, "Good", "Classic novel in good condition with minimal wear.", "Fiction", 2, "mockingbird.jpg")
        )
        cursor.execute(
            "INSERT INTO books (title, author, price, condition, description, category, seller_id, image_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("1984", "George Orwell", 7.50, "Fair", "Dystopian classic with some highlighting and notes.", "Fiction", 2, "1984.jpg")
        )
        cursor.execute(
            "INSERT INTO books (title, author, price, condition, description, category, seller_id, image_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("Introduction to Algorithms", "Thomas H. Cormen", 45.00, "Like New", "Computer science textbook, barely used.", "Textbook", 3, "algorithms.jpg")
        )
    
    conn.commit()
    conn.close()

# Run database setup
setup_database()

# Authentication middleware
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get database connection
def get_db_connection():
    conn = sqlite3.connect('bookstore.db')
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({"error": "Missing required fields"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if email already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (data['email'],))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Email already registered"}), 409
    
    # Insert new user
    password_hash = generate_password_hash(data['password'])
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (data['name'], data['email'], password_hash)
        )
        conn.commit()
        
        # Get the newly created user
        cursor.execute(
            "SELECT id, name, email FROM users WHERE email = ?",
            (data['email'],)
        )
        user = cursor.fetchone()
        
        # Set session
        session['user_id'] = user['id']
        
        conn.close()
        return jsonify({
            "id": user['id'],
            "name": user['name'],
            "email": user['email']
        }), 201
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing email or password"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find user by email
    cursor.execute("SELECT * FROM users WHERE email = ?", (data['email'],))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not check_password_hash(user['password_hash'], data['password']):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Set session
    session['user_id'] = user['id']
    
    return jsonify({
        "id": user['id'],
        "name": user['name'],
        "email": user['email'],
        "is_admin": user['is_admin']
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, email, is_admin FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": user['id'],
        "name": user['name'],
        "email": user['email'],
        "is_admin": user['is_admin']
    })

@app.route('/api/books', methods=['GET'])
def get_books():
    category = request.args.get('category')
    condition = request.args.get('condition')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    search = request.args.get('search')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT b.*, u.name as seller_name
        FROM books b
        JOIN users u ON b.seller_id = u.id
        WHERE b.status = 'available'
    """
    params = []
    
    if category:
        query += " AND b.category = ?"
        params.append(category)
    
    if condition:
        query += " AND b.condition = ?"
        params.append(condition)
    
    if min_price:
        query += " AND b.price >= ?"
        params.append(float(min_price))
    
    if max_price:
        query += " AND b.price <= ?"
        params.append(float(max_price))
    
    if search:
        query += " AND (b.title LIKE ? OR b.author LIKE ? OR b.description LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    query += " ORDER BY b.created_at DESC"
    
    cursor.execute(query, params)
    books_data = cursor.fetchall()
    conn.close()
    
    books = []
    for book in books_data:
        books.append({
            "id": book['id'],
            "title": book['title'],
            "author": book['author'],
            "price": book['price'],
            "condition": book['condition'],
            "description": book['description'],
            "category": book['category'],
            "seller": book['seller_name'],
            "image_path": book['image_path'],
            "created_at": book['created_at']
        })
    
    return jsonify(books)

@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT b.*, u.name as seller_name
        FROM books b
        JOIN users u ON b.seller_id = u.id
        WHERE b.id = ?
    """, (book_id,))
    
    book = cursor.fetchone()
    
    if not book:
        conn.close()
        return jsonify({"error": "Book not found"}), 404
    
    # Get book reviews
    cursor.execute("""
        SELECT r.*, u.name as reviewer_name
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.book_id = ?
        ORDER BY r.created_at DESC
    """, (book_id,))
    
    reviews_data = cursor.fetchall()
    conn.close()
    
    reviews = []
    for review in reviews_data:
        reviews.append({
            "id": review['id'],
            "rating": review['rating'],
            "comment": review['comment'],
            "user": review['reviewer_name'],
            "created_at": review['created_at']
        })
    
    return jsonify({
        "id": book['id'],
        "title": book['title'],
        "author": book['author'],
        "price": book['price'],
        "condition": book['condition'],
        "description": book['description'],
        "category": book['category'],
        "seller": book['seller_name'],
        "seller_id": book['seller_id'],
        "image_path": book['image_path'],
        "created_at": book['created_at'],
        "reviews": reviews
    })

@app.route('/api/books', methods=['POST'])
@login_required
def add_book():
    data = request.get_json()
    user_id = session.get('user_id')
    
    required_fields = ['title', 'author', 'price', 'condition', 'description', 'category']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # For simplicity, we're not handling image uploads here
        # In a real app, you would process the uploaded image and save it
        image_path = "default_book.jpg"
        
        cursor.execute("""
            INSERT INTO books (title, author, price, condition, description, category, seller_id, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['title'],
            data['author'],
            float(data['price']),
            data['condition'],
            data['description'],
            data['category'],
            user_id,
            image_path
        ))
        
        book_id = cursor.lastrowid
        conn.commit()
        
        # Get the newly added book
        cursor.execute("""
            SELECT b.*, u.name as seller_name
            FROM books b
            JOIN users u ON b.seller_id = u.id
            WHERE b.id = ?
        """, (book_id,))
        
        book = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "id": book['id'],
            "title": book['title'],
            "author": book['author'],
            "price": book['price'],
            "condition": book['condition'],
            "description": book['description'],
            "category": book['category'],
            "seller": book['seller_name'],
            "image_path": book['image_path'],
            "created_at": book['created_at']
        }), 201
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/books/<int:book_id>', methods=['PUT'])
@login_required
def update_book(book_id):
    data = request.get_json()
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if book exists and belongs to the user
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    
    if not book:
        conn.close()
        return jsonify({"error": "Book not found"}), 404
    
    if book['seller_id'] != user_id:
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user or not user['is_admin']:
            conn.close()
            return jsonify({"error": "Not authorized to update this book"}), 403
    
    # Update the book
    try:
        update_fields = []
        update_values = []
        
        for field in ['title', 'author', 'price', 'condition', 'description', 'category', 'status']:
            if field in data:
                update_fields.append(f"{field} = ?")
                
                if field == 'price':
                    update_values.append(float(data[field]))
                else:
                    update_values.append(data[field])
        
        if not update_fields:
            conn.close()
            return jsonify({"error": "No fields to update"}), 400
        
        # Add book_id to values
        update_values.append(book_id)
        
        cursor.execute(
            f"UPDATE books SET {', '.join(update_fields)} WHERE id = ?",
            update_values
        )
        conn.commit()
        
        # Get the updated book
        cursor.execute("""
            SELECT b.*, u.name as seller_name
            FROM books b
            JOIN users u ON b.seller_id = u.id
            WHERE b.id = ?
        """, (book_id,))
        
        updated_book = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "id": updated_book['id'],
            "title": updated_book['title'],
            "author": updated_book['author'],
            "price": updated_book['price'],
            "condition": updated_book['condition'],
            "description": updated_book['description'],
            "category": updated_book['category'],
            "seller": updated_book['seller_name'],
            "status": updated_book['status'],
            "image_path": updated_book['image_path'],
            "created_at": updated_book['created_at']
        })
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/books/<int:book_id>', methods=['DELETE'])
@login_required
def delete_book(book_id):
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if book exists and belongs to the user
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    
    if not book:
        conn.close()
        return jsonify({"error": "Book not found"}), 404
    
    if book['seller_id'] != user_id:
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user or not user['is_admin']:
            conn.close()
            return jsonify({"error": "Not authorized to delete this book"}), 403
    
    try:
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Book deleted successfully"})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/cart', methods=['GET'])
@login_required
def get_cart():
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT ci.*, b.title, b.price, b.image_path
        FROM cart_items ci
        JOIN books b ON ci.book_id = b.id
        WHERE ci.user_id = ?
    """, (user_id,))
    
    cart_items_data = cursor.fetchall()
    conn.close()
    
    cart_items = []
    total = 0
    
    for item in cart_items_data:
        item_total = item['price'] * item['quantity']
        total += item_total
        
        cart_items.append({
            "id": item['id'],
            "book_id": item['book_id'],
            "title": item['title'],
            "price": item['price'],
            "quantity": item['quantity'],
            "image_path": item['image_path'],
            "item_total": item_total
        })
    
    return jsonify({
        "items": cart_items,
        "total": total
    })

@app.route('/api/cart', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json()
    user_id = session.get('user_id')
    
    if not data or not data.get('book_id') or not data.get('quantity'):
        return jsonify({"error": "Missing book_id or quantity"}), 400
    
    book_id = data['book_id']
    quantity = int(data['quantity'])
    
    if quantity <= 0:
        return jsonify({"error": "Quantity must be positive"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if book exists and is available
    cursor.execute("SELECT * FROM books WHERE id = ? AND status = 'available'", (book_id,))
    book = cursor.fetchone()
    
    if not book:
        conn.close()
        return jsonify({"error": "Book not found or not available"}), 404
    
    # Check if book is already in cart
    cursor.execute(
        "SELECT * FROM cart_items WHERE user_id = ? AND book_id = ?",
        (user_id, book_id)
    )
    existing_item = cursor.fetchone()
    
    try:
        if existing_item:
            # Update quantity
            new_quantity = existing_item['quantity'] + quantity
            cursor.execute(
                "UPDATE cart_items SET quantity = ? WHERE id = ?",
                (new_quantity, existing_item['id'])
            )
        else:
            # Add new item
            cursor.execute(
                "INSERT INTO cart_items (user_id, book_id, quantity) VALUES (?, ?, ?)",
                (user_id, book_id, quantity)
            )
        
        conn.commit()
        
        # Get updated cart
        cursor.execute("""
            SELECT ci.*, b.title, b.price, b.image_path
            FROM cart_items ci
            JOIN books b ON ci.book_id = b.id
            WHERE ci.user_id = ?
        """, (user_id,))
        
        cart_items_data = cursor.fetchall()
        conn.close()
        
        cart_items = []
        total = 0
        
        for item in cart_items_data:
            item_total = item['price'] * item['quantity']
            total += item_total
            
            cart_items.append({
                "id": item['id'],
                "book_id": item['book_id'],
                "title": item['title'],
                "price": item['price'],
                "quantity": item['quantity'],
                "image_path": item['image_path'],
                "item_total": item_total
            })
        
        return jsonify({
            "message": "Item added to cart",
            "items": cart_items,
            "total": total
        })
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/cart/<int:item_id>', methods=['PUT'])
@login_required
def update_cart_item(item_id):
    data = request.get_json()
    user_id = session.get('user_id')
    
    if not data or 'quantity' not in data:
        return jsonify({"error": "Missing quantity"}), 400
    
    quantity = int(data['quantity'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if cart item exists and belongs to user
    cursor.execute(
        "SELECT * FROM cart_items WHERE id = ? AND user_id = ?",
        (item_id, user_id)
    )
    item = cursor.fetchone()
    
    if not item:
        conn.close()
        return jsonify({"error": "Cart item not found"}), 404
    
    try:
        if quantity <= 0:
            # Delete item if quantity is 0 or negative
            cursor.execute("DELETE FROM cart_items WHERE id = ?", (item_id,))
        else:
            # Update quantity
            cursor.execute(
                "UPDATE cart_items SET quantity = ? WHERE id = ?",
                (quantity, item_id)
            )
        
        conn.commit()
        
        # Get updated cart
        cursor.execute("""
            SELECT ci.*, b.title, b.price, b.image_path
            FROM cart_items ci
            JOIN books b ON ci.book_id = b.id
            WHERE ci.user_id = ?
        """, (user_id,))
        
        cart_items_data = cursor.fetchall()
        conn.close()
        
        cart_items = []
        total = 0
        
        for item in cart_items_data:
            item_total = item['price'] * item['quantity']
            total += item_total
            
            cart_items.append({
                "id": item['id'],
                "book_id": item['book_id'],
                "title": item['title'],
                "price": item['price'],
                "quantity": item['quantity'],
                "image_path": item['image_path'],
                "item_total": item_total
            })
        
        return jsonify({
            "message": "Cart updated",
            "items": cart_items,
            "total": total
        })
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/cart/<int:item_id>', methods=['DELETE'])
@login_required
def remove_from_cart(item_id):
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if cart item exists and belongs to user
    cursor.execute(
        "SELECT * FROM cart_items WHERE id = ? AND user_id = ?",
        (item_id, user_id)
    )
    item = cursor.fetchone()
    
    if not item:
        conn.close()
        return jsonify({"error": "Cart item not found"}), 404
    
    try:
        cursor.execute("DELETE FROM cart_items WHERE id = ?", (item_id,))
        conn.commit()
        
        # Get updated cart
        cursor.execute("""
            SELECT ci.*, b.title, b.price, b.image_path
            FROM cart_items ci
            JOIN books b ON ci.book_id = b.id
            WHERE ci.user_id = ?
        """, (user_id,))
        
        cart_items_data = cursor.fetchall()
        conn.close()
        
        cart_items = []
        total = 0
        
        for item in cart_items_data:
            item_total = item['price'] * item['quantity']
            total += item_total
            
            cart_items.append({
                "id": item['id'],
                "book_id": item['book_id'],
                "title": item['title'],
                "price": item['price'],
                "quantity": item['quantity'],
                "image_path": item['image_path'],
                "item_total": item_total
            })
        
        return jsonify({
            "message": "Item removed from cart",
            "items": cart_items,
            "total": total
        })
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/checkout', methods=['POST'])
@login_required
def checkout():
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get cart items
    cursor.execute("""
        SELECT ci.*, b.price, b.id as book_id, b.seller_id
        FROM cart_items ci
        JOIN books b ON ci.book_id = b.id
        WHERE ci.user_id = ?
    """, (user_id,))
    
    cart_items = cursor.fetchall()
    
    if not cart_items:
        conn.close()
        return jsonify({"error": "Cart is empty"}), 400
    
    try:
        # Calculate total amount
        total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
        
        # Create order
        cursor.execute(
            "INSERT INTO orders (user_id, total_amount) VALUES (?, ?)",
            (user_id, total_amount)
        )
        order_id = cursor.lastrowid
        
        # Create order items
        for item in cart_items:
            cursor.execute(
                "INSERT INTO order_items (order_id, book_id, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, item['book_id'], item['quantity'], item['price'])
            )
            
            # Update book status to sold
            cursor.execute(
                "UPDATE books SET status = 'sold' WHERE id = ?",
                (item['book_id'],)
            )
        
        # Clear cart
        cursor.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
        
        conn.commit()
        
        # Get order details
        cursor.execute("""
            SELECT o.*, u.name as buyer_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = ?
        """, (order_id,))
        
        order = cursor.fetchone()
        
        # Get order items
        cursor.execute("""
            SELECT oi.*, b.title, b.author
            FROM order_items oi
            JOIN books b ON oi.book_id = b.id
            WHERE oi.order_id = ?
        """, (order_id,))
        
        order_items_data = cursor.fetchall()
        conn.close()
        
        order_items = []
        for item in order_items_data:
            order_items.append({
                "id": item['id'],
                "book_id": item['book_id'],
                "title": item['title'],
                "author": item['author'],
                "quantity": item['quantity'],
                "price": item['price'],
                "item_total": item['quantity'] * item['price']
            })
        
        return jsonify({
            "id": order['id'],
            "total_amount": order['total_amount'],
            "status": order['status'],
            "created_at": order['created_at'],
            "buyer": order['buyer_name'],
            "items": order_items
        }), 201
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders', methods=['GET'])
@login_required
def get_orders():
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user orders
    cursor.execute("""
        SELECT * FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    
    orders_data = cursor.fetchall()
    
    if not orders_data:
        conn.close()
        return jsonify([])
    
    orders = []
    for order in orders_data:
        # Get order items
        cursor.execute("""
            SELECT oi.*, b.title, b.author, b.image_path
            FROM order_items oi
            JOIN books b ON oi.book_id = b.id
            WHERE oi.order_id = ?
        """, (order['id'],))
        
        items_data = cursor.fetchall()
        
        items = []
        for item in items_data:
            items.append({
                "id": item['id'],
                "book_id": item['book_id'],
                "title": item['title'],
                "author": item['author'],
                "quantity": item['quantity'],
                "price": item['price'],
                "image_path": item['image_path'],
                "item_total": item['quantity'] * item['price']
            })
        
        orders.append({
            "id": order['id'],
            "total_amount": order['total_amount'],
            "status": order['status'],
            "created_at": order['created_at'],
            "items": items
        })
    
    conn.close()
    return jsonify(orders)

@app.route('/api/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if order exists and belongs to user
    cursor.execute(
        "SELECT * FROM orders WHERE id = ? AND user_id = ?",
        (order_id, user_id)
    )
    order = cursor.fetchone()
    
    if not order:
        # Check if user is admin
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user or not user['is_admin']:
            conn.close()
            return jsonify({"error": "Order not found"}), 404
        
        # Admin can view any order
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            conn.close()
            return jsonify({"error": "Order not found"}), 404
    
    # Get order items
    cursor.execute("""
        SELECT oi.*, b.title, b.author, b.image_path
        FROM order_items oi
        JOIN books b ON oi.book_id = b.id
        WHERE oi.order_id = ?
    """, (order_id,))
    
    items_data = cursor.fetchall()
    
    # Get buyer info
    cursor.execute("SELECT name, email FROM users WHERE id = ?", (order['user_id'],))
    buyer = cursor.fetchone()
    
    conn.close()
    
    items = []
    for item in items_data:
        items.append({
            "id": item['id'],
            "book_id": item['book_id'],
            "title": item['title'],
            "author": item['author'],
            "quantity": item['quantity'],
            "price": item['price'],
            "image_path": item['image_path'],
            "item_total": item['quantity'] * item['price']
        })
    
    return jsonify({
        "id": order['id'],
        "total_amount": order['total_amount'],
        "status": order['status'],
        "created_at": order['created_at'],
        "buyer": {
            "id": order['user_id'],
            "name": buyer['name'],
            "email": buyer['email']
        },
        "items": items
    })

@app.route('/api/seller/books', methods=['GET'])
@login_required
def get_seller_books():
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get books sold by the user
    cursor.execute("""
        SELECT * FROM books
        WHERE seller_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    
    books_data = cursor.fetchall()
    conn.close()
    
    books = []
    for book in books_data:
        books.append({
            "id": book['id'],
            "title": book['title'],
            "author": book['author'],
            "price": book['price'],
            "condition": book['condition'],
            "description": book['description'],
            "category": book['category'],
            "status": book['status'],
            "image_path": book['image_path'],
            "created_at": book['created_at']
        })
    
    return jsonify(books)

@app.route('/api/books/<int:book_id>/reviews', methods=['POST'])
@login_required
def add_review(book_id):
    data = request.get_json()
    user_id = session.get('user_id')
    
    if not data or 'rating' not in data:
        return jsonify({"error": "Missing rating"}), 400
    
    rating = int(data['rating'])
    comment = data.get('comment', '')
    
    if rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be between 1 and 5"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if book exists
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    
    if not book:
        conn.close()
        return jsonify({"error": "Book not found"}), 404
    
    # Check if user has already reviewed this book
    cursor.execute(
        "SELECT * FROM reviews WHERE book_id = ? AND user_id = ?",
        (book_id, user_id)
    )
    existing_review = cursor.fetchone()
    
    try:
        if existing_review:
            # Update existing review
            cursor.execute(
                "UPDATE reviews SET rating = ?, comment = ? WHERE id = ?",
                (rating, comment, existing_review['id'])
            )
        else:
            # Add new review
            cursor.execute(
                "INSERT INTO reviews (book_id, user_id, rating, comment) VALUES (?, ?, ?, ?)",
                (book_id, user_id, rating, comment)
            )
        
        conn.commit()
        
        # Get the updated review
        if existing_review:
            review_id = existing_review['id']
        else:
            review_id = cursor.lastrowid
        
        cursor.execute("""
            SELECT r.*, u.name as reviewer_name
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
        """, (review_id,))
        
        review = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "id": review['id'],
            "rating": review['rating'],
            "comment": review['comment'],
            "user": review['reviewer_name'],
            "created_at": review['created_at']
        }), 201 if not existing_review else 200
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/books/<int:book_id>/reviews', methods=['GET'])
def get_book_reviews(book_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if book exists
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    
    if not book:
        conn.close()
        return jsonify({"error": "Book not found"}), 404
    
    # Get book reviews
    cursor.execute("""
        SELECT r.*, u.name as reviewer_name
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.book_id = ?
        ORDER BY r.created_at DESC
    """, (book_id,))
    
    reviews_data = cursor.fetchall()
    conn.close()
    
    reviews = []
    for review in reviews_data:
        reviews.append({
            "id": review['id'],
            "rating": review['rating'],
            "comment": review['comment'],
            "user": review['reviewer_name'],
            "created_at": review['created_at']
        })
    
    return jsonify(reviews)

# Admin routes
@app.route('/api/admin/users', methods=['GET'])
@login_required
def get_users():
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user is admin
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user or not user['is_admin']:
        conn.close()
        return jsonify({"error": "Not authorized"}), 403
    
    # Get all users
    cursor.execute("""
        SELECT id, name, email, is_admin, created_at
        FROM users
        ORDER BY created_at DESC
    """)
    
    users_data = cursor.fetchall()
    conn.close()
    
    users = []
    for user in users_data:
        users.append({
            "id": user['id'],
            "name": user['name'],
            "email": user['email'],
            "is_admin": user['is_admin'],
            "created_at": user['created_at']
        })
    
    return jsonify(users)

@app.route('/api/admin/books', methods=['GET'])
@login_required
def admin_get_books():
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user is admin
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user or not user['is_admin']:
        conn.close()
        return jsonify({"error": "Not authorized"}), 403
    
    # Get all books
    cursor.execute("""
        SELECT b.*, u.name as seller_name
        FROM books b
        JOIN users u ON b.seller_id = u.id
        ORDER BY b.created_at DESC
    """)
    
    books_data = cursor.fetchall()
    conn.close()
    
    books = []
    for book in books_data:
        books.append({
            "id": book['id'],
            "title": book['title'],
            "author": book['author'],
            "price": book['price'],
            "condition": book['condition'],
            "description": book['description'],
            "category": book['category'],
            "seller": book['seller_name'],
            "seller_id": book['seller_id'],
            "status": book['status'],
            "image_path": book['image_path'],
            "created_at": book['created_at']
        })
    
    return jsonify(books)

@app.route('/api/admin/orders', methods=['GET'])
@login_required
def admin_get_orders():
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user is admin
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user or not user['is_admin']:
        conn.close()
        return jsonify({"error": "Not authorized"}), 403
    
    # Get all orders
    cursor.execute("""
        SELECT o.*, u.name as buyer_name
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    """)
    
    orders_data = cursor.fetchall()
    
    orders = []
    for order in orders_data:
        # Get order items
        cursor.execute("""
            SELECT oi.*, b.title
            FROM order_items oi
            JOIN books b ON oi.book_id = b.id
            WHERE oi.order_id = ?
        """, (order['id'],))
        
        items_data = cursor.fetchall()
        
        items = []
        for item in items_data:
            items.append({
                "id": item['id'],
                "book_id": item['book_id'],
                "title": item['title'],
                "quantity": item['quantity'],
                "price": item['price']
            })
        
        orders.append({
            "id": order['id'],
            "user_id": order['user_id'],
            "buyer": order['buyer_name'],
            "total_amount": order['total_amount'],
            "status": order['status'],
            "created_at": order['created_at'],
            "items": items
        })
    
    conn.close()
    return jsonify(orders)

@app.route('/api/admin/orders/<int:order_id>', methods=['PUT'])
@login_required
def update_order_status(order_id):
    data = request.get_json()
    user_id = session.get('user_id')
    
    if not data or not data.get('status'):
        return jsonify({"error": "Missing status"}), 400
    
    status = data['status']
    allowed_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    
    if status not in allowed_statuses:
        return jsonify({"error": f"Status must be one of: {', '.join(allowed_statuses)}"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user is admin
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user or not user['is_admin']:
        conn.close()
        return jsonify({"error": "Not authorized"}), 403
    
    # Check if order exists
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    
    if not order:
        conn.close()
        return jsonify({"error": "Order not found"}), 404
    
    try:
        cursor.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id)
        )
        conn.commit()
        
        # Get updated order
        cursor.execute("""
            SELECT o.*, u.name as buyer_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = ?
        """, (order_id,))
        
        updated_order = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "id": updated_order['id'],
            "user_id": updated_order['user_id'],
            "buyer": updated_order['buyer_name'],
            "total_amount": updated_order['total_amount'],
            "status": updated_order['status'],
            "created_at": updated_order['created_at']
        })
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get distinct categories
    cursor.execute("SELECT DISTINCT category FROM books WHERE category IS NOT NULL")
    categories_data = cursor.fetchall()
    conn.close()
    
    categories = [category['category'] for category in categories_data]
    return jsonify(categories)

@app.route('/api/conditions', methods=['GET'])
def get_conditions():
    # Common book conditions
    conditions = ["New", "Like New", "Very Good", "Good", "Fair", "Poor"]
    return jsonify(conditions)

@app.route('/api/stats', methods=['GET'])
@login_required
def get_user_stats():
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Books added by user
    cursor.execute("SELECT COUNT(*) as count FROM books WHERE seller_id = ?", (user_id,))
    books_added = cursor.fetchone()['count']
    
    # Books sold by user
    cursor.execute("SELECT COUNT(*) as count FROM books WHERE seller_id = ? AND status = 'sold'", (user_id,))
    books_sold = cursor.fetchone()['count']
    
    # Books purchased by user
    cursor.execute("""
        SELECT COUNT(*) as count FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.user_id = ?
    """, (user_id,))
    books_purchased = cursor.fetchone()['count']
    
    # Total spent
    cursor.execute("SELECT SUM(total_amount) as total FROM orders WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    total_spent = result['total'] if result['total'] else 0
    
    # Total earned
    cursor.execute("""
        SELECT SUM(b.price) as total FROM books b
        WHERE b.seller_id = ? AND b.status = 'sold'
    """, (user_id,))
    result = cursor.fetchone()
    total_earned = result['total'] if result['total'] else 0
    
    conn.close()
    
    return jsonify({
        "books_added": books_added,
        "books_sold": books_sold,
        "books_purchased": books_purchased,
        "total_spent": total_spent,
        "total_earned": total_earned
    })

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# Main application entry point
if _name_ == '_main_':
    app.run(debug=True)