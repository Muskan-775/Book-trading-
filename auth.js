/**
 * BookSwap Authentication JavaScript
 * Handles login functionality, social login, and form validation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the login form
    initializeLoginForm();
    
    // Initialize social login buttons
    initializeSocialLogin();
    
    // Initialize password toggle functionality
    initializePasswordToggle();
});

// Initialize login form functionality
function initializeLoginForm() {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form values
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const rememberMe = document.getElementById('remember').checked;
            
            // Validate form inputs
            if (!validateEmail(email)) {
                showError('Please enter a valid email address');
                return;
            }
            
            if (password.length < 6) {
                showError('Password must be at least 6 characters long');
                return;
            }
            
            // Show loading state
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
            submitBtn.disabled = true;
            
            // If validation passes, prepare the form data
            const formData = {
                email: email,
                password: password,
                rememberMe: rememberMe
            };
            
            // Send login request to server (simulated here)
            authenticateUser(formData)
                .then(response => {
                    // Handle successful login
                    showSuccess('Login successful!');
                    
                    // Store auth token if remember me is checked
                    if (rememberMe && response.token) {
                        localStorage.setItem('authToken', response.token);
                    } else if (response.token) {
                        sessionStorage.setItem('authToken', response.token);
                    }
                    
                    // Redirect to dashboard
                    setTimeout(() => {
                        window.location.href = 'dashboard.html';
                    }, 1500);
                })
                .catch(error => {
                    // Handle login error
                    showError(error.message || 'Login failed. Please check your credentials.');
                })
                .finally(() => {
                    // Reset button state
                    submitBtn.innerHTML = originalBtnText;
                    submitBtn.disabled = false;
                });
        });
    }
}

// Initialize social login buttons
function initializeSocialLogin() {
    const googleLoginBtn = document.querySelector('.social-btn.google');
    const facebookLoginBtn = document.querySelector('.social-btn.facebook');
    
    if (googleLoginBtn) {
        googleLoginBtn.addEventListener('click', handleGoogleLogin);
    }
    
    if (facebookLoginBtn) {
        facebookLoginBtn.addEventListener('click', handleFacebookLogin);
    }
}

// Google Login Handler
function handleGoogleLogin() {
    // Disable the button and show loading state
    const googleBtn = document.querySelector('.social-btn.google');
    const originalText = googleBtn.innerHTML;
    googleBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
    googleBtn.disabled = true;
    
    // Load the Google Sign-In API script if it's not already loaded
    if (!window.gapi) {
        loadGoogleAPI()
            .then(() => {
                initializeGoogleSignIn();
            })
            .catch(error => {
                showError('Failed to load Google Sign-In. Please try again later.');
                console.error('Google API loading error:', error);
                // Reset button
                googleBtn.innerHTML = originalText;
                googleBtn.disabled = false;
            });
    } else {
        // If Google API is already loaded, initialize sign-in
        initializeGoogleSignIn();
    }
}

// Load Google API
function loadGoogleAPI() {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://apis.google.com/js/platform.js';
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// Initialize Google Sign-In
function initializeGoogleSignIn() {
    // Replace with your Google Client ID
    const CLIENT_ID = 'YOUR_GOOGLE_CLIENT_ID';
    
    gapi.load('auth2', () => {
        gapi.auth2.init({
            client_id: CLIENT_ID,
            scope: 'email profile'
        }).then(auth2 => {
            // Reset the Google button to its original state
            const googleBtn = document.querySelector('.social-btn.google');
            googleBtn.innerHTML = '<i class="fab fa-google"></i> Login with Google';
            googleBtn.disabled = false;
            
            // Start the Google OAuth flow
            auth2.signIn().then(googleUser => {
                // Get user profile information
                const profile = googleUser.getBasicProfile();
                const id_token = googleUser.getAuthResponse().id_token;
                
                // Process the user data
                const userData = {
                    id: profile.getId(),
                    name: profile.getName(),
                    email: profile.getEmail(),
                    imageUrl: profile.getImageUrl(),
                    token: id_token,
                    provider: 'google'
                };
                
                // Send the token to your server for verification
                verifyGoogleToken(userData);
                
            }).catch(error => {
                if (error.error !== 'popup_closed_by_user') {
                    showError('Google sign-in error: ' + (error.error || 'Unknown error'));
                    console.error('Google sign-in error:', error);
                }
            });
        }).catch(error => {
            // Reset button
            const googleBtn = document.querySelector('.social-btn.google');
            googleBtn.innerHTML = '<i class="fab fa-google"></i> Login with Google';
            googleBtn.disabled = false;
            
            showError('Failed to initialize Google Sign-In. Please try again later.');
            console.error('Google API init error:', error);
        });
    });
}

// Verify Google token with server
function verifyGoogleToken(userData) {
    // Show loading state
    const googleBtn = document.querySelector('.social-btn.google');
    googleBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';
    googleBtn.disabled = true;
    
    // In a real app, you would send this data to your server
    // For demonstration purposes, we'll simulate a server response
    
    // Simulate API call
    setTimeout(() => {
        console.log('Google user data:', userData);
        
        // Simulate successful authentication
        const authResponse = {
            success: true,
            user: {
                id: userData.id,
                name: userData.name,
                email: userData.email,
                profileImage: userData.imageUrl
            },
            token: 'google_auth_' + Math.random().toString(36).substring(2)
        };
        
        // Store auth token in session storage
        sessionStorage.setItem('authToken', authResponse.token);
        
        // Store user basic info
        sessionStorage.setItem('user', JSON.stringify(authResponse.user));
        
        // Show success message
        showSuccess('Successfully signed in with Google!');
        
        // Redirect to dashboard after short delay
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 1500);
    }, 1000);
}

// Facebook Login Handler
function handleFacebookLogin() {
    // Disable the button and show loading state
    const facebookBtn = document.querySelector('.social-btn.facebook');
    const originalText = facebookBtn.innerHTML;
    facebookBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
    facebookBtn.disabled = true;
    
    // Load the Facebook SDK if it's not already loaded
    if (!window.FB) {
        loadFacebookSDK()
            .then(() => {
                initializeFacebookLogin();
            })
            .catch(error => {
                showError('Failed to load Facebook Login. Please try again later.');
                console.error('Facebook SDK loading error:', error);
                // Reset button
                facebookBtn.innerHTML = originalText;
                facebookBtn.disabled = false;
            });
    } else {
        // If Facebook SDK is already loaded, initialize login
        initializeFacebookLogin();
    }
}

// Load Facebook SDK
function loadFacebookSDK() {
    return new Promise((resolve, reject) => {
        // Add Facebook SDK
        window.fbAsyncInit = function() {
            FB.init({
                appId: 'YOUR_FACEBOOK_APP_ID',
                cookie: true,
                xfbml: true,
                version: 'v17.0'
            });
            
            resolve();
        };
        
        // Load the SDK asynchronously
        (function(d, s, id) {
            var js, fjs = d.getElementsByTagName(s)[0];
            if (d.getElementById(id)) return;
            js = d.createElement(s); js.id = id;
            js.src = "https://connect.facebook.net/en_US/sdk.js";
            js.onload = resolve;
            js.onerror = reject;
            fjs.parentNode.insertBefore(js, fjs);
        }(document, 'script', 'facebook-jssdk'));
    });
}

// Initialize Facebook Login
function initializeFacebookLogin() {
    // Reset the Facebook button to its original state
    const facebookBtn = document.querySelector('.social-btn.facebook');
    facebookBtn.innerHTML = '<i class="fab fa-facebook-f"></i> Login with Facebook';
    facebookBtn.disabled = false;
    
    FB.login(function(response) {
        if (response.status === 'connected') {
            // Show loading state
            facebookBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';
            facebookBtn.disabled = true;
            
            // Get user data from Facebook
            FB.api('/me', {fields: 'id,name,email,picture'}, function(userData) {
                // Add the access token to user data
                userData.accessToken = response.authResponse.accessToken;
                userData.provider = 'facebook';
                
                // User profile picture
                if (userData.picture && userData.picture.data) {
                    userData.imageUrl = userData.picture.data.url;
                }
                
                // Send the data to your server for verification
                verifyFacebookToken(userData);
            });
        } else {
            if (response.status !== 'not_authorized') {
                showError('Facebook login failed or was cancelled.');
                console.error('Facebook login error:', response);
            }
        }
    }, {scope: 'email,public_profile'});
}

// Verify Facebook token with server
function verifyFacebookToken(userData) {
    // In a real app, you would send this data to your server
    // For demonstration purposes, we'll simulate a server response
    
    // Simulate API call
    setTimeout(() => {
        console.log('Facebook user data:', userData);
        
        // Simulate successful authentication
        const authResponse = {
            success: true,
            user: {
                id: userData.id,
                name: userData.name,
                email: userData.email,
                profileImage: userData.imageUrl || null
            },
            token: 'facebook_auth_' + Math.random().toString(36).substring(2)
        };
        
        // Store auth token in session storage
        sessionStorage.setItem('authToken', authResponse.token);
        
        // Store user basic info
        sessionStorage.setItem('user', JSON.stringify(authResponse.user));
        
        // Show success message
        showSuccess('Successfully signed in with Facebook!');
        
        // Redirect to dashboard after short delay
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 1500);
    }, 1000);
}

// Traditional email/password authentication (simulated)
function authenticateUser(userData) {
    return new Promise((resolve, reject) => {
        // In a real app, you would send this data to your server via fetch or XMLHttpRequest
        // Here we'll simulate a server response
        
        // Simulate API call with timeout
        setTimeout(() => {
            // Check if this is a valid user (in real app, this happens on server)
            // For demo, let's assume test@example.com with password "password123" is valid
            if (userData.email === 'test@example.com' && userData.password === 'password123') {
                // Successful login
                resolve({
                    success: true,
                    user: {
                        id: '12345',
                        name: 'Test User',
                        email: userData.email
                    },
                    token: 'auth_' + Math.random().toString(36).substring(2)
                });
            } else {
                // Failed login
                reject({
                    success: false,
                    message: 'Invalid email or password'
                });
            }
        }, 1000);
    });
}

// Initialize password toggle visibility
function initializePasswordToggle() {
    const toggleButton = document.querySelector('.toggle-password');
    const passwordInput = document.getElementById('password');
    
    if (toggleButton && passwordInput) {
        toggleButton.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // Toggle the eye / eye-slash icon
            const icon = this.querySelector('i');
            icon.classList.toggle('fa-eye');
            icon.classList.toggle('fa-eye-slash');
        });
    }
}

// Utility function to validate email
function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

// Show error message
function showError(message) {
    // Check if error container exists, otherwise create it
    let errorContainer = document.querySelector('.auth-message.error');
    
    if (!errorContainer) {
        errorContainer = document.createElement('div');
        errorContainer.className = 'auth-message error';
        
        // Insert it after the form heading
        const formContainer = document.querySelector('.auth-form-container');
        formContainer.insertBefore(errorContainer, formContainer.querySelector('form'));
    }
    
    errorContainer.textContent = message;
    errorContainer.style.display = 'block';
    
    // Hide the error after 5 seconds
    setTimeout(() => {
        errorContainer.style.display = 'none';
    }, 5000);
}

// Show success message
function showSuccess(message) {
    // Check if success container exists, otherwise create it
    let successContainer = document.querySelector('.auth-message.success');
    
    if (!successContainer) {
        successContainer = document.createElement('div');
        successContainer.className = 'auth-message success';
        
        // Insert it after the form heading
        const formContainer = document.querySelector('.auth-form-container');
        formContainer.insertBefore(successContainer, formContainer.querySelector('form'));
    }
    
    successContainer.textContent = message;
    successContainer.style.display = 'block';
}

// Check if user is already logged in
function checkAuthStatus() {
    const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    
    if (token) {
        // User is already logged in, redirect to dashboard
        window.location.href = 'dashboard.html';
    }
}

// Call this function when the page loads
// Uncomment if you want to redirect logged-in users away from the login page
// checkAuthStatus();