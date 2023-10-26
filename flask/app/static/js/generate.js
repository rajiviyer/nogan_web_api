function displayActionElements(val) {
    const actionName = val;    
    var valNumNodesDiv = document.querySelector('div[id="valNumNodesDiv"]')
    var genNumRowsDiv = document.querySelector('div[id="genNumRowsDiv"]')
    var genKSStatsDiv = document.querySelector('div[id="genKSStatsDiv"]')
    var genNumNodesLabel = document.querySelector('label[name="genNumNodesLabel"]');
    var genKSStatsInput = document.querySelector('input[name="genKSStats"]');
    var genNumNodes  = document.querySelector('input[name="genNumNodes"]');
    var submitButton = document.querySelector('input[type="submit"]');

    if (actionName == "validate") {
      genNumRowsDiv.classList.add("hidden");
      genKSStatsDiv.classList.add("hidden");
      valNumNodesDiv.classList.remove("hidden");    
      submitButton.value = 'Validate';    
    }
    else {
      genNumRowsDiv.classList.remove("hidden");      
      genKSStatsDiv.classList.remove("hidden");      
      if (genKSStatsInput.checked) {
        genNumNodesLabel.classList.remove("hidden");
        genNumNodes.classList.remove("hidden");
      }      
      valNumNodesDiv.classList.add("hidden");
      submitButton.value = 'Generate';       
    }
}

function displayGenNumNodes() {
    var genKSStatsInput = document.querySelector('input[name="genKSStats"]');
    var genNumNodesLabel = document.querySelector('label[name="genNumNodesLabel"]');
    var genNumNodes = document.querySelector('input[name="genNumNodes"]');
  
    if (genKSStatsInput.checked) {
      genNumNodesLabel.classList.remove("hidden");
      genNumNodes.classList.remove("hidden");
    }
    else {
      genNumNodesLabel.classList.add("hidden");
      genNumNodes.classList.add("hidden");
    }
}

function displayBins() {
  var binsInput = document.querySelector('input[name="bins"]');
  var binsText = document.querySelector('div[name="divBinText"]');

  if (binsInput.checked) {
    binsText.classList.remove('hidden');
  }
  else {
    binsText.classList.add('hidden');
  }
}

function displayStretchType() {
  var stretchTypeInput = document.querySelector('input[name="stretchType"]');
  var stretchTypeText = document.querySelector('div[name="divStretchTypeText"]');

  if (stretchTypeInput.checked) {
    stretchTypeText.classList.remove('hidden');
  }
  else {
    stretchTypeText.classList.add('hidden');
  }

}

function displayStretchVal() {
  var stretchValInput = document.querySelector('input[name="stretchVal"]');
  var stretchValText = document.querySelector('div[name="divStretchValText"]');

  if (stretchValInput.checked) {
    stretchValText.classList.remove('hidden');
  }
  else {
    stretchValText.classList.add('hidden');
  }
}

function generateJSON() {
  const selectedOptions = Array.from(document.getElementById('category_columns').selectedOptions);
  const allOptions = document.getElementById('category_columns').options;
  const nonNumColsCount = document.getElementById('nonNumColsCount').value;
  const jsonBinsData = {};
  const jsonStretchTypeData = {};
  const jsonStretchValData = {};


  for (let i = 0; i < allOptions.length; i++) {
    const option = allOptions[i];
    if (!selectedOptions.includes(option)) {
      jsonBinsData[option.value] = 100;
      jsonStretchTypeData[option.value] = 'Uniform';
      jsonStretchValData[option.value] = 1.0;
    }
  }

  if (selectedOptions.length > 0 || nonNumColsCount > 0) {
    jsonBinsData['cat_cols'] = 100;
    jsonStretchTypeData['cat_cols'] = 'Uniform';
    jsonStretchValData['cat_cols'] = 1.0;
  }

  document.getElementById('binsText').value = JSON.stringify(jsonBinsData, null, 2);
  document.getElementById('StretchTypeText').value = JSON.stringify(jsonStretchTypeData, null, 2);
  document.getElementById('stretchValText').value = JSON.stringify(jsonStretchValData, null, 2);
}

const socket = io();

// Add this code to your generate.js
const progressDiv = document.getElementById('progress-div');
const progressStatus = document.getElementById('progress-status');
const progressBar = document.getElementById('progress-bar');
const successDiv = document.getElementById('successDiv');
const success = document.getElementById('success');
const errorDiv = document.getElementById('errorDiv');
const error = document.getElementById('error');

document.querySelector('form').addEventListener('submit', function(e) {
  e.preventDefault();
  successDiv.classList.add('hidden');
  errorDiv.classList.add('hidden');
  success.textContent = '';
  error.textContent = '';
  progressDiv.classList.remove('hidden');
  progressStatus.innerText = "";

  fetch('/generate', {
      method: 'POST',
      body: new FormData(e.target)
  })
  .then(response => response.json())
  .then(data => {
      if (data.type == "error" && data.message.trim() != '') {
        progressDiv.classList.add('hidden');
        errorDiv.classList.remove('hidden');
        error.textContent = data.message;
      }
      else {
        errorDiv.classList.add('hidden');
      }
  });
});

// Listen for progress updates
socket.on('update_progress', function(data) {
  // console.log(data)
  progressBar.setAttribute("style", `width: ${data.progress_perc}%`);
  progressStatus.innerText = data.progress;
});

// Listen for message updates (success or error)
socket.on('update_message', function(data) {
  if (data.type === 'success') {
    console.log(`Success ${data.message}`);
    progressDiv.classList.add('hidden');
    successDiv.classList.remove('hidden');
    success.innerHTML = data.message;
  } else if (data.type === 'error') {
    console.log(`Error ${data.message}`);    
    progressDiv.classList.add('hidden');
    errorDiv.classList.remove('hidden');
    error.textContent = data.message;
  }
});


// document.querySelector('form').addEventListener('submit', function(e) {
//   e.preventDefault();
//   document.getElementById('success').classList.add('hidden');
//   document.getElementById('error').classList.add('hidden');
//   document.getElementById('successDiv').classList.add('hidden');
//   document.getElementById('errorDiv').classList.add('hidden');
//   document.getElementById('success').textContent = '';
//   document.getElementById('error').textContent = '';
//   document.getElementById('progress').classList.remove('hidden');  
//   fetch('/generate', {
//       method: 'POST',
//       body: new FormData(e.target)
//   })
//   .then(response => response.json())
//   .then(data => {
//       if (data.success_message && data.success_message.trim() != '') {
//         document.getElementById('progress').classList.add('hidden');        
//         document.getElementById('successDiv').classList.remove('hidden');
//         document.getElementById('success').classList.remove('hidden');
//         document.getElementById('success').innerHTML = data.success_message;
//       }
//       else {
//         document.getElementById('success').classList.add('hidden');     
//         document.getElementById('successDiv').classList.add('hidden');     
//       }
      
//       if (data.error_message && data.error_message.trim() != '') {
//         document.getElementById('progress').classList.add('hidden');         
//         document.getElementById('errorDiv').classList.remove('hidden');
//         document.getElementById('error').classList.remove('hidden');
//         document.getElementById('error').textContent = data.error_message;
//       }
//       else {
//         document.getElementById('error').classList.add('hidden');
//         document.getElementById('errorDiv').classList.add('hidden');
//       }      
  
//       if (data.file_location && data.file_location.trim() != '') {
//         document.getElementById('fileLocation').classList.remove('hidden');
//         document.getElementById('fileLocation').href = data.file_location;
//       }
//       else {
//         document.getElementById('fileLocation').classList.add('hidden');      
//       }
//   });
// });

// Add an event listener to call the function when the page loads
window.addEventListener("load", function() {
  generateJSON();
  displayActionElements("generate");
});
