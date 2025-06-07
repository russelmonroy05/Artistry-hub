
const themeToggle = document.getElementById('theme-toggle');
const body = document.body;

// Load saved theme from localStorage
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    body.classList.add(savedTheme);
    themeToggle.innerHTML = savedTheme === 'dark-mode'
        ? '<i class="fas fa-moon"></i>'
        : '<i class="fas fa-sun"></i>';
}

// Toggle theme on button click
themeToggle.addEventListener('click', () => {
    const isDarkMode = body.classList.toggle('dark-mode');
    localStorage.setItem('theme', isDarkMode ? 'dark-mode' : '');
    themeToggle.innerHTML = isDarkMode
        ? '<i class="fas fa-moon"></i>'
        : '<i class="fas fa-sun"></i>';
});

// Apply additional styling for dark mode
function applyDarkModeStyles(isDarkMode) {
    const divs = document.querySelectorAll('div');
    const forms = document.querySelectorAll('form');
    const textElements = document.querySelectorAll('h1, h2, h3, p, span, label');
    
    divs.forEach(div => {
        div.style.backgroundColor = isDarkMode ? '#333' : '';
        div.style.color = isDarkMode ? '#fff' : '';
        div.style.borderColor = isDarkMode ? '#555' : '';
    });

    forms.forEach(form => {
        form.style.backgroundColor = isDarkMode ? '#444' : '';
        form.style.color = isDarkMode ? '#fff' : '';
        form.style.borderColor = isDarkMode ? '#666' : '';
    });

    textElements.forEach(el => {
        el.style.color = isDarkMode ? '#e0e0e0' : '';
    });

    // Optional: Handle button styles
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.style.backgroundColor = isDarkMode ? '#555' : '';
        button.style.color = isDarkMode ? '#fff' : '';
        button.style.borderColor = isDarkMode ? '#777' : '';
    });
}

// Initial application of styles
applyDarkModeStyles(savedTheme === 'dark-mode');

// Reapply styles on toggle
themeToggle.addEventListener('click', () => {
    applyDarkModeStyles(body.classList.contains('dark-mode'));
});
    // Get all like buttons
    const likeButtons = document.querySelectorAll('.like-button');

    // Add event listener to each like button
    likeButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault(); // Prevent the default form submission behavior
            const postId = button.parentNode.action.split('/').pop(); // Get the post ID from the form action
            const csrfToken = button.parentNode.querySelector('input[name="csrfmiddlewaretoken"]').value; // Get the CSRF token

            // Send an AJAX request to the server to update the likes
            fetch(`/like_post/${postId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
                .then(response => response.json())
                .then(data => {
                    // Update the likes count on the page
                    button.querySelector('.like-label').textContent = `Likes ${data.no_of_likes}`;
                    // Toggle the 'liked' class on the button
                    button.classList.toggle('liked');
                })
                .catch(error => console.error(error));
                

        });
    });

    