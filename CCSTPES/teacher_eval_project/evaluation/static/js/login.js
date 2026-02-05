 document.addEventListener('DOMContentLoaded', function () {
            // Toggle Password Visibility
            const togglePassword = document.getElementById('togglePassword');
            const passwordInput = document.getElementById('password');

            if (togglePassword && passwordInput) {
                togglePassword.addEventListener('click', function () {
                    // Toggle the type attribute
                    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                    passwordInput.setAttribute('type', type);
                    
                    // Toggle the icon
                    this.classList.toggle('fa-eye');
                    this.classList.toggle('fa-eye-slash');
                });
            }

            // Auto-hide messages after 5 seconds
            const messageAlerts = document.querySelectorAll('.login-alert');
            messageAlerts.forEach(alert => {
                setTimeout(function () {
                    alert.style.opacity = '0';
                    setTimeout(() => alert.remove(), 300);
                }, 5000);
            });

            // Hide messages when user starts typing
            const usernameInput = document.getElementById('username');
            const hideMessages = () => {
                messageAlerts.forEach(alert => {
                    alert.style.opacity = '0';
                    setTimeout(() => alert.remove(), 5000);
                });
            };

            if (usernameInput) {
                usernameInput.addEventListener('input', hideMessages);
            }
            if (passwordInput) {
                passwordInput.addEventListener('input', hideMessages);
            }
        });

// Modal Functionality for "sign up" Button
        function openModal() {
        document.getElementById('getStartedModal').style.display = 'block';
    }

    function closeModal() {
        document.getElementById('getStartedModal').style.display = 'none';
    }

    // Close modal when clicking outside
    window.onclick = function (event) {
        var modal = document.getElementById('getStartedModal');
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }


    // 
     document.getElementById('loginForm').addEventListener('submit', function (e) {
        const signInBtn = document.getElementById('signInBtn');
        const btnText = document.getElementById('btnText');
        const btnIcon = document.getElementById('btnIcon');

        // Add loading state
        signInBtn.classList.add('loading');
        signInBtn.disabled = true;

        // Create spinner
        const spinner = document.createElement('i');
        spinner.className = 'fas fa-spinner fa-spin';
        spinner.style.marginRight = '8px';

        // Update button content
        btnText.textContent = 'Signing in';
        btnIcon.style.display = 'none';
        btnIcon.parentNode.insertBefore(spinner, btnIcon);
    });
