// Hamburger Menu Toggle
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');

// Toggle menu when hamburger is clicked
hamburger.addEventListener('click', function() {
    hamburger.classList.toggle('active');
    navLinks.classList.toggle('active');
});

// Close menu when a link is clicked
const navItems = navLinks.querySelectorAll('a');
navItems.forEach(item => {
    item.addEventListener('click', function() {
        hamburger.classList.remove('active');
        navLinks.classList.remove('active');
    });
});

// Close menu when clicking outside
document.addEventListener('click', function(event) {
    const isClickInsideNav = navLinks.contains(event.target);
    const isClickInsideHamburger = hamburger.contains(event.target);
    
    if (!isClickInsideNav && !isClickInsideHamburger && navLinks.classList.contains('active')) {
        hamburger.classList.remove('active');
        navLinks.classList.remove('active');
    }
});


// Smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Typing Effect for Home Section
const quotes = [
    "Teacher Evaluation System",
    "Excellence • Integrity • Service",
    "Empowering Education Since 1948"
];

let quoteIndex = 0;
let charIndex = 0;
let currentQuote = '';
let isDeleting = false;

function typeEffect() {
    const typingElement = document.querySelector('.typing-text');
    
    if (!typingElement) return;

    if (!isDeleting && charIndex <= quotes[quoteIndex].length) {
        currentQuote = quotes[quoteIndex].substring(0, charIndex);
        charIndex++;
    } else if (isDeleting && charIndex >= 0) {
        currentQuote = quotes[quoteIndex].substring(0, charIndex);
        charIndex--;
    }

    typingElement.textContent = currentQuote;

    let typingSpeed = 100;

    if (!isDeleting && charIndex === quotes[quoteIndex].length + 1) {
        typingSpeed = 2000; // Pause at end
        isDeleting = true;
    } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        quoteIndex = (quoteIndex + 1) % quotes.length;
        typingSpeed = 500; // Pause before next quote
    } else if (isDeleting) {
        typingSpeed = 50; // Faster when deleting
    }

    setTimeout(typeEffect, typingSpeed);
}

// Start typing effect when page loads
window.addEventListener('load', () => {
    setTimeout(typeEffect, 500);
});
