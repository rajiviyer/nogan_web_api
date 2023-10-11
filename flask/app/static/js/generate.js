// function updateTextInput(val) {
//     document.getElementById("numRows").value=val; 
//   }

function displayActionElements(val) {
    // const actionName = document.getElementsByName("action").value;
    const actionName = val;    
    var valNumNodesLabel = document.querySelector('label[name="valNumNodesLabel"]');
    var genNumRowsLabel = document.querySelector('label[name="genNumRowsLabel"]');
    var genKSStatsLabel = document.querySelector('label[name="genKSStatsLabel"]');
    var genNumNodesLabel = document.querySelector('label[name="genNumNodesLabel"]');
    var genKSStatsInput = document.querySelector('input[name="genKSStats"]');
    var genNumNodesInput  = document.querySelector('input[name="genNumNodes"]');
    var genNumRowsInput = document.querySelector('input[id="genNumRows"]');
    var valNumNodes = document.querySelector('input[id="valNumNodes"]');    
    // var rangeInput = document.querySelector('input[id="genRangeInput"]');
    var submitButton = document.querySelector('input[type="submit"]');    
    // console.log("test");
    // console.log(actionName);
    if (actionName == "validate") {
      genNumRowsLabel.style.display = 'none';
      genNumRowsInput.style.display = 'none';
      genKSStatsLabel.style.display = 'none';     
      genKSStatsInput.style.display = 'none';
      genNumNodesLabel.style.display = 'none';
      genNumNodesInput.style.display = 'none';
      // rangeInput.style.display = 'none';
      valNumNodesLabel.style.display = 'inline-block';
      valNumNodes.style.display = 'inline-block';      
      submitButton.value = 'Validate'; 
      submitButton.style.marginTop = '5px'; // Adjust the margin      
    }
    else {
      genNumRowsLabel.style.display = 'inline-block';
      genNumRowsInput.style.display = 'inline-block';
      genKSStatsLabel.style.display = 'inline-block';      
      genKSStatsInput.style.display = 'inline-block';
      if (genKSStatsInput.checked) {
        genNumNodesLabel.style.display = 'inline-block';      
        genNumNodes.style.display = 'inline-block';
      }      
      // rangeInput.style.display = 'inline-block';
      valNumNodesLabel.style.display = 'none'; 
      valNumNodes.style.display = 'none';          
      submitButton.value = 'Generate';
      submitButton.style.marginTop = '0'; // Reset the margin            
    }
}

function displayGenNumNodes() {
    var genKSStatsInput = document.querySelector('input[name="genKSStats"]');
    var genNumNodesLabel = document.querySelector('label[name="genNumNodesLabel"]');
    var genNumNodes = document.querySelector('input[name="genNumNodes"]');
  
    if (genKSStatsInput.checked) {
      genNumNodesLabel.style.display = 'inline-block';      
      genNumNodes.style.display = 'inline-block';
    }
    else {
      genNumNodesLabel.style.display = 'none';          
      genNumNodes.style.display = 'none';
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

  if (selectedOptions.length > 0) {
    // If some selected, create a single entry called "Cat_Cols"
    jsonBinsData['cat_cols'] = 100;
    jsonStretchTypeData['cat_cols'] = 'Uniform';
    jsonStretchValData['cat_cols'] = 1.0;
  }

  document.getElementById('binsText').value = JSON.stringify(jsonBinsData, null, 2);
  document.getElementById('StretchTypeText').value = JSON.stringify(jsonStretchTypeData, null, 2);
  document.getElementById('stretchValText').value = JSON.stringify(jsonStretchValData, null, 2);
}

// function clearMessages() {
//   document.getElementById('success').classList.add('hidden');     
//   document.getElementById('successDiv').classList.add('hidden');
  
//   document.getElementById('error').classList.add('hidden');     
//   document.getElementById('errorDiv').classList.add('hidden');  
// }

document.querySelector('form').addEventListener('submit', function(e) {
  e.preventDefault();
  document.getElementById('success').classList.add('hidden');
  document.getElementById('error').classList.add('hidden');
  document.getElementById('successDiv').classList.add('hidden');
  document.getElementById('errorDiv').classList.add('hidden');
  fetch('/generate', {
      method: 'POST',
      body: new FormData(e.target)
  })
  .then(response => response.json())
  .then(data => {
      if (data.success_message && data.success_message.trim() != '') {
        document.getElementById('successDiv').classList.remove('hidden');
        document.getElementById('success').classList.remove('hidden');
        document.getElementById('success').textContent = data.success_message;
      }
      else {
        document.getElementById('success').classList.add('hidden');     
        document.getElementById('successDiv').classList.add('hidden');
      }
      
      if (data.error_message && data.error_message.trim() != '') {
        document.getElementById('errorDiv').classList.remove('hidden');
        document.getElementById('error').classList.remove('hidden');
        document.getElementById('error').textContent = data.error_message;
      }
      else {
        document.getElementById('error').classList.add('hidden');
        document.getElementById('errorDiv').classList.add('hidden');             
      }      
  
      if (data.file_location && data.file_location.trim() != '') {
        document.getElementById('fileLocation').classList.remove('hidden');
        document.getElementById('fileLocation').href = data.file_location;
      }
      else {
        document.getElementById('fileLocation').classList.add('hidden');        
      }        
  });
});