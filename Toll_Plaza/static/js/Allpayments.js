

async function Process_Toll_pay() {
    event.preventDefault();
    var Vehicle_Type = document.getElementById("vehicleType").value;
    var Journey = document.getElementById("JourneyType").value;
    var Vehicle_Number = document.getElementById("registrationNumber").value;

    if (!Vehicle_Type || !Vehicle_Number || !Journey) {
        return;
    }

    // Create an object with the data you want to send to the /pay endpoint
    var data = {
        Type: "Toll Payment",
        Vehicle_Type: Vehicle_Type,
        Journey: Journey,
        Vehicle_Number: Vehicle_Number
    };
    console.log(data);
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

async function Check_and_apply() {
    const coupon = document.getElementById("cuponCode").value.toLowerCase().trim();
    if(coupon.length<=3 ||coupon.length>=10){
        return;
    }
    try {
        const response = await fetch('/Apply_coupon', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({'cupon': coupon }),
        });

        if (response.ok) {
            const responseData = await response.json();

                if (responseData.success) {
                    // Coupon applied successfully
                    const PaymentInfo = responseData.Data;
                    const formattedCupon = formatToTwoDecimalPlaces(PaymentInfo.Cupon);
                    const formattedTotal = formatToTwoDecimalPlaces(PaymentInfo.Amount + PaymentInfo.Gst - PaymentInfo.Cupon - PaymentInfo.GlobalDiscount);
                    document.getElementById("paymentInfoCupon").innerHTML = `&#8377;${formattedCupon}`;
                    document.getElementById("paymentInfoTotal").innerHTML = `&#8377;${formattedTotal}`;
                } else {
                    // Handle the case where coupon application was not successful
                    console.error('Coupon application failed');
                }
        } else {
            // Handle the case where the fetch request itself was not successful (e.g., network error)
            console.error('Fetch request failed with status ' + response.status);
        }
    } catch (error) {
        // Handle any other errors that may occur
        console.error('Error:', error);
    }
}

window.addEventListener('load',function(){
  try{
      var val = PaymentInfo.Amount + PaymentInfo.Gst - PaymentInfo.Cupon - PaymentInfo.GlobalDiscount;
      const formattedTotal = formatToTwoDecimalPlaces(val);
      document.getElementById("paymentInfoTotal").innerHTML = `&#8377;${formattedTotal}`;
      
  }catch(error){
    null;
  }
    
})

