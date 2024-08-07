var jsonData; //Stores the toll rates data
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

async function getEmail() {
  return new Promise(async (resolve, reject) => {
    try {
      let response = await fetch('/Check_login');
      if (response.ok) {
        let data = await response.json();
        resolve(data.message);
        delete dict['login'];
      } else {
        reject(null);
        delete dict['logout'];
      }
    } catch (error) {
      delete dict['logout'];
      reject(null);
    }
  });
}

async function check_login(){
  return new Promise (async(resolve,reject)=>{
    try{
      let data = await getEmail();
      if (data) {
        document.getElementById('Login').remove();
        document.getElementById('Sign_up').remove();
        document.getElementById('Profile').href = '/profile';
        document.getElementById('Wallet').href = '/profile';
        document.getElementById('History').href = '/profile';
        resolve(true);
      }
      else {
        document.getElementById('Sign_up').innerHTML = "Sign Up";
        document.getElementById('Login').innerHTML = 'Login';
        document.getElementById('Profile').addEventListener('click', showLoginModal);
        document.getElementById('Wallet').addEventListener('click', showLoginModal);
        document.getElementById('History').addEventListener('click', showLoginModal);
        reject(false);
      }
    }catch{
      document.getElementById('Sign_up').innerHTML = "Sign Up";
      document.getElementById('Login').innerHTML = 'Login';
      document.getElementById('Profile').addEventListener('click', showLoginModal);
      document.getElementById('Wallet').addEventListener('click', showLoginModal);
      document.getElementById('History').addEventListener('click', showLoginModal);
      reject(false);
    }
  });
}




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
  try{
      var result =await showConfirmation('You are about to log-out!');
    if (result) {
      let response = await fetch('/Log_out');
      // Handle the response as needed
      if (response.status === 200 && response.redirected) {
        window.location.href = '/';
      } else {
        showError("Log out failed. try again!");
      }
    }
  }catch{
    showError("Log out failed. try again!");
    null;
  }
}

function validateMobile() {
  var mobileInput = document.getElementById("mobile") || document.getElementById("editMobile");
  var mobileValue = mobileInput.value;
  if (mobileValue.length > 0 && mobileValue.length < 12 && mobileValue.length!=10) {
    showError("Provide a 10/12 digit mobile number!");
    mobileInput.value = "";
    return false;
  }
  // Regular expression to match valid mobile number format
  var mobileRegex = /^(\+\d{1,2}\s?)?\d{10}$/;


  if (mobileValue.length > 0 && !mobileRegex.test(mobileValue)) {
    showError("Invalid mobile number format.Use 10/12 digits Only");
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
        const coupons = data.data;
        if(data.data.length==1){
          showCuponsDiv.textContent = "No coupons available currently...";
        }else{
          const globalCoupon = coupons.find(coupon => coupon.name.toLowerCase() === 'global');
        const otherCoupons = coupons.filter(coupon => coupon.name.toLowerCase() !== 'global');
        if(globalCoupon && globalCoupon.rate){
          const discountRate = globalCoupon.rate; // Replace with the actual field name
          document.getElementById("Discounts").innerText = `Discounts applied: ${discountRate} %`;

          for (const vehicleType in jsonData) {
            const journeyTypes = jsonData[vehicleType];
            for (const journeyType in journeyTypes) {
              const originalAmount = journeyTypes[journeyType];
              const discountedAmount = calculateDiscountedAmount(originalAmount, discountRate);
              journeyTypes[journeyType] = discountedAmount;
            }
          }
        }
        // Map the other coupon data to formatted strings
        const formattedCoupons = otherCoupons.map(coupon => {
          return `${coupon.name.charAt(0).toUpperCase() + coupon.name.slice(1)} - ${coupon.rate}%`;
        });

        // Join the formatted coupon strings with commas and set as text content
        showCuponsDiv.textContent = 'Coupons available: ' + formattedCoupons.join(' | ');
        }
        
      } else {
        // Handle the case where there are no coupons
        showCuponsDiv.textContent = "No coupons available currently...";
      }
      populateTable();
    })
    .catch(error => {
      document.getElementById('scroll-container').remove();
      console.error('Error:', error);
      populateTable();
    });
}


async function fetchTollRate() {
  var c=5000;
  while(c--){
    try {
      // Fetch the toll rate
      const tollResponse = await fetch('/get_toll_rate');
  
      // Check if the response status is OK (200)
      if (tollResponse.status === 200) {
        // Parse the JSON response for toll rates
        jsonData = await tollResponse.json();
      } else {
        // Handle the error or return a default value for toll rates
        throw new Error('Failed to fetch toll rate data');
      }
      get_cupons();
      break;
    } catch (error) {
      // Handle any errors that occurred during the fetch
      continue;
    } 
  }
 
}

// Function to calculate the discounted amount
function calculateDiscountedAmount(originalAmount, discountRate) {
  // Calculate the discounted amount
  const discountedAmount = originalAmount - (originalAmount * discountRate / 100);
  // Round the result to two decimal places and parse it as a float
  return parseFloat(discountedAmount.toFixed(2));
}

// Function to format vehicle type names
function formatVehicleTypeName(name) {
  if (name.startsWith("axel")) {
    const parts = name.split("_");

    if (parts.length > 2)
      return `${parts[1]} to ${parts[2]} Axel`;
    return `${parts[1]} Axel`
  } else {
    return name.charAt(0).toUpperCase() + name.slice(1);
  }
}

function populateTable() {
  // Get the table body element
  const tableBody = document.getElementById("priceTableBody");

  // Convert JSON data into an array of objects
  const dataArray = [];
  for (const vehicleType in jsonData) {
    if (vehicleType !== "_id") {
      const formattedVehicleType = formatVehicleTypeName(vehicleType);
      const vehicleData = jsonData[vehicleType];
      dataArray.push({
        vehicleType: formattedVehicleType,
        ...vehicleData,
      });
    }
  }

  // Sort the array by the "single" category in ascending order
  dataArray.sort((a, b) => a.single - b.single);

  // Iterate through the sorted array and create table rows
  dataArray.forEach((dataItem) => {
    const newRow = document.createElement("tr");

    const vehicleTypeCell = document.createElement("td");
    vehicleTypeCell.textContent = dataItem.vehicleType;
    newRow.appendChild(vehicleTypeCell);

    // Create separate cells for "single," "return," and "monthly" values
    ["single", "return", "monthly"].forEach((category) => {
      const cell = document.createElement("td");
      cell.textContent = ` ${dataItem[category]}`;
      newRow.appendChild(cell);
    });

    tableBody.appendChild(newRow);
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
  if(input==undefined || input==null) return false;
  var validRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
  return String(input).match(validRegex) != null;
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


