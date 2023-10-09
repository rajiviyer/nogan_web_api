function hideTextInput(selectedValue) {
    var delimiterLabel = document.querySelector('label[name="delimLabel"]');
    var delimiterInput = document.querySelector('input[name="delimiter"]');
    var uploadButton = document.querySelector('input[name="uploadButton"]');
    
    if (selectedValue === 'excel') {
        delimiterLabel.style.display = 'none';
        delimiterInput.style.display = 'none';
        // uploadButton.style.marginTop = '10px'; // Adjust the margin

    } else {
        delimiterLabel.style.display = 'inline-block'; // Display the label
        delimiterInput.style.display = 'inline-block'; // Display the input
        // uploadButton.style.marginTop = '0'; // Reset the margin
    }
}

function checkFileSize()
{
    // const max_file_size = 524288000
    const max_file_size = 419430400
    var upl = document.getElementById("fileID");

    if(upl.files[0].size > max_file_size)
    {
       alert("Cannot Upload Files beyond 400 MB Size!");
       upl.value = "";
    }
};

// function checkFileSize() {
//     const fileInput = document.getElementById('fileInput');
//     const customAlert = document.getElementById('customAlert');
//     const customAlertMessage = document.getElementById('customAlertMessage');

//     if (fileInput.files.length > 0) {
//         const fileSize = fileInput.files[0].size;
//         const maxSize = 13631488; // 13 MB (adjust as needed)

//         if (fileSize > maxSize) {
//             customAlertMessage.textContent = 'File size exceeds the maximum allowed size.';
//             customAlert.classList.remove('hidden');
//         } else {
//             customAlertMessage.textContent = 'File size is within the allowed limit.';
//             customAlert.classList.remove('hidden');
//         }
//     }
// }

// function closeCustomAlert() {
//     const customAlert = document.getElementById('customAlert');
//     customAlert.classList.add('hidden');
// }
