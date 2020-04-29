// When the user starts to type something inside the password field
const password = document.querySelector("#password");
const password_validation_message = document.querySelector('#password-validation-message');
password.oninput = () => {
    if (password.value.length === 0) {
        password_validation_message.style.display = "none";
    } else {
        password_validation_message.style.display = "block";
    }

    // Validate lowercase letters
    const lowerCaseLetters = /[a-z]/g;
    const letter = document.getElementById("letter");
    if (password.value.match(lowerCaseLetters)) {
        letter.classList.remove("invalid");
        letter.classList.add("valid");
    } else {
        letter.classList.remove("valid");
        letter.classList.add("invalid");
    }

    // Validate capital letters
    const upperCaseLetters = /[A-Z]/g;
    const capital = document.querySelector("#capital");
    if (password.value.match(upperCaseLetters)) {
        capital.classList.remove("invalid");
        capital.classList.add("valid");
    } else {
        capital.classList.remove("valid");
        capital.classList.add("invalid");
    }

    // Validate numbers
    const numbers = /[0-9]/g;
    const number = document.querySelector("#number");
    if (password.value.match(numbers)) {
        number.classList.remove("invalid");
        number.classList.add("valid");
    } else {
        number.classList.remove("valid");
        number.classList.add("invalid");
    }

    // Validate length
    const length = document.querySelector("#length");
    if (password.value.length >= 8) {
        length.classList.remove("invalid");
        length.classList.add("valid");
    } else {
        length.classList.remove("valid");
        length.classList.add("invalid");
    }
};

const registration_form_submit = document.querySelector('#registration-form-submit');
const password_confirm_message = document.querySelector('#password-confirm-message');

const password_confirm = document.querySelector('#password-confirm');
password_confirm.onkeyup = () => {
    if (password_confirm.value.length === 0) {
        password_confirm_message.style.display = "none";
        registration_form_submit.disabled = true;
    } else if (password.value !== password_confirm.value) {
        password_confirm_message.style.display = "block";
        registration_form_submit.disabled = true;
    } else {
        password_confirm_message.style.display = "none";
        registration_form_submit.disabled = false;
    }
};

