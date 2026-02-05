/* ==========================================
   STUDENT DASHBOARD.JS
   ========================================== */

/* ==========================================
   INITIALIZATION
   ========================================== */

document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
    initNavigation();
    ensureSidebarState();
    setTimeout(animateProgressBars, 300);
});

/* ==========================================
   SIDEBAR FUNCTIONALITY
   ========================================== */

function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mobileToggle = document.getElementById('mobileMenuToggle');
    const closeBtn = document.getElementById('closeSidebarBtn');
    const overlay = document.getElementById('sidebarOverlay');
    const menuItems = document.querySelectorAll('.menu-item');

    if (mobileToggle) {
        mobileToggle.addEventListener('click', toggleSidebar);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', closeSidebar);
    }

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // Close sidebar on menu item click for mobile
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            if (window.innerWidth < 768) {
                closeSidebar();
            }
        });
    });

    // Close sidebar on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeSidebar();
        }
    });

    // Handle window resize
    window.addEventListener('resize', ensureSidebarState);
}

function toggleSidebar() {
    // Do not toggle on desktop where sidebar is permanently visible
    if (window.innerWidth >= 768) return;

    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (sidebar && overlay) {
        const isOpen = sidebar.classList.toggle('open');
        overlay.classList.toggle('active', isOpen);
        document.body.style.overflow = isOpen ? 'hidden' : '';
    }
}

function closeSidebar() {
    // No-op on desktop where sidebar is permanent
    if (window.innerWidth >= 768) return;

    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('active');
    document.body.style.overflow = '';
}

function ensureSidebarState() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (window.innerWidth >= 768) {
        // Desktop: sidebar always visible
        if (sidebar) sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
        document.body.style.overflow = '';
    } else {
        // Mobile: ensure sidebar is closed by default
        if (sidebar) sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
        document.body.style.overflow = '';
    }
}

/* ==========================================
   NAVIGATION FUNCTIONALITY
   ========================================== */

function initNavigation() {
    const menuItems = document.querySelectorAll('.menu-item');
    const actionButtons = document.querySelectorAll('.action-btn');
    
    // Handle menu item clicks
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            const page = this.getAttribute('data-page');
            if (page) {
                navigateToPage(page);
                setActiveMenuItem(this);
            }
        });
    });

    // Handle action button clicks
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const page = this.getAttribute('data-page');
            if (page) {
                navigateToPage(page);
                const menuItem = document.querySelector(`.menu-item[data-page="${page}"]`);
                if (menuItem) {
                    setActiveMenuItem(menuItem);
                }
            }
        });
    });
}

function navigateToPage(pageName) {
    // Hide all sections
    const allSections = document.querySelectorAll('.dashboard-main');
    allSections.forEach(section => {
        section.style.display = 'none';
    });

    // Page mapping
    const pageMap = {
        'dashboard': 'dashboardMain',
        'evaluate': 'evaluateMain',
        'subjects': 'subjectsMain',
        'history': 'historyMain',
        'announcements': 'announcementsMain',
        'profile': 'profileMain'
    };

    // Show selected section
    const sectionId = pageMap[pageName];
    if (sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.style.display = 'block';
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }
}

function setActiveMenuItem(activeItem) {
    // Remove active class from all items
    const allItems = document.querySelectorAll('.menu-item');
    allItems.forEach(item => {
        item.classList.remove('active');
    });
    
    // Add active class to clicked item
    if (activeItem) {
        activeItem.classList.add('active');
    }
}

/* ==========================================
   LEGACY NAVIGATION FUNCTIONS (for compatibility)
   ========================================== */

function backToDashboard() {
    navigateToPage('dashboard');
    const menuItem = document.querySelector('.menu-item[data-page="dashboard"]');
    if (menuItem) setActiveMenuItem(menuItem);
}

function openEvaluateMain() {
    navigateToPage('evaluate');
    const menuItem = document.querySelector('.menu-item[data-page="evaluate"]');
    if (menuItem) setActiveMenuItem(menuItem);
}

function openMySubjects() {
    navigateToPage('subjects');
    const menuItem = document.querySelector('.menu-item[data-page="subjects"]');
    if (menuItem) setActiveMenuItem(menuItem);
}

function openHistory() {
    navigateToPage('history');
    const menuItem = document.querySelector('.menu-item[data-page="history"]');
    if (menuItem) setActiveMenuItem(menuItem);
}

function openAnnouncements() {
    navigateToPage('announcements');
    const menuItem = document.querySelector('.menu-item[data-page="announcements"]');
    if (menuItem) setActiveMenuItem(menuItem);
}

function openProfile() {
    navigateToPage('profile');
    const menuItem = document.querySelector('.menu-item[data-page="profile"]');
    if (menuItem) setActiveMenuItem(menuItem);
}

/* ==========================================
   WELCOME BANNER TYPING EFFECT
   ========================================== */

function initWelcomeBanner(userName) {
    // Set today's date
    setTodaysDate();
    
    // Initialize typing effect
    const text = `Welcome back, ${userName}!`;
    const typedElement = document.getElementById('welcomeTyped');
    
    if (typedElement) {
        typeWriter(text, typedElement, 0);
    }
}

function setTodaysDate() {
    const dateElement = document.getElementById('todayDate');
    if (dateElement) {
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        };
        const today = new Date();
        dateElement.textContent = today.toLocaleDateString('en-US', options);
    }
}

function typeWriter(text, element, index) {
    if (index < text.length) {
        element.textContent += text.charAt(index);
        setTimeout(() => typeWriter(text, element, index + 1), 50);
    }
}

/* ==========================================
   MODAL FUNCTIONS
   ========================================== */

function openEvaluationModal(button) {
    const evalId = button.getAttribute('data-eval-id');
    const modal = document.getElementById('modal-' + evalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        trapFocus(modal);
    }
}

function closeEvaluationModal(evalId) {
    const modal = document.getElementById('modal-' + evalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

function closeAllModals() {
    const modals = document.querySelectorAll('.evaluation-modal');
    modals.forEach(modal => {
        modal.style.display = 'none';
    });
    document.body.style.overflow = 'auto';
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal-overlay')) {
        const modal = event.target.closest('.evaluation-modal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }
});

/* ==========================================
   ACCESSIBILITY - FOCUS TRAP
   ========================================== */

function trapFocus(element) {
    const focusableElements = element.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    element.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                if (document.activeElement === firstFocusable) {
                    lastFocusable.focus();
                    e.preventDefault();
                }
            } else {
                if (document.activeElement === lastFocusable) {
                    firstFocusable.focus();
                    e.preventDefault();
                }
            }
        }
    });

    // Focus first element
    if (firstFocusable) {
        firstFocusable.focus();
    }
}

/* ==========================================
   PROGRESS BAR ANIMATION
   ========================================== */

function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-fill');
    
    progressBars.forEach(bar => {
        const width = bar.style.width;
        if (width && width !== '0%') {
            bar.style.width = '0%';
            
            setTimeout(() => {
                bar.style.transition = 'width 1s ease';
                bar.style.width = width;
            }, 100);
        }
    });
}

/* ==========================================
   STATS ANIMATION ON SCROLL
   ========================================== */

document.addEventListener('DOMContentLoaded', function() {
    const statCards = document.querySelectorAll('.stat-card');
    
    if (!statCards.length) return;
    
    const observerOptions = {
        threshold: 0.3,
        rootMargin: '0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    entry.target.style.transition = 'all 0.5s ease';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, 100);
                
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    statCards.forEach(card => {
        observer.observe(card);
    });
});

/* ==========================================
   SEARCH FUNCTIONALITY (Future Enhancement)
   ========================================== */

function initSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            filterContent(searchTerm);
        });
    }
}

function filterContent(searchTerm) {
    const cards = document.querySelectorAll('.teacher-card, .subject-card, .history-card');
    
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

/* ==========================================
   NOTIFICATION SYSTEM (Future Enhancement)
   ========================================== */

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 2rem;
        right: 2rem;
        padding: 1rem 1.5rem;
        background: var(--maroon-primary);
        color: white;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-md);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/* ==========================================
   EXPORT FUNCTIONS TO GLOBAL SCOPE
   ========================================== */

window.initWelcomeBanner = initWelcomeBanner;
window.backToDashboard = backToDashboard;
window.openEvaluateMain = openEvaluateMain;
window.openMySubjects = openMySubjects;
window.openHistory = openHistory;
window.openAnnouncements = openAnnouncements;
window.openProfile = openProfile;
window.openEvaluationModal = openEvaluationModal;
window.closeEvaluationModal = closeEvaluationModal;
window.closeAllModals = closeAllModals;
window.showNotification = showNotification;
window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;