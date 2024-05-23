async function getEmail() {
  let response = await fetch('/Check_login');
  if (response.ok) {
    let data = await response.json();
    return data; 
  }
  return null;
}


async function check_login(){
  let data = await getEmail();
  get_cupons();
  if (data) {
    document.getElementById('Login').remove();
    document.getElementById('Sign_up').remove();
    document.getElementById('Profile').href = '/profile';
    document.getElementById('Wallet').href = '/profile';
    document.getElementById('History').href = '/profile';
    return true;
  }
  else{
    
    document.getElementById('Sign_up').innerHTML = "Sign Up";
    document.getElementById('Login').innerHTML = 'Login';
    document.getElementById('Profile').addEventListener('click', showLoginModal);
    document.getElementById('Wallet').addEventListener('click', showLoginModal);
    document.getElementById('History').addEventListener('click', showLoginModal);
    return false;
  }
  
}


var dict = {
  messages: expandMessagesDropdown,
  notifications: expandMessagesDropdown,
  query: expandMessagesDropdown,
  home:Go_home,
  profile:Go_profile,
  login:Go_Login,
  help: expandMessagesDropdown,
  logout:Logout,
  
};

function suggest() {
  var searched = $('#Search_bar').val().trim();
  var matchingKeys = [];
  // Find keys in 'dict' that start with the input text
  for (var key in dict) {
    if (key.startsWith(searched.toLowerCase())) {
      matchingKeys.push(key);
    }
  }

  var suggestionsContainer = $('#suggestions');
  suggestionsContainer.empty();
  if (matchingKeys.length > 0) {
    // Display the suggestions based on matching keys
    showSuggestions(matchingKeys);
  } 
  
}

function showSuggestions(suggestions) {
  var suggestionsContainer = $('#suggestions');
  suggestionsContainer.empty();

  suggestions.forEach(function (suggestion) {
    var capitalizedSuggestion = suggestion.charAt(0).toUpperCase() + suggestion.slice(1);
    var suggestionElement = $('<div>')
      .addClass('suggestion')
      .text(capitalizedSuggestion);
    suggestionsContainer.append(suggestionElement);
  });

  // Attach a click event handler to the suggestions container for delegation
  suggestionsContainer.on('click', '.suggestion', function () {
    var suggestion = $(this).text();
    $('#Search_bar').val(suggestion.toLowerCase());
    search(suggestion); // Trigger search when a suggestion is clicked
  });

  // Position the suggestions div below the search bar
  var inputOffset = $('#Search_bar').offset();
  suggestionsContainer.css({
    top: inputOffset.top + $('#Search_bar').outerHeight(),
    left: inputOffset.left,
    width: $('#Search_bar').outerWidth(),
  });
  suggestionsContainer.show();
  
}

function clearSuggestions() {
  $('#suggestions').hide();
  $('#Search_bar').val('');
}

function search(text) {
  event.preventDefault();
  var searched = text;
  //clearSuggestions();
  if (searched.length > 0) {
    if (searched.length <= 15 && dict.hasOwnProperty(searched.toLowerCase())) {
      dict[searched.toLowerCase()]();
    } else {
      findString(searched);
    }
  }
}

function findString(str) {
 
  var found = false;
  if (window.find) {
    
    // Modern browsers that support window.find
    found = window.find(str);
  } else {
    // Fallback for older browsers
    var body = document.body;
    var textNode = document.createTextNode(str);
    var searchRange, range, span;

    // Create a temporary element to wrap the found text
    span = document.createElement('span');
    span.className = 'highlighted-text';
    span.appendChild(textNode);

    // Append the temporary element to the body
    body.appendChild(span);

    // Create a range to search for the text
    searchRange = document.createRange();
    searchRange.selectNodeContents(body);

    // Start the search from the beginning of the document
    range = searchRange.cloneRange();
    range.collapse(true);

    // Perform the search
    while (range.findText(str)) {
      range.surroundContents(span.cloneNode(true));
      found = true;
    }

    body.normalize();
    span.parentNode.replaceChild(textNode, span);
  }

  if (!found) {
   
    if (str.length > 8) {
      showPopup(str.substring(0,4) + '...');
    } else {
      showPopup(str);
    }
    $('#Search_bar').val('');
  }
}


function expandMessagesDropdown() {
  var messagesToggle = $('#MessagesToggle');
  var dropdown = new bootstrap.Dropdown(messagesToggle);
    setTimeout(()=>{dropdown.show()},100);
}



function showPopup(data) {
  // Create a container element for the popup
  const container = document.createElement('div');
  container.setAttribute('class', 'popup-container');
  document.body.appendChild(container);

  const box = document.createElement('div');
  box.setAttribute('class', 'big_5_selected_text_analysis_box');

  box.innerHTML = `
    <h3 class="title">
      <span>${data} not found</span>
    </h3>
    <h6 style="color:green">You can make a Query instead.</h6>
  `;

  const buttonContainer = document.createElement('div');
  buttonContainer.style.display = 'flex';
  buttonContainer.style.justifyContent = 'flex-end';
  buttonContainer.style.marginTop = '10px';

  const okButton = document.createElement('button');
  okButton.style.width = '70px';
  okButton.style.height = '30px';
  okButton.style.borderRadius = '4px';
  okButton.style.backgroundColor = '#27f2b2';
  okButton.style.border = 'none';
  okButton.style.cursor = 'pointer';
  okButton.style.marginRight = '10px';
  okButton.style.marginTop = '10px';
  okButton.innerText = 'OK';

  const cancelButton = document.createElement('button');
  cancelButton.style.width = '70px';
  cancelButton.style.height = '30px';
  cancelButton.style.borderRadius = '4px';
  cancelButton.style.backgroundColor = '#27f2b2';
  cancelButton.style.marginTop = '10px';
  cancelButton.style.border = 'none';
  cancelButton.style.cursor = 'pointer';
  cancelButton.innerText = 'Cancel';

  okButton.addEventListener('click', () => {
    expandMessagesDropdown();
    box.remove();
    container.remove();
    
  });

  cancelButton.addEventListener('click', () => {
    box.remove();
    container.remove();
  });

  // Create a <span> element to style the inner HTML
  const closeBtn = document.createElement('button');
  closeBtn.style.width = '25px';
  closeBtn.style.height = '25px';
  closeBtn.style.borderRadius = '4px';
  closeBtn.style.backgroundColor = '#fff';
  closeBtn.style.border = 'none';
  closeBtn.style.cursor = 'pointer';
  closeBtn.style.margin = '15px 15px 5px 0px';

  // Create a <span> element to style the inner HTML
  const closeIcon = document.createElement('span');
  closeIcon.innerHTML = '&#10005;'; // Insert the cross sign (×)
  closeIcon.style.fontFamily = 'Arial, sans-serif'; // Set the font family
  closeIcon.style.fontSize = '18px'; // Set the font size
  closeIcon.style.fontWeight = 'bold';
  closeIcon.style.color = 'black'; // Set the color
  closeIcon.style.position = 'relative';
  closeIcon.style.bottom = '10px';
  closeBtn.appendChild(closeIcon);

  closeBtn.addEventListener('click', () => {
    box.remove();
    container.remove();
  });

  setTimeout(function () {
    closeBtn.click();
  }, 6000);

  box.querySelector('h3').appendChild(closeBtn);

  // Append buttons to button container
  buttonContainer.appendChild(okButton);
  buttonContainer.appendChild(cancelButton);

  // Append the button container to the box
  box.appendChild(buttonContainer);

  // Append the box to the container
  container.appendChild(box);

  // Apply CSS styles to control the position
  container.style.position = 'fixed'; // Fixed positioning to keep it in view
  container.style.top = '80px'; // Adjust top as needed
  container.style.right = '30px'; // Adjust right as needed
  container.style.background = '#ffe6c4'; // Background color
  container.style.color = 'black'; // Text color
  container.style.maxWidth = '80%'; // Maximum width for responsiveness
  container.style.padding = '10px'; // Padding for content
  container.style.zIndex = '9999'; // Ensure it's above other content
  container.style.borderRadius = '10px';
  box.style.borderRadius = '10px';
  container.style.alignContent = 'center';
  box.style.padding = '10px';
  container.style.border = '2px solid black';
}



function Go_home(){
  location.href='/';
}


function Go_Login() {
  showLoginModal();
}

function Go_profile() {
  location.href="/profile";
}
function Logout(){
  var btn = document.getElementById('Sign_up');
  if(btn){
    Go_Login();
  }else{
    logout();
  }
}

async function logout() {
  var result = confirm('You are about to log-out!');
  if (result) {
    let response = await fetch('/Log_out');
    // Handle the response as needed
    if (response.status === 200 && response.redirected) {
      window.location.href = response.url;
    } else {
      alert("Log Out failed.");
    }
  }
}

// function getFirebaseErrorMessage (code) {
//   var message = null;
//   console.log(code);
//   switch (code) {
//     case "auth/user-not-found":
//       message = 'USER NOT FOUND';
//       break;
//     case "auth/email-already-in-use":
//       message = 'EMAIL ALREADY IN USE';
//       break;
//     case "auth/internal-error":
//       message = 'INTERNAL ERROR';
//       break;
//     case "auth/invalid-login-credentials":
//       message = 'INVALID LOGIN CREDENTIALS';
//       break;
//     case "auth/invalid-email":
//       message = 'INVALID EMAIL FORMAT';
//       break;
//     case "auth/invalid-password":
//       message = 'INVALID PASSWORD FORMAT';
//       break;
//     case "auth/weak-password":
//       message = 'Password Too Weak! Use Atleast 6 characters';
//       break;
//     default:
//       message = 'Something Went Wrong! Try Again';
//       break;
//   }
//   return message;
// }

function validateMobile() {
  var mobileInput = document.getElementById("mobile") || document.getElementById("editMobile");
  var mobileValue = mobileInput.value;
  if (mobileValue.length > 0 && mobileValue.length < 12 && mobileValue.length!=10) {
    alert("Provide a 10/12 digit mobile number!");
    mobileInput.value = "";
    return false;
  }
  // Regular expression to match valid mobile number format
  var mobileRegex = /^(\+\d{1,2}\s?)?\d{10}$/;


  if (mobileValue.length > 0 && !mobileRegex.test(mobileValue)) {
    alert("Invalid mobile number format.Use 10/12 digits Only");
    mobileInput.value = "";
    return false;
  }

  return true;
}


function get_cupons() {
  const showCuponsDiv = document.getElementById('ShowCupons');
  fetch('/get_cupons')
    .then(response => response.json())
    .then(data => {
      if (data.data && data.data.length > 0) {
        const cupons = data.data;
        
        // Map the coupon data to formatted strings
        const formattedCupons = cupons.map(cupon => {
          const [name, value] = cupon;
          return `${name.charAt(0).toUpperCase() + name.slice(1)} - ${value}%`;
        });

        // Join the formatted coupon strings with commas and set as text content
        showCuponsDiv.textContent = 'Coupons available: ' + formattedCupons.join(' | ');
      } else {
        // Handle the case where there are no coupon names
        showCuponsDiv.textContent ="No coupons available currently..";
        console.log('No coupons available currently..');
      }
    })
    .catch(error => {
      document.getElementById('scroll-container').remove();
      console.error('Error:', error);
    });
}

function validateForm() {
  var email = document.getElementById('contactemail').value;
  var message = document.getElementById('contactmessage').value;

  // Check if email is valid and message is at least 5 characters long
  var isValidEmail = ValidateEmail(email);
  var isMessageValid = message.length >= 5;

  // Enable or disable the "Proceed" button based on validation results
  $('#proceedbutton2').prop('disabled', !(isValidEmail && isMessageValid));
}

function submitContactForm() {
  var email = document.getElementById('contactemail').value;
  var message = document.getElementById('contactmessage').value;

  var formData = {
    email: email,
    message: message
  };

  // Send the data to the Flask endpoint using AJAX
  $.ajax({
    type: "POST",
    url: "/make_query", // Replace with the actual URL
    data: JSON.stringify(formData),
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    success: function (response) {
      document.getElementById("Reply1").innerHTML = `<div class="alert alert-success" role="alert" style="color:black;font-weight:500;text-align:center;">
                ${response.message} <br> Unregistered user queries will be resolved via mail.
            </div>`;
      setTimeout(function () { $('#ContactModal').modal('hide'); }, 4000);

    },
    error: function (error) {
      document.getElementById("Reply1").innerHTML = `<div class="alert alert-danger" role="alert" style="color:black;font-weight:500;text-align:center;">
                Some Error occurred. Try Again!
            </div>`;
    }
  });
}

function ValidateEmail(input) {
  var validRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;

  return input.match(validRegex) != null;
}


function validateForm() {
  var email = document.getElementById('contactemail').value;
  var message = document.getElementById('contactmessage').value;

  // Check if email is valid and message is at least 5 characters long
  var isValidEmail = ValidateEmail(email);
  var isMessageValid = message.length >= 5;

  // Enable or disable the "Proceed" button based on validation results
  $('#SendMessage').prop('disabled', !(isValidEmail && isMessageValid));
}


