import os
import uuid
import sqlite3
from werkzeug.utils import secure_filename
from flask import current_app, g

def get_db():
    """Get a database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE_FILE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close the database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with schema"""
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_image(file):
    """Save an uploaded image file and return the filename"""
    if file and allowed_file(file.filename):
        # Create a unique filename
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # Ensure upload directory exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        return unique_filename
    return None

def format_price(price):
    """Format price to two decimal places"""
    return "{:.2f}".format(price)

def paginate(query_results, page, per_page):
    """Paginate query results"""
    start = (page - 1) * per_page
    end = start + per_page
    
    items = query_results[start:end]
    total = len(query_results)
    
    return {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page  # ceiling division
    }

def search_books(query, filters=None):
    """Search books by query with optional filters"""
    db = get_db()
    cursor = db.cursor()
    
    sql = """
        SELECT b.*, u.name as seller_name
        FROM books b
        JOIN users u ON b.seller_id = u.id
        WHERE (b.title LIKE ? OR b.author LIKE ? OR b.description LIKE ?)
    """
    params = [f"%{query}%", f"%{query}%", f"%{query}%"]
    
    if filters:
        if 'category' in filters and filters['category']:
            sql += " AND b.category = ?"
            params.append(filters['category'])
            
        if 'condition' in filters and filters['condition']:
            sql += " AND b.condition = ?"
            params.append(filters['condition'])
            
        if 'min_price' in filters and filters['min_price'] is not None:
            sql += " AND b.price >= ?"
            params.append(filters['min_price'])
            
        if 'max_price' in filters and filters['max_price'] is not None:
            sql += " AND b.price <= ?"
            params.append(filters['max_price'])
    
    # Only show available books
    sql += " AND b.status = 'available'"
    
    # Order by most recent
    sql += " ORDER BY b.created_at DESC"
    
    cursor.execute(sql, params)
    books = cursor.fetchall()
    
    return [dict(book) for book in books]

def get_book_statistics():
    """Get general statistics about books in the store"""
    db = get_db()
    cursor = db.cursor()
    
    # Total books
    cursor.execute("SELECT COUNT(*) FROM books")
    total_books = cursor.fetchone()[0]
    
    # Available books
    cursor.execute("SELECT COUNT(*) FROM books WHERE status = 'available'")
    available_books = cursor.fetchone()[0]
    
    # Sold books
    cursor.execute("SELECT COUNT(*) FROM books WHERE status = 'sold'")
    sold_books = cursor.fetchone()[0]
    
    # Popular categories
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM books 
        GROUP BY category 
        ORDER BY count DESC 
        LIMIT 5
    """)
    popular_categories = [dict(row) for row in cursor.fetchall()]
    
    # Price ranges
    cursor.execute("""
        SELECT 
            CASE
                WHEN price <= 5 THEN 'Under $5'
                WHEN price <= 10 THEN '$5 - $10'
                WHEN price <= 20 THEN '$10 - $20'
                WHEN price <= 50 THEN '$20 - $50'
                ELSE 'Over $50'
            END as price_range,
            COUNT(*) as count
        FROM books
        GROUP BY price_range
        ORDER BY min(price)
    """)
    price_ranges = [dict(row) for row in cursor.fetchall()]
    
    return {
        'total_books': total_books,
        'available_books': available_books,
        'sold_books': sold_books,
        'popular_categories': popular_categories,
        'price_ranges': price_ranges
    }