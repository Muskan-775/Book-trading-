// app.js - Main JavaScript file for Second Hand Book Marketplace

// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initApp();
});

// Global state
const appState = {
    currentUser: null,
    books: [],
    cart: [],
    isLoggedIn: false
};

// Initialize application
function initApp() {
    loadMockData();
    setupEventListeners();
    checkAuthStatus();
    renderBooks();
    updateUIState();
}

// Mock data for development purposes
function loadMockData() {
    appState.books = [
        {
            id: 1,
            title: "To Kill a Mockingbird",
            author: "Harper Lee",
            price: 8.99,
            condition: "Good",
            seller: "bookworm42",
            description: "Classic novel in good condition with minimal wear.",
            imageUrl: "/api/placeholder/150/200",
            category: "Fiction"
        },
        {
            id: 2,
            title: "1984",
            author: "George Orwell",
            price: 7.50,
            condition: "Fair",
            seller: "literaryfan",
            description: "Dystopian classic with some highlighting and notes.",
            imageUrl: "/api/placeholder/150/200",
            category: "Fiction"
        },
        {
            id: 3,
            title: "Introduction to Algorithms",
            author: "Thomas H. Cormen",
            price: 45.00,
            condition: "Like New",
            seller: "csstudent",
            description: "Computer science textbook, barely used.",
            imageUrl: "/api/placeholder/150/200",
            category: "Textbook"
        }
    ];
    
    // Load from localStorage if available
    const storedBooks = localStorage.getItem('books');
    if (storedBooks) {
        try {
            const parsedBooks = JSON.parse(storedBooks);
            if (Array.isArray(parsedBooks)) {
                appState.books = parsedBooks;
            }
        } catch (e) {
            console.error('Error parsing stored books', e);
        }
    }
    
    // Load cart from localStorage if available
    const storedCart = localStorage.getItem('cart');
    if (storedCart) {
        try {
            appState.cart = JSON.parse(storedCart);
        } catch (e) {
            console.error('Error parsing stored cart', e);
        }
    }
}

// Set up event listeners for all interactive elements
function setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Register form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // Add book form
    const addBookForm = document.getElementById('add-book-form');
    if (addBookForm) {
        addBookForm.addEventListener('submit', handleAddBook);
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Search form
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }
    
    // Book filters
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('change', handleFilter);
    }
    
    // Setup buy buttons (delegated event)
    const bookContainer = document.getElementById('book-listings');
    if (bookContainer) {
        bookContainer.addEventListener('click', function(e) {
            if (e.target.classList.contains('buy-btn')) {
                const bookId = parseInt(e.target.dataset.bookId);
                addToCart(bookId);
            }
            
            if (e.target.classList.contains('book-details-btn')) {
                const bookId = parseInt(e.target.dataset.bookId);
                showBookDetails(bookId);
            }
        });
    }
    
    // Cart button
    const cartBtn = document.getElementById('cart-btn');
    if (cartBtn) {
        cartBtn.addEventListener('click', showCart);
    }
    
    // Navigation links
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            navigateTo(this.getAttribute('href').substring(1));
        });
    });
}

// Authentication functions
function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    // In a real app, this would be an API call
    if (email && password) {
        // Mock successful login
        appState.currentUser = {
            id: 1,
            name: email.split('@')[0],
            email: email
        };
        appState.isLoggedIn = true;
        
        // Save to localStorage
        localStorage.setItem('currentUser', JSON.stringify(appState.currentUser));
        
        // Update UI
        updateUIState();
        showMessage('Login successful!', 'success');
        navigateTo('home');
    } else {
        showMessage('Please enter both email and password', 'error');
    }
}

function handleRegister(e) {
    e.preventDefault();
    
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    
    // Validation
    if (!name || !email || !password || !confirmPassword) {
        showMessage('Please fill out all fields', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showMessage('Passwords do not match', 'error');
        return;
    }
    
    // In a real app, this would be an API call to create user
    // Mock successful registration
    appState.currentUser = {
        id: Date.now(),
        name: name,
        email: email
    };
    appState.isLoggedIn = true;
    
    // Save to localStorage
    localStorage.setItem('currentUser', JSON.stringify(appState.currentUser));
    
    // Update UI
    updateUIState();
    showMessage('Registration successful!', 'success');
    navigateTo('home');
}

function handleLogout() {
    appState.currentUser = null;
    appState.isLoggedIn = false;
    
    // Remove from localStorage
    localStorage.removeItem('currentUser');
    
    // Update UI
    updateUIState();
    showMessage('You have been logged out', 'info');
    navigateTo('home');
}

function checkAuthStatus() {
    const storedUser = localStorage.getItem('currentUser');
    if (storedUser) {
        try {
            appState.currentUser = JSON.parse(storedUser);
            appState.isLoggedIn = true;
        } catch (e) {
            console.error('Error parsing stored user', e);
        }
    }
}

// Book-related functions
function handleAddBook(e) {
    e.preventDefault();
    
    if (!appState.isLoggedIn) {
        showMessage('You must be logged in to add books', 'error');
        navigateTo('login');
        return;
    }
    
    const title = document.getElementById('book-title').value;
    const author = document.getElementById('book-author').value;
    const price = parseFloat(document.getElementById('book-price').value);
    const condition = document.getElementById('book-condition').value;
    const description = document.getElementById('book-description').value;
    const category = document.getElementById('book-category').value;
    
    // Validation
    if (!title || !author || isNaN(price) || !condition || !description || !category) {
        showMessage('Please fill out all fields correctly', 'error');
        return;
    }
    
    // Create new book
    const newBook = {
        id: Date.now(),
        title,
        author,
        price,
        condition,
        description,
        category,
        seller: appState.currentUser.name,
        imageUrl: "/api/placeholder/150/200"  // Default placeholder image
    };
    
    // Add to state
    appState.books.push(newBook);
    
    // Save to localStorage
    localStorage.setItem('books', JSON.stringify(appState.books));
    
    // Update UI
    renderBooks();
    showMessage('Book added successfully!', 'success');
    
    // Clear form
    document.getElementById('add-book-form').reset();
    
    // Navigate to home to show all books
    navigateTo('home');
}

function renderBooks(booksToRender = null) {
    const bookListings = document.getElementById('book-listings');
    if (!bookListings) return;
    
    const books = booksToRender || appState.books;
    
    if (books.length === 0) {
        bookListings.innerHTML = '<p class="no-books">No books found!</p>';
        return;
    }
    
    let booksHTML = '';
    
    books.forEach(book => {
        booksHTML += `
            <div class="book-card">
                <img src="${book.imageUrl}" alt="${book.title}" class="book-image">
                <h3>${book.title}</h3>
                <p>by ${book.author}</p>
                <p class="book-price">$${book.price.toFixed(2)}</p>
                <p>Condition: ${book.condition}</p>
                <p>Seller: ${book.seller}</p>
                <div class="book-actions">
                    <button class="book-details-btn" data-book-id="${book.id}">Details</button>
                    <button class="buy-btn" data-book-id="${book.id}">Add to Cart</button>
                </div>
            </div>
        `;
    });
    
    bookListings.innerHTML = booksHTML;
}

function handleSearch(e) {
    e.preventDefault();
    
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    
    if (!searchTerm) {
        renderBooks();
        return;
    }
    
    const filteredBooks = appState.books.filter(book => 
        book.title.toLowerCase().includes(searchTerm) ||
        book.author.toLowerCase().includes(searchTerm) ||
        book.description.toLowerCase().includes(searchTerm)
    );
    
    renderBooks(filteredBooks);
}

function handleFilter() {
    const categoryFilter = document.getElementById('category-filter').value;
    const conditionFilter = document.getElementById('condition-filter').value;
    const priceFilter = document.getElementById('price-filter').value;
    
    let filteredBooks = [...appState.books];
    
    // Apply category filter
    if (categoryFilter && categoryFilter !== 'all') {
        filteredBooks = filteredBooks.filter(book => book.category === categoryFilter);
    }
    
    // Apply condition filter
    if (conditionFilter && conditionFilter !== 'all') {
        filteredBooks = filteredBooks.filter(book => book.condition === conditionFilter);
    }
    
    // Apply price filter
    if (priceFilter) {
        const maxPrice = parseInt(priceFilter);
        filteredBooks = filteredBooks.filter(book => book.price <= maxPrice);
    }
    
    renderBooks(filteredBooks);
}

function showBookDetails(bookId) {
    const book = appState.books.find(b => b.id === bookId);
    
    if (!book) {
        showMessage('Book not found', 'error');
        return;
    }
    
    const modalContent = `
        <div class="book-details-modal">
            <div class="modal-header">
                <h2>${book.title}</h2>
                <button class="close-modal">&times;</button>
            </div>
            <div class="modal-body">
                <div class="book-details-layout">
                    <div class="book-details-image">
                        <img src="${book.imageUrl}" alt="${book.title}">
                    </div>
                    <div class="book-details-info">
                        <p><strong>Author:</strong> ${book.author}</p>
                        <p><strong>Price:</strong> $${book.price.toFixed(2)}</p>
                        <p><strong>Condition:</strong> ${book.condition}</p>
                        <p><strong>Category:</strong> ${book.category}</p>
                        <p><strong>Seller:</strong> ${book.seller}</p>
                        <p><strong>Description:</strong> ${book.description}</p>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="buy-btn" data-book-id="${book.id}">Add to Cart</button>
            </div>
        </div>
    `;
    
    showModal(modalContent);
    
    // Add event listeners for modal
    document.querySelector('.close-modal').addEventListener('click', closeModal);
    document.querySelector('.modal-footer .buy-btn').addEventListener('click', function() {
        addToCart(bookId);
        closeModal();
    });
}

// Cart functions
function addToCart(bookId) {
    if (!appState.isLoggedIn) {
        showMessage('Please login to add items to cart', 'error');
        navigateTo('login');
        return;
    }
    
    const book = appState.books.find(b => b.id === bookId);
    
    if (!book) {
        showMessage('Book not found', 'error');
        return;
    }
    
    // Check if book is already in cart
    const existingItem = appState.cart.find(item => item.id === bookId);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        appState.cart.push({
            id: book.id,
            title: book.title,
            price: book.price,
            quantity: 1
        });
    }
    
    // Save to localStorage
    localStorage.setItem('cart', JSON.stringify(appState.cart));
    
    updateCartCount();
    showMessage("${book.title}" added to cart, 'success');
}

function updateCartCount() {
    const cartCount = document.getElementById('cart-count');
    if (!cartCount) return;
    
    const totalItems = appState.cart.reduce((total, item) => total + item.quantity, 0);
    cartCount.textContent = totalItems;
    
    if (totalItems > 0) {
        cartCount.classList.add('has-items');
    } else {
        cartCount.classList.remove('has-items');
    }
}

function showCart() {
    if (appState.cart.length === 0) {
        showMessage('Your cart is empty', 'info');
        return;
    }
    
    let cartHTML = `
        <div class="cart-modal">
            <div class="modal-header">
                <h2>Your Cart</h2>
                <button class="close-modal">&times;</button>
            </div>
            <div class="modal-body">
                <table class="cart-table">
                    <thead>
                        <tr>
                            <th>Book</th>
                            <th>Price</th>
                            <th>Quantity</th>
                            <th>Total</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    let totalAmount = 0;
    
    appState.cart.forEach(item => {
        const itemTotal = item.price * item.quantity;
        totalAmount += itemTotal;
        
        cartHTML += `
            <tr>
                <td>${item.title}</td>
                <td>$${item.price.toFixed(2)}</td>
                <td>
                    <button class="quantity-btn minus" data-book-id="${item.id}">-</button>
                    <span>${item.quantity}</span>
                    <button class="quantity-btn plus" data-book-id="${item.id}">+</button>
                </td>
                <td>$${itemTotal.toFixed(2)}</td>
                <td>
                    <button class="remove-btn" data-book-id="${item.id}">Remove</button>
                </td>
            </tr>
        `;
    });
    
    cartHTML += `
                    </tbody>
                </table>
                <div class="cart-summary">
                    <p class="cart-total">Total: $${totalAmount.toFixed(2)}</p>
                </div>
            </div>
            <div class="modal-footer">
                <button class="checkout-btn">Proceed to Checkout</button>
            </div>
        </div>
    `;
    
    showModal(cartHTML);
    
    // Add event listeners for modal
    document.querySelector('.close-modal').addEventListener('click', closeModal);
    
    // Add event listeners for quantity and remove buttons
    document.querySelectorAll('.quantity-btn.minus').forEach(btn => {
        btn.addEventListener('click', function() {
            updateCartItemQuantity(parseInt(this.dataset.bookId), -1);
        });
    });
    
    document.querySelectorAll('.quantity-btn.plus').forEach(btn => {
        btn.addEventListener('click', function() {
            updateCartItemQuantity(parseInt(this.dataset.bookId), 1);
        });
    });
    
    document.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            removeFromCart(parseInt(this.dataset.bookId));
        });
    });
    
    document.querySelector('.checkout-btn').addEventListener('click', handleCheckout);
}

function updateCartItemQuantity(bookId, change) {
    const item = appState.cart.find(item => item.id === bookId);
    
    if (!item) return;
    
    item.quantity += change;
    
    if (item.quantity <= 0) {
        removeFromCart(bookId);
    } else {
        // Save to localStorage
        localStorage.setItem('cart', JSON.stringify(appState.cart));
        
        // Update UI
        showCart(); // Refresh cart view
    }
    
    updateCartCount();
}

function removeFromCart(bookId) {
    appState.cart = appState.cart.filter(item => item.id !== bookId);
    
    // Save to localStorage
    localStorage.setItem('cart', JSON.stringify(appState.cart));
    
    // Update UI
    updateCartCount();
    
    if (appState.cart.length === 0) {
        closeModal();
        showMessage('Your cart is now empty', 'info');
    } else {
        showCart(); // Refresh cart view
    }
}

function handleCheckout() {
    if (!appState.isLoggedIn) {
        showMessage('Please login to checkout', 'error');
        closeModal();
        navigateTo('login');
        return;
    }
    
    if (appState.cart.length === 0) {
        showMessage('Your cart is empty', 'error');
        closeModal();
        return;
    }
    
    // In a real app, this would redirect to a checkout page or show a checkout form
    showMessage('Proceeding to checkout...', 'info');
    
    // Mock successful checkout
    setTimeout(() => {
        // Clear cart
        appState.cart = [];
        localStorage.removeItem('cart');
        updateCartCount();
        
        closeModal();
        showMessage('Order placed successfully!', 'success');
    }, 1500);
}

// UI helper functions
function updateUIState() {
    // Update auth-dependent elements
    const authElements = document.querySelectorAll('.auth-dependent');
    const guestElements = document.querySelectorAll('.guest-only');
    
    if (appState.isLoggedIn) {
        // Show elements that require authentication
        authElements.forEach(el => el.classList.remove('hidden'));
        // Hide elements for guests only
        guestElements.forEach(el => el.classList.add('hidden'));
        
        // Update user name display
        const userNameElements = document.querySelectorAll('.user-name');
        userNameElements.forEach(el => {
            el.textContent = appState.currentUser.name;
        });
    } else {
        // Hide elements that require authentication
        authElements.forEach(el => el.classList.add('hidden'));
        // Show elements for guests only
        guestElements.forEach(el => el.classList.remove('hidden'));
    }
    
    // Update cart count
    updateCartCount();
}

function showMessage(message, type = 'info') {
    const messageContainer = document.getElementById('message-container');
    if (!messageContainer) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = message ${type};
    messageElement.textContent = message;
    
    messageContainer.appendChild(messageElement);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        messageElement.classList.add('fade-out');
        setTimeout(() => {
            messageContainer.removeChild(messageElement);
        }, 500);
    }, 3000);
}

function showModal(content) {
    let modalContainer = document.getElementById('modal-container');
    
    if (!modalContainer) {
        modalContainer = document.createElement('div');
        modalContainer.id = 'modal-container';
        document.body.appendChild(modalContainer);
    }
    
    modalContainer.innerHTML = `
        <div class="modal-overlay">
            <div class="modal">
                ${content}
            </div>
        </div>
    `;
    
    modalContainer.classList.add('active');
    document.body.classList.add('modal-open');
}

function closeModal() {
    const modalContainer = document.getElementById('modal-container');
    if (!modalContainer) return;
    
    modalContainer.classList.remove('active');
    document.body.classList.remove('modal-open');
}

function navigateTo(page) {
    // Hide all pages
    const pages = document.querySelectorAll('.page');
    pages.forEach(p => p.classList.add('hidden'));
    
    // Show the selected page
    const selectedPage = document.getElementById(${page}-page);
    if (selectedPage) {
        selectedPage.classList.remove('hidden');
    }
    
    // Update active nav link
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === #${page}) {
            link.classList.add('active');
        }
    });
    
    // Scroll to top
    window.scrollTo(0, 0);
}

// Initialize popstate event to handle browser back/forward navigation
window.addEventListener('popstate', function(event) {
    if (event.state && event.state.page) {
        navigateTo(event.state.page);
    }
});