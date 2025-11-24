// static/js/auth.js - FIXED VERSION

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('access_token');
        this.user = null;
        this.init();
    }

    init() {
        // Check auth status on page load
        this.checkAuthStatus();

        // Setup logout button if exists
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
    }

    async checkAuthStatus() {
        try {
            const response = await this.makeAuthenticatedRequest('/auth/status');
            if (response && response.authenticated) {
                this.user = response.user;
                this.token = localStorage.getItem('access_token');
                this.updateUIForLoggedIn();
            } else {
                this.updateUIForLoggedOut();
            }
        } catch (error) {
            console.error('Auth status check failed:', error);
            this.updateUIForLoggedOut();
        }
    }

    async login(email, password) {
        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Login failed');
            }

            const data = await response.json();
            this.token = data.access_token;
            localStorage.setItem('access_token', this.token);

            // Store user info if available
            if (data.user) {
                this.user = data.user;
            }

            // Get user profile
            await this.checkAuthStatus();

            return { success: true, data };

        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: error.message };
        }
    }

    async signup(name, email, password) {
        try {
            const response = await fetch('/auth/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, email, password })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Signup failed');
            }

            const data = await response.json();
            // Signup response may or may not include token
            if (data.access_token) {
                this.token = data.access_token;
                localStorage.setItem('access_token', this.token);
            }

            // Get user profile
            await this.checkAuthStatus();

            return { success: true, data };

        } catch (error) {
            console.error('Signup error:', error);
            return { success: false, error: error.message };
        }
    }

    async logout() {
        try {
            // Call logout endpoint to revoke token on server
            await this.makeAuthenticatedRequest('/auth/logout', {
                method: 'POST'
            });
        } catch (error) {
            console.error('Logout request failed (continuing with local cleanup):', error);
        } finally {
            // Always clear local state
            this.token = null;
            this.user = null;
            localStorage.removeItem('access_token');
            this.updateUIForLoggedOut();

            // Redirect to login page
            window.location.href = '/static/login.html';
        }
    }

    async makeAuthenticatedRequest(url, options = {}) {
        const token = this.token || localStorage.getItem('access_token');

        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(url, {
            ...options,
            headers,
            credentials: 'include'
        });

        if (response.status === 401) {
            // Token expired or invalid
            this.logout();
            throw new Error('Authentication required');
        }

        if (!response.ok) {
            // Try to get error message from response
            try {
                const errorData = await response.json();
                const errorMsg = errorData.detail || `HTTP error! status: ${response.status}`;
                throw new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
            } catch (e) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        }

        return await response.json();
    }

    updateUIForLoggedIn() {
        // Hide login/signup buttons
        const loginBtn = document.getElementById('login-btn');
        const signupBtn = document.getElementById('signup-btn');
        const logoutBtn = document.getElementById('logoutBtn');
        const loggedInName = document.getElementById('loggedInName');

        if (loginBtn) loginBtn.style.display = 'none';
        if (signupBtn) signupBtn.style.display = 'none';

        // Show user info
        if (logoutBtn) logoutBtn.style.display = 'block';
        if (loggedInName && this.user) {
            loggedInName.style.display = 'inline-block';
            loggedInName.textContent = this.user.name;
        }

        // Hide login prompt
        const loginPrompt = document.getElementById('loginPrompt');
        if (loginPrompt) loginPrompt.style.display = 'none';

        this.enableProtectedFeatures();
    }

    updateUIForLoggedOut() {
        // Show login/signup buttons
        const loginBtn = document.getElementById('login-btn');
        const signupBtn = document.getElementById('signup-btn');
        const logoutBtn = document.getElementById('logoutBtn');
        const loggedInName = document.getElementById('loggedInName');

        if (loginBtn) loginBtn.style.display = 'block';
        if (signupBtn) signupBtn.style.display = 'block';

        // Hide user info
        if (logoutBtn) logoutBtn.style.display = 'none';
        if (loggedInName) loggedInName.style.display = 'none';

        // Show login prompt
        const loginPrompt = document.getElementById('loginPrompt');
        if (loginPrompt) loginPrompt.style.display = 'flex';

        this.disableProtectedFeatures();
    }

    enableProtectedFeatures() {
        // Enable all voice control buttons
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const resetBtn = document.getElementById('resetBtn');
        const endCallBtn = document.getElementById('endCallBtn');

        // Show and enable buttons
        const buttons = [startBtn, stopBtn, pauseBtn, resetBtn, endCallBtn];
        buttons.forEach(btn => {
            if (btn) {
                btn.disabled = false;
                btn.style.pointerEvents = 'auto';
                btn.style.opacity = '1';
                btn.style.display = 'inline-flex'; // Show buttons
                // Remove the click blocker
                btn.removeEventListener('click', this.blockClick, true);
            }
        });

        if (startBtn) startBtn.title = 'Start Listening';
        if (stopBtn) {
            stopBtn.disabled = true; // Initially disabled until listening starts
            stopBtn.title = 'Stop Listening';
        }
        if (pauseBtn) {
            pauseBtn.disabled = true; // Initially disabled
            pauseBtn.title = 'Pause Conversation';
        }
        if (resetBtn) resetBtn.title = 'Reset Conversation';
        if (endCallBtn) endCallBtn.title = 'End Call';

        // Hide the login required message
        const loginMsg = document.getElementById('loginRequiredMsg');
        if (loginMsg) {
            loginMsg.style.display = 'none';
        }
    }

    disableProtectedFeatures() {
        // Disable all voice control buttons
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const resetBtn = document.getElementById('resetBtn');
        const endCallBtn = document.getElementById('endCallBtn');

        // Hide buttons and add click blocker to prevent any interaction
        const buttons = [startBtn, stopBtn, pauseBtn, resetBtn, endCallBtn];
        buttons.forEach(btn => {
            if (btn) {
                btn.disabled = true;
                btn.style.pointerEvents = 'none';
                btn.style.opacity = '0.3';
                btn.style.display = 'none'; // Hide buttons completely
                btn.title = 'Please login to use voice coach';
                // Add click blocker as extra safety
                btn.addEventListener('click', this.blockClick, true);
            }
        });

        // Show the login required message
        const loginMsg = document.getElementById('loginRequiredMsg');
        if (loginMsg) {
            loginMsg.style.display = 'block';
        }
    }

    // Click blocker function
    blockClick(e) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        return false;
    }

    isAuthenticated() {
        return !!this.token && !!this.user;
    }

    getUser() {
        return this.user;
    }

    getToken() {
        return this.token;
    }
}

// Global auth instance
window.authManager = new AuthManager();