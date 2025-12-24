// --- 1. Toggle Login vs Register ---
function switchForm(formType) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const btnLogin = document.getElementById('btn-login');
    const btnRegister = document.getElementById('btn-register');

    if (formType === 'login') {
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        btnLogin.classList.add('active');
        btnRegister.classList.remove('active');
    } else {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
        btnLogin.classList.remove('active');
        btnRegister.classList.add('active');
    }
}

// --- 2. Toggle Vendor Fields ---
function toggleVendorFields() {
    const role = document.querySelector('input[name="role"]:checked').value;
    const vendorFields = document.getElementById('vendor-fields');
    
    if (role === 'vendor') {
        vendorFields.style.display = 'block';
    } else {
        vendorFields.style.display = 'none';
    }
}

// --- 3. Realtime Validation ---
document.addEventListener("DOMContentLoaded", function () {
    const inputs = document.querySelectorAll('#register-form input');
    const submitBtn = document.getElementById('reg-btn');

    // Validation patterns
    const patterns = {
        firstname: /^[a-zA-Z\s]{2,}$/,   // At least 2 letters
        lastname: /^[a-zA-Z\s]{2,}$/,
        email: /^[^ ]+@[^ ]+\.[a-z]{2,3}$/,
        phone: /^[0-9]{10}$/,             // Exactly 10 digits
        password: /^(?=.*\d)(?=.*[a-z]).{6,}$/, // 6+ chars, 1 number
        business_name: /.+/               // Not empty
    };

    function validate(field, regex) {
        if (regex.test(field.value)) {
            field.className = 'valid';
            return true;
        } else {
            field.className = 'invalid';
            return false;
        }
    }

    // Special check for Confirm Password
    function checkPasswords() {
        const pass = document.getElementById('password');
        const confirm = document.getElementById('confirm_password');
        if (confirm.value === '') return false;
        
        if (pass.value === confirm.value) {
            confirm.className = 'valid';
            return true;
        } else {
            confirm.className = 'invalid';
            return false;
        }
    }

    // Attach Keyup Listeners
    inputs.forEach((input) => {
        input.addEventListener('keyup', (e) => {
            let isValid = false;

            // Check specific fields
            if (patterns[e.target.id]) {
                isValid = validate(e.target, patterns[e.target.id]);
            } else if (e.target.id === 'confirm_password') {
                isValid = checkPasswords();
            } else {
                // Fields without specific regex (like City) are just considered valid if not empty
                if(e.target.value.length > 0) e.target.classList.add('valid'); 
            }
            
            checkFormValidity();
        });
    });

    function checkFormValidity() {
        const invalidInputs = document.querySelectorAll('.invalid'); // Any red fields?
        const pass = document.getElementById('password').value;
        const conf = document.getElementById('confirm_password').value;
        
        // 1. Get Address Value (Handle potential null if on login page)
        const addressField = document.querySelector('textarea[name="address"]');
        const address = addressField ? addressField.value.trim() : "skip"; 

        // 2. Logic: Button enabled ONLY if:
        //    - No red fields (invalidInputs == 0)
        //    - Passwords match and are filled
        //    - Address is not empty
        if (invalidInputs.length === 0 && pass && conf && (pass === conf) && address !== "") {
            submitBtn.removeAttribute('disabled');
            submitBtn.style.backgroundColor = "#FF6B00"; // Make it bright orange
            submitBtn.style.cursor = "pointer";
        } else {
            submitBtn.setAttribute('disabled', 'true');
            submitBtn.style.backgroundColor = "#ccc"; // Grey out
            submitBtn.style.cursor = "not-allowed";
        }
    }
   
});
 /**
 * Toggles password visibility
 * @param {string} inputId - The ID of the input field (e.g. 'password')
 * @param {element} icon - The icon element itself (to switch classes)
 */
    function togglePassword(inputId, icon) {
        const input = document.getElementById(inputId);
        
        if (input.type === "password") {
            input.type = "text";
            icon.classList.remove("fa-eye");
            icon.classList.add("fa-eye-slash");
        } else {
            input.type = "password";
            icon.classList.remove("fa-eye-slash");
            icon.classList.add("fa-eye");
        }
    }

    // --- Snackbar Logic ---
document.addEventListener("DOMContentLoaded", function() {
    const snackbar = document.getElementById("snackbar");
    
    // If the snackbar exists and has text (meaning Flask sent a message)
    if (snackbar && snackbar.innerText.trim() !== "") {
        snackbar.className = "show " + snackbar.className; // Add 'show' class
        
        // Hide after 3 seconds
        setTimeout(function() { 
            snackbar.className = snackbar.className.replace("show", ""); 
        }, 3000);
    }
});