// Password visibility toggle
    const togglePass = document.getElementById("togglePass");
    const togglePass2 = document.getElementById("togglePass2");
    const p1 = document.getElementById("password");
    const p2 = document.getElementById("password2");

    function toggleVisibility(iconEl, inputEl) {
        if (!iconEl || !inputEl) return;
        if (inputEl.type === 'password') {
            inputEl.type = 'text';
            // switch boxicon from show -> hide if available
            iconEl.classList.remove('bx-show');
            iconEl.classList.add('bx-hide');
        } else {
            inputEl.type = 'password';
            iconEl.classList.remove('bx-hide');
            iconEl.classList.add('bx-show');
        }
    }

    togglePass.addEventListener('click', function () { toggleVisibility(togglePass, p1); });
    togglePass2.addEventListener('click', function () { toggleVisibility(togglePass2, p2); });

    // Modal Functions
    function showModal() {
        document.getElementById('emailVerifyModal').classList.add('show');
    }

    function closeModal() {
        document.getElementById('emailVerifyModal').classList.remove('show');
        clearInterval(pollingInterval);
        clearInterval(timeInterval);
    }

    // Close modal when clicking outside
    document.getElementById('emailVerifyModal').addEventListener('click', function (e) {
        if (e.target === this) {
            closeModal();
        }
    });

    // Email Verification System
    let pollingInterval = null;
    let timeCounter = 0;
    let timeInterval = null;

    document.getElementById('verifyEmailBtn').addEventListener('click', function (e) {
        e.preventDefault();
        const emailInput = document.getElementById('emailInput');
        const email = emailInput.value.trim();

        // Validate email
        if (!email) {
            alert('Please enter an email address');
            emailInput.focus();
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('Please enter a valid email address');
            emailInput.focus();
            return;
        }

        // Start verification process
        startEmailVerification(email);
    });

    function startEmailVerification(email) {
        // Show modal
        showModal();

        // Reset phases
        document.getElementById('sendingPhase').style.display = 'block';
        document.getElementById('waitingPhase').style.display = 'none';
        document.getElementById('successPhase').style.display = 'none';
        document.getElementById('errorPhase').style.display = 'none';
        document.getElementById('sendingEmail').textContent = email;

        // Send verification email
        fetch('/send-verification-code/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ email: email })
        })
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                if (data.success) {
                    // Switch to waiting phase
                    document.getElementById('sendingPhase').style.display = 'none';
                    document.getElementById('waitingPhase').style.display = 'block';
                    document.getElementById('verificationEmail').textContent = email;

                    // Start polling
                    startPolling(email);

                    // Start timer
                    startTimer();
                } else {
                    showError(data.message || 'Failed to send verification email');
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                showError('Network error. Please try again.');
            });
    }

    function startPolling(email) {
        timeCounter = 0;
        let pollCount = 0;
        const maxPolls = 120; // 4 minutes

        pollingInterval = setInterval(() => {
            pollCount++;

            fetch(`/check-verification-status/?email=${encodeURIComponent(email)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.verified) {
                        // Success!
                        clearInterval(pollingInterval);
                        clearInterval(timeInterval);
                        showSuccess();
                    } else if (pollCount >= maxPolls) {
                        // Timeout
                        clearInterval(pollingInterval);
                        clearInterval(timeInterval);
                        showError('Verification timeout. Please try again.');
                    }
                })
                .catch(error => {
                    console.error('Polling error:', error);
                });
        }, 2000); // Check every 2 seconds
    }

    function startTimer() {
        timeCounter = 0;
        timeInterval = setInterval(() => {
            timeCounter++;
            document.getElementById('timeElapsed').textContent = timeCounter;
        }, 1000);
    }

    function showSuccess() {
        document.getElementById('waitingPhase').style.display = 'none';
        document.getElementById('successPhase').style.display = 'block';

        // Update button
        const verifyBtn = document.getElementById('verifyEmailBtn');
        verifyBtn.innerHTML = '<i class="fas fa-check-circle"></i> Verified';
        verifyBtn.disabled = true;
        verifyBtn.classList.remove('btn-outline-primary');
        verifyBtn.classList.add('btn-success');

        // Set hidden flag
        document.getElementById('emailVerifiedFlag').value = 'true';

        // Auto close after 2 seconds
        setTimeout(() => {
            closeModal();
        }, 2000);
    }

    function showError(message) {
        document.getElementById('sendingPhase').style.display = 'none';
        document.getElementById('waitingPhase').style.display = 'none';
        document.getElementById('errorPhase').style.display = 'block';
        document.getElementById('errorMessage').textContent = message;

        clearInterval(pollingInterval);
        clearInterval(timeInterval);
    }

    // Retry button
    document.getElementById('retryBtn').addEventListener('click', function () {
        const email = document.getElementById('emailInput').value;
        startEmailVerification(email);
    });

    // (submission validation is handled below with terms check)

    // Terms checkbox validation
    const termsCheckbox = document.getElementById('termsCheckbox');
    const termsError = document.getElementById('termsError');

    termsCheckbox.addEventListener('change', function () {
        if (this.checked) {
            termsError.style.display = 'none';
        }
    });

    document.getElementById('registrationForm').addEventListener('submit', function (e) {
        const emailVerified = document.getElementById('emailVerifiedFlag').value;
        const termsChecked = document.getElementById('termsCheckbox').checked;

        if (emailVerified !== 'true') {
            e.preventDefault();
            alert('Please verify your email address before registering');
            document.getElementById('verifyEmailBtn').focus();
            return false;
        }

        if (!termsChecked) {
            e.preventDefault();
            termsError.style.display = 'block';
            document.getElementById('termsCheckbox').focus();
            return false;
        }
    });

    // Terms and Privacy Modal Functions (use a reusable content modal)
    function showContentModal(title, htmlContent) {
        // Create modal if not exists
        let modal = document.getElementById('contentModal');
        if (!modal) {
            const modalHtml = `
            <div class="modal" id="contentModal">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="contentModalTitle"></h5>
                            <button type="button" class="btn-close" onclick="closeContentModal()">&times;</button>
                        </div>
                        <div class="modal-body p-4" id="contentModalBody"></div>
                    </div>
                </div>
            </div>`;
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            modal = document.getElementById('contentModal');

            // close when clicking outside
            modal.addEventListener('click', function (e) {
                if (e.target === this) closeContentModal();
            });
        }

        document.getElementById('contentModalTitle').textContent = title;
        document.getElementById('contentModalBody').innerHTML = htmlContent.replace(/\n/g, '<br><br>');
        modal.classList.add('show');
    }

    function closeContentModal() {
        const modal = document.getElementById('contentModal');
        if (modal) modal.classList.remove('show');
    }

    function showTermsModal(e) {
        e.preventDefault();
        const html = `
        <strong>1.</strong> By registering, you agree to comply with all applicable laws and regulations.
        <strong>2.</strong> You are responsible for maintaining the confidentiality of your account credentials.
        <strong>3.</strong> You agree not to use this platform for any unlawful or harmful activities.
        <strong>4.</strong> The platform reserves the right to suspend or terminate accounts that violate these terms.
        <strong>5.</strong> All content and materials provided are for educational purposes only.`;
        showContentModal('Terms and Conditions', html);
    }

    function showPrivacyModal(e) {
        e.preventDefault();
        const html = `
        <strong>1.</strong> We collect personal information only for account creation and educational purposes.
        <strong>2.</strong> Your email and personal data will not be shared with third parties without consent.
        <strong>3.</strong> We use industry-standard security measures to protect your data.
        <strong>4.</strong> You can request data deletion at any time by contacting support.
        <strong>5.</strong> This policy may be updated periodically; continued use implies acceptance.`;
        showContentModal('Privacy Policy', html);
    }
    // Get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }