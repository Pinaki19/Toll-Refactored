
function Add_template(Name, Desc, modal = "none") {
    var elem = document.createElement('div');
    elem.setAttribute('class', "col-sm-6 mb-3");
    var ch1 = document.createElement('div');
    ch1.setAttribute('class', "card h-100");
    var ch2 = document.createElement('div');
    ch2.setAttribute('class', "card-body");
    ch2.innerHTML = `<h6 class="d-flex align-items-center mb-3" style="font-size:20px;">${Name}</h6>
    <p>${Desc}</p><hr style="padding:0px;margin:0px;"><div style="margin-top:5px;padding:0px;text-align:right;">
    <a class="btn btn-info btn-md" style=" background-color:lightgreen;"${modal} >Go</a></div>`;
    ch1.appendChild(ch2);
    elem.appendChild(ch1);
    document.getElementById('Content-Div').appendChild(elem);
}


function show_super_admin_content() {
    Add_template('Modify Users', 'Add a new Admin for the system, Suspend User Accounts', 'data-bs-toggle="modal" data-bs-target="#newAdminModal"');
    Add_template('Delete Admin', 'Remove Admin account', 'data-bs-toggle="modal" data-bs-target="#deleteAdminModal"');
   
}

function show_admin_content() {

    var elem2 = document.createElement('h4');
    elem2.textContent = "ADMIN SECTION";
    elem2.style.color = 'blue';
    document.getElementById("Content-Div").appendChild(elem2);
    Add_template('Change Toll Rate', 'Modify the current Toll Rates', 'data-bs-toggle="modal" data-bs-target="#changeTollModal"');
    Add_template('Modify Discounts', 'Issue new or modify existing Discount offers.', 'data-bs-toggle="modal" data-bs-target="#changeDiscountsModal"');
    
}

function show_user_content() {

    Add_template('All Transactions', 'Check your lifetime transactions', 'data-bs-toggle="modal" data-bs-target="#RecentModal"');

}
document.addEventListener('DOMContentLoaded', function () {
    // Make a query to the URL and save the data in a variable
    const options = {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
        
    };

    fetch('/load_recent_transactions')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.transactions.length > 0) {
                var recentTransactions = data.transactions.slice(0, 10); // Limit to 5 transactions
                const listGroup = document.querySelector('.list-group');
                var alltransactions = data.transactions;
                // Iterate over the recent transactions and create list items
                recentTransactions.forEach(transaction => {
                    const listItem = document.createElement('li');
                    listItem.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');

                    // Create a div to hold the transaction details
                    const transactionDiv = document.createElement('div');
                    transactionDiv.textContent = transaction.data.Type;

                    // Calculate the value (Amount - GlobalDiscount - Cupons + Gst)
                    const value = transaction.data.Amount - transaction.data.GlobalDiscount - transaction.data.Cupon + transaction.data.Gst;
                    const valueSpan = document.createElement('span');

                    const dateTimeDiv = document.createElement('div');
                    dateTimeDiv.textContent = formatTime(transaction.DateTime);
                    // Add a plus sign and make it green for "Add Money," otherwise add a negative sign and make it red
                    if (transaction.data.Type === 'Add Money') {
                        valueSpan.innerHTML = `+ &#8377;${value.toFixed(2)}`; // Format to 2 decimal places
                        valueSpan.style.color = 'green';
                    } else {
                        valueSpan.innerHTML = `- &#8377;${Math.abs(value).toFixed(2)}`; // Format to 2 decimal places
                        valueSpan.style.color = 'red';
                    }

                    // Append the transaction details and value to the list item
                    listItem.appendChild(transactionDiv);
                    listItem.appendChild(valueSpan);
                    listItem.appendChild(dateTimeDiv);
                    // Append the list item to the list group
                    listGroup.appendChild(listItem);
                });
                
                alltransactions.forEach(transaction => {
                    
                    fillModalBody(transaction);
                    
                });
            } else {
                // Handle the case where there are no recent transactions
                fillModalBodyDummy('No recent transactions !');
                console.log('No recent transactions available');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
});

function fillModalBodyDummy(text) {
   
    const transactionDiv = document.createElement('div');
    transactionDiv.innerHTML = `<div class="alert alert-info" role="alert" style="font-weight:500;text-align:center;">
        ${text}
    </div>`;
    const modalBody = document.getElementById("RecentModalbody");
    modalBody.appendChild(transactionDiv);
}


function toggleAddMoneySection() {
    const addMoneySection = document.getElementById('AddMoneySection');
    const addMoneyButton = document.querySelector('[onclick="toggleAddMoneySection()"]');
    const proceedButton = document.getElementById('proceedButton');

    if (addMoneySection.style.display === 'none') {
        addMoneySection.style.display = 'block';
        addMoneyButton.style.display = 'none';
        proceedButton.style.display = 'block';
    } else {
        addMoneySection.style.display = 'none';
        addMoneyButton.style.display = 'block';
        proceedButton.style.display = 'none';
    }
}

function processAddMoney() {
    const amountInput = document.getElementById('amount');
    const amount = parseInt(amountInput.value);
    // Check if the entered amount is a valid integer within the specified range
    if (Number.isInteger(amount) && amount >= 100 && amount <= 5000) {
        process_add_money(amount) ;
       
    } else {
        
        amountInput.value = ''; // Clear the input field
    }
}




async function process_add_money(amount) {
    event.preventDefault();
    
    var data = {
        Type: "Add Money",
        Amount: amount
    };

    try {
        // Send the POST request using await fetch
        const response = await fetch('/pay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            // Response status is OK, check if it's a redirection
            if (response.redirected) {
                window.location.href = '/complete_payment';
            } else {
                // Handle other successful responses if needed
            }
        } else {
            // Handle other response statuses (e.g., 404, 500) if needed
            console.error('Response status:', response.status);
        }
    } catch (error) {
        console.error("Error:", error);
    }
}



function formatToTwoDecimalPlaces(number) {
    return parseFloat(number).toFixed(2);
}


function Reset() {
    // JavaScript for handling Reset PIN button click
    var resetPinButton = document.getElementById('ResetPinButton');
    var resetPinFields = document.getElementById('ResetPinFields');
   
    resetPinFields.style.display = 'block'; // Show the input fields
    resetPinButton.style.display = 'none'; // Hide the Reset PIN button
    document.getElementById('Gobutton').style.display='none';
    var cancel=document.getElementById('cancelButton');
    cancel.style.display = 'inline-block';
    cancel.addEventListener(
        'click', reset_style
    );
    // JavaScript for handling Confirm button click
    var confirmButton = document.getElementById('confirmButton');
    confirmButton.style.display ='inline-block';
    
    confirmButton.addEventListener('click', function () {
        try {
            var newPin = document.getElementById('NewPinInput').value;
            var confirmPin = document.getElementById('ConfirmPinInput').value;
        } catch (error) {
            return;
        }

        if (newPin.length !== 4 || confirmPin.length !== 4) {
            return;
        }

        //console.log("Sending new PIN:", newPin);

        // Check if the entered PINs match and have 4 digits
        if (newPin.length === 4 && newPin === confirmPin) {
            // Prepare the data object to send as JSON
            var data = {
                New: newPin
            };

            fetch('/Forgot_wallet_pass', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
                .then(function (response) {
                    
                    if (response.ok) {
                        document.getElementById("Default_pin").innerHTML = `<div class="alert alert-success" role="alert">
                            PIN Reset Successful !</div>`
                        reset_style();
                    } else {
                        // Handle error response from the server
                        console.error('Failed to reset PIN. Server returned an error.');
                        document.getElementById("Default_pin").innerHTML = `<div class="alert alert-danger" role="alert">
                                        Failed to Reset PIN !</div>`
                        reset_style();
                    }
                })
                .catch(function (error) {
                    console.error('Failed to reset PIN. Error:', error);
                    document.getElementById("Default_pin").innerHTML = `<div class="alert alert-danger" role="alert">
                                        Failed to Reset PIN !</div>`
                    reset_style();
                });
        } else {
            reset_style();
        }
    });

    function reset_style(){
        $('#ConfirmPinInput').val('');
        $('#NewPinInput').val('');
        resetPinFields.style.display = 'none'; // Hide the input fields
        resetPinButton.style.display = 'inline-block'; // Show the Reset PIN button again
        cancel.style.display = 'none';
        confirmButton.style.display='none';
        document.getElementById('Gobutton').style.display = 'inline-block';
    }
}

$(document).ready(function () {
    // Add event listener to the New PIN input field
    $('#NewPinInput').on('input', function () {
        var value = $(this).val();

        // Remove non-numeric characters and ensure the value is a positive integer
        value = value.replace(/\D/g, ''); // Remove non-numeric characters

        value = parseInt(value, 10); // Convert to integer

        if (isNaN(value) || value <= 0) {
            value = ''; // Reset to empty if not a positive integer
        } else if (value > 9999) {
            value = $(this).val().slice(0, 4); // Limit to 4-digit positive integer
        }
        if (String(value).length == 4) {
            $('#ConfirmPinInput').focus();
        }
        $(this).val(value);
        
    });

    // Add event listener to the Confirm PIN input field
    $('#ConfirmPinInput').on('input', function () {
        var value = $(this).val();

        // Remove non-numeric characters and ensure the value is a positive integer
        value = value.replace(/\D/g, ''); // Remove non-numeric characters
        value = parseInt(value, 10); // Convert to integer

        if (isNaN(value) || value <= 0) {
            value = ''; // Reset to empty if not a positive integer
        } else if (value > 9999) {
            value = $(this).val().slice(0, 4); // Limit to 4-digit positive integer
        }

        $(this).val(value);
    });
});


function Newadmin(){
    document.getElementById('proceedbutton3').style.display='none';
    document.getElementById('EnterPasscode').style.display="block";
    document.getElementById('confirmbutton').style.display='inline-block';
    document.getElementById("warning").innerHTML = `<div class="alert alert-danger" role="alert" style="font-size:15px;color:black;text-align:left;">
       Anyone selected to become <strong>ADMIN</strong> will now have Admin powers!!<br>
       Any user with Email marked red will be <strong>SUSPENDED</strong>.<br>
       Enter your Passcode below and Confirm.</div>`;
}


function deladmin() {
    document.getElementById('proceedbutton2').style.display = 'none';
    document.getElementById('EnterPasscode2').style.display = "block";
    document.getElementById('confirmbutton2').style.display = 'inline-block';
    document.getElementById("warning2").innerHTML = `<div class="alert alert-danger" role="alert" style="color:black;font-weight:500;text-align:center;">
       Anyone selected will now become a normal user!!<br>Enter your Passcode below and Confirm.</div>`
}

function reset_modal(){
    try{
        document.getElementById('proceedbutton3').style.display = 'inline-block';
        document.getElementById('confirmbutton').style.display = 'none';
        document.getElementById('EnterPasscode').style.display = "none";
        document.getElementById("warning").innerHTML = '';
    }catch{null;}
    }
    


function reset_modal2() {
    try{
        document.getElementById('proceedbutton2').style.display = 'inline-block';
        document.getElementById('confirmbutton2').style.display = 'none';
        document.getElementById('EnterPasscode2').style.display = "none";
        document.getElementById("warning2").innerHTML = '';
    }catch{
        null;
    }
    
}


function reset_modal3() {
    try {
        $('#proceedbutton5').prop('disabled', true);
        $('#ADDnew').prop('disabled',false);
        document.getElementById('proceedbutton5').style.display = 'inline-block';
        document.getElementById('confirmbutton5').style.display = 'none';
        document.getElementById('EnterPasscode5').style.display = "none";
        document.getElementById("warnDiscountchange").innerHTML = `<div class="alert alert-danger" role="alert" style="color:black;font-weight:500;text-align:center;">
               The Discount rates will be changed on confirmation.
    </div > `;
        document.getElementById('NewCoupon').style.display = 'none';
        document.getElementById('EnterNewRate').style.display = 'none';
}catch{
    null;
}
    
}


function change_toll_modal() {
    document.getElementById('proceedbutton4').style.display = 'inline-block';
    document.getElementById('confirmbutton4').style.display = 'none';
    document.getElementById('EnterPasscode4').style.display = "none";
    document.getElementById("warnTollchange").innerHTML =`<div class="alert alert-danger" role="alert" style="color:black;font-weight:500;text-align:center;">
               The Toll rates will be changed. Be careful !!
    </div>`;
}

function change_toll(){
    document.getElementById('proceedbutton4').style.display = 'none';
    document.getElementById('confirmbutton4').style.display = 'inline-block';
    document.getElementById('EnterPasscode4').style.display = "block";
    document.getElementById("warnTollchange").innerHTML = `<div class="alert alert-danger" role="alert" style="color:black;font-weight:500;text-align:center;">
        You are about to change the Toll Rates !!
    </div>`;
}

function getSelectedEmails() {
    var selectedEmails = [];
    $('#CreateAdmin .admin-checkbox:checked').each(function () {
        var emailId = $(this).data('email'); // Get the data-email attribute
        selectedEmails.push(emailId);
    });

    return  selectedEmails ;
}


function getSelectedEmails2() {
    var selectedEmails = [];
    $('#DeleteAdmin input[type="checkbox"]:checked').each(function () {
        var listItem = $(this).closest('li');
        var email = listItem.find('span#Emailid').text();
        selectedEmails.push(email);
    });

    return { data: selectedEmails };
}



function modify_users() {
    // Get the passcode from the input field
    var passcode = $("#passcode").val();
    if (passcode.length != 4) 
        return;
    // Get the selected emails using the previously defined function
    var selectedEmails = getSelectedEmails();
    var activated = getActivatedEmails();
    var suspended = getSuspendedEmails();
    
    

    // Create the JSON object with the required format
    var dataToSend = {
        data: selectedEmails,
        suspend:suspended,
        activate:activated,
        Password: passcode
    };
    
    $.ajax({
        type: "POST",
        url: "/make_admin", // Replace with the actual URL
        data: JSON.stringify(dataToSend),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
            // Handle the success response here
            document.getElementById("CreateAdmin").dataset = false;
            //console.log("Admins created successfully:", response);
            var warningElement = document.getElementById("warning");
            warningElement.innerHTML = `<div class="alert alert-success" role="alert" style="color:black;font-weight:500;text-align:center;">
                ${response.message}
            </div>`;
            //reset_modal();
            setTimeout(function(){location.reload()},1700);
            // Optionally, you can perform additional actions after a successful request.
        },
        error: function (error) {
            // Handle any errors that occur during the AJAX request
            console.error("Error creating admins:", error.responseJSON);
            var warningElement = document.getElementById("warning");
            warningElement.innerHTML = `<div class="alert alert-danger" role="alert" style="color:black;font-weight:500;text-align:center;">
                ${error.responseJSON.message}
            </div>`;
            
        }
    });
}



function delete_admin() {
    // Get the passcode from the input field
    var passcode = $("#passcode2").val();
    if (passcode.length != 4)
        return;
    // Get the selected emails using the previously defined function
    var selectedEmails = getSelectedEmails2();
    if (selectedEmails.data.length == 0) {
        reset_modal2();
        return;
    }

    // Create the JSON object with the required format
    var dataToSend = {
        data: selectedEmails.data,
        Password: passcode
    };

    $.ajax({
        type: "POST",
        url: "/delete_admin", // Replace with the actual URL
        data: JSON.stringify(dataToSend),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
            // Handle the success response here
            document.getElementById("DeleteAdmin").dataset = false;
            //console.log("Admins deleted successfully:", response);
            var warningElement = document.getElementById("warning2");
            warningElement.innerHTML = `<div class="alert alert-success" role="alert" style="color:black;font-weight:500;text-align:center;">
                ${response.message}
            </div>`;
            setTimeout(function () { location.reload() }, 1700);
            // Optionally, you can perform additional actions after a successful request.
        },
        error: function (error) {
            // Handle any errors that occur during the AJAX request
            console.error("Error deleting admins:", error.responseJSON);
            var warningElement = document.getElementById("warning2");
            warningElement.innerHTML = `<div class="alert alert-danger" role="alert" style="color:black;font-weight:500;text-align:center;">
                ${error.responseJSON.message}
            </div>`;
            // Optionally, you can display an error message or take corrective actions.
        }
    });
}


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

function resetToOriginal(dataItem, originalItem) {
    for (const category of ["single", "return", "monthly"]) {
        dataItem[category] = originalItem[category];
    }
}

var dataArray=[];
function populateTable(jsonData) {
    // Get the table body element
    dataArray = [];
    var originalDataArray = JSON.parse(JSON.stringify(jsonData));
    const tableBody = document.getElementById("TollTableBody");
  
    for (const vehicleType in jsonData) {
        const vehicleData = jsonData[vehicleType];
        dataArray.push({
            vehicleType: vehicleType,
            ...vehicleData,
        });
        
    }
    
    // Sort the array by the "single" category in ascending order
    dataArray.sort((a, b) => a.single - b.single);

    // Iterate through the sorted array and create table rows
    dataArray.forEach((dataItem) => {
        const newRow = document.createElement("tr");

        const vehicleTypeCell = document.createElement("td");
        vehicleTypeCell.textContent = formatVehicleTypeName(dataItem.vehicleType);
        vehicleTypeCell.style.paddingLeft="15px";
        newRow.appendChild(vehicleTypeCell);

        // Create a cell for each rate category
        ["single", "return", "monthly"].forEach((category) => {
            const cell = document.createElement("td");

            // Create a container div to hold the input and original value
            const container = document.createElement("div");
            container.className = "input-group";

            // Create an input element
            const input = document.createElement("input");
            input.type = "number";
            
            input.value = dataItem[category];
            input.className = "form-control"; // You can add Bootstrap classes for styling
            input.min = 1;
            // Create a span to display the original value
            const originalValueSpan = document.createElement("span");
            originalValueSpan.className = "input-group-text";
            var vehicle = dataItem.vehicleType;
            originalValueSpan.textContent = originalDataArray[vehicle][category];

            input.addEventListener("input", (event) => {
                // Ensure the input is a valid positive number
                const newValue = parseFloat(event.target.value);

                if (isNaN(newValue) || newValue <= 0) {
                    event.target.value = '';
                    // Reset to the original value from originalDataArray
                    dataItem[category] = originalDataArray[vehicle][category];
                    $('#proceedbutton4').prop('disabled', true);
                } else {
                    $('#proceedbutton4').prop('disabled', false);
                    dataItem[category] = newValue;
                }
                
            });

            // Append the input and original value to the container
            container.appendChild(input);
            container.appendChild(originalValueSpan);

            // Append the container to the cell
            cell.appendChild(container);
            newRow.appendChild(cell);
        });

        tableBody.appendChild(newRow);
    });
}


function change_toll_Rate(){
    const passcode = parseInt(document.getElementById("passcode4").value);
    if(String(passcode).length!=4){
        return;
    }
    change_toll_rate(passcode);
}

function change_toll_rate(passcode) {
    const url = "/update_toll_rate"; // Replace with the actual URL of your Flask endpoint
    const payload = {
        Password: passcode, // Replace with your actual password
        dataArray: dataArray, // The data array you want to update
    };
    const warningElement = document.getElementById('warnTollchange');
    $.ajax({
        url: url,
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify(payload),
        success: function (data) {
            if (data && data.message) {
                document.getElementById("TollTableBody").dataset=false;
                // Update the warningElement with the response message
                warningElement.innerHTML = `<div class="alert alert-success" role="alert" style="color:black;font-weight:500;text-align:center;">
                ${data.message}</div>`;
                console.log(data.message);
                setTimeout(function () { location.reload() }, 1700);
            } else {
                console.error("Response does not contain a message.");
            }
        },
        error: function (error) {
            // Handle any errors that occur during the AJAX request
            console.error("Error changing Toll rate:", error.responseJSON);
            warningElement.innerHTML = `<div class="alert alert-danger" role="alert" style="color:black;font-weight:500;text-align:center;">
                ${error.responseJSON.message}
            </div>`;
            // Optionally, you can display an error message or take corrective actions.
        }
    });
}

var originalData,currentData;
function change_Discounts(){
    $.ajax({
        url: '/get_cupons',
        type: 'GET',
        dataType: 'json',
        success: function (data) {
            const discountsTable = $('#DiscountTableBody');
            if (data.success && data.data && data.data.length > 0) {
                originalData = JSON.parse(JSON.stringify(data.data));
                currentData = JSON.parse(JSON.stringify(data.data));
                var delCount = 0;
                $.each(data.data, function (index, coupon) {
                    const [couponName, currentRate] = coupon;
                    const newRow = document.createElement("tr");
                    newRow.style.justifyContent ="space-around";
                    const Couponcell = document.createElement("td");
                    Couponcell.textContent = couponName.toUpperCase();
                    Couponcell.style.paddingLeft = "3em";
                    newRow.appendChild(Couponcell);
                    const containerparent = document.createElement("td");
                    containerparent.style.paddingLeft = "2em";
                    const container = document.createElement("div");
                    container.style.maxWidth = "6em";
                    container.style.minWidth = "3em";
                    container.className = "input-group";

                    // Create an input element
                    const input = document.createElement("input");
                    input.type = "number";

                    input.value = currentRate;
                    input.className = "form-control"; // You can add Bootstrap classes for styling
                    input.min = 1;
                    input.max=100;
                    // Create a span to display the original value
                    const container2parent = document.createElement("td");
                    container2parent.style.paddingLeft = "2em";
                    const container2 = document.createElement("div");
                    
                    container2.style.maxWidth="6em";
                    container2.style.minWidth = "3em";
                    const originalValueSpan = document.createElement("span");
                    originalValueSpan.className = "input-group-text";
                    originalValueSpan.style.paddingLeft='2.1em';
                    originalValueSpan.textContent = parseInt(originalData[index][1])+'%';
                    
                    // Add a delete button
                    const container3 = document.createElement("td");
                    const deleteButton = document.createElement("button");
                    deleteButton.style.marginTop='5px';
                    deleteButton.textContent = "Delete";
                    deleteButton.className = "btn btn-danger btn-sm ";
                    
                    deleteButton.addEventListener("click", function () {
                        if (deleteButton.textContent === "Delete"){
                            delCount++;
                            Couponcell.style.color = "red";
                            currentData[index][1] = -99;
                            originalValueSpan.style.background = 'red';
                            originalValueSpan.style.color = 'white';
                            $('#proceedbutton5').prop('disabled', false);
                            deleteButton.textContent = "Cancel";
                            deleteButton.className = "btn btn-info btn-sm ";
                            document.getElementById('warnDiscountchange').innerHTML =`<div class="alert alert-danger" role="alert" style="color:black;font-weight:500;text-align:center;">
                               The Cupons marked Red will be Deleted
                            </div>`;
                            
                        }else{
                            delCount--;
                            Couponcell.style.color = "";
                            currentData[index][1] = originalData[index][1];
                            originalValueSpan.style.background = '';
                            originalValueSpan.style.color = '';
                            if(delCount==0){
                                $('#proceedbutton5').prop('disabled', true);
                                document.getElementById('warnDiscountchange').innerHTML = `<div class="alert alert-danger" role="alert" style="color:black;font-weight:500;text-align:center;">
                                    The Discount rates will be changed on confirmation.
                                </div>`;
                            }
        
                            deleteButton.textContent = "Delete";
                            deleteButton.className = "btn btn-danger btn-sm ";
                        }
                        
                    });

                    input.addEventListener("input", (event) => {
                        // Ensure the input is a valid positive number

                        const newValue = parseFloat(event.target.value);
                        if (event.target.value.length>2){
                            $('#proceedbutton5').prop('disabled', false);
                            event.target.value='100';
                            currentData[index][1] =100;
                        }
                        else if (isNaN(newValue) || newValue <= 0) {
                            event.target.value = '';
                            // Reset to the original value from originalDataArray
                            currentData[index][1] = originalData[index][1];
                            $('#proceedbutton5').prop('disabled', true);
                        } else {
                            $('#proceedbutton5').prop('disabled', false);
                            const Value = parseFloat(event.target.value);
                            currentData[index][1] = Value;
                        }
                        
                      
                    });

                    // Append the input and original value to the container
                    container.appendChild(input);
                    container2.appendChild(originalValueSpan);
                    containerparent.appendChild(container);
                    container2parent.appendChild(container2);
                    newRow.appendChild(containerparent);
                    newRow.appendChild(container2parent);
                    container3.appendChild(deleteButton);
                    newRow.appendChild(container3);
                    discountsTable.append(newRow);
                });
                
            } else {
                // Handle the case where there are no coupons or an error occurred
                const noDiscountsMessage = $('<p>').text('No coupons available');
                discountsTable.append(noDiscountsMessage);
            }
        },
        error: function (error) {
            console.error('Error:', error);
        },
    });
}

function changeCupon(){
    document.getElementById('EnterPasscode5').style.display = "block";
    document.getElementById('proceedbutton5').style.display = 'none';
    document.getElementById('confirmbutton5').style.display = 'inline-block';
    
    document.getElementById("warnDiscountchange").innerHTML = `<div class="alert alert-danger" role="alert" style="color:black;font-weight:500;text-align:center;">
        You are about to change Discount rates!! <br> Provide passcode below to confirm.
    </div>`;
}

function change_cupon_rate(){
    const passcode = parseInt(document.getElementById("passcode5").value);
    if (String(passcode).length != 4) {
        return;
    }
}

function add_new_cupon(){
    try{
        document.getElementById('NewCoupon').style.display = 'block';
        $('#ADDnew').prop('disabled', true);
    }catch{null;}
   
}

function change_global(){
    if (document.getElementById("globalChange").innerText=="Change"){
        document.getElementById('EnterNewRate').style.display = 'block';
        document.getElementById("globalChange").innerText = "Cancel";
    }
    else{
        document.getElementById('EnterNewRate').style.display = 'none';
        document.getElementById("globalChange").innerText = "Change";
    }
}

function change_discount_rate(){
    var globalRate = document.getElementById("GlobalRate").value;
    var couponName = document.getElementById('cuponName').value;
    var newcuponRate = document.getElementById('cuponRate').value;
    var Rate = parseInt(globalRate);
    var cuponRate=parseInt(newcuponRate);
    if (globalRate.length == 0 || isNaN(Rate) || Rate >= 100 || Rate < 0) {
        Rate = -1;
    }
    if(newcuponRate.length==0||cuponRate<=0||cuponRate>100){
        cuponRate=0;
    }
    //console.log(Rate,currentData,couponName,cuponRate);
    const passcode=document.getElementById('passcode5').value;
    if(passcode.length!=4||isNaN(parseInt(passcode))){
        return;
    }
    var payload={
        Global:Rate,
        Password:passcode,
        NewCupon:couponName,
        NewRate:cuponRate,
        TollRate: convertToKeyValuePairs(currentData)
    }
    //console.log(payload);
    var warningElement = document.getElementById("warnDiscountchange");
    $.ajax({
        url: '/modify_discounts',
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify(payload),
        success: function (data) {
            //console.log(data.message);
            warningElement.innerHTML = `<div class="alert alert-success" role="alert" style="color:black;font-weight:500;text-align:center;">
                ${data.message}</div>`;
            setTimeout(function () { location.reload() }, 1700);
        },
        error: function (error) {
            // Handle any errors that occur during the AJAX request
            warningElement.innerHTML = `<div class="alert alert-danger" role="alert" style="color:black;font-weight:500;text-align:center;">
                ${error.responseJSON.message}
            </div>`;
            // Optionally, you can display an error message or take corrective actions.
        }
    });
}

function convertToKeyValuePairs(twoDList) {
    const keyValuePairs = {};

    for (let i = 0; i < twoDList.length; i++) {
        const row = twoDList[i];
        if (row.length >= 2) {
            const key = row[0];
            const value = row[1];
            keyValuePairs[key] = value;
        }
    }
    //console.log(keyValuePairs);
    return keyValuePairs;
    
}

function getSuspendedEmails() {
    var selectedEmails = [];
    $('#CreateAdmin .suspend-checkbox:checked').each(function () {
        const email = $(this).data('email');
        selectedEmails.push(email);
    });
    //console.log(selectedEmails);
    return selectedEmails;
}

function getActivatedEmails() {
    var selectedEmails = [];
    $('#CreateAdmin .activate-checkbox:checked').each(function () {
        const email = $(this).data('email');
        selectedEmails.push(email);
    });
    //console.log(selectedEmails);
    return selectedEmails;
}
