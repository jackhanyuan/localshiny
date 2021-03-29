/* global tus */
/* eslint no-console: 0 */

"use strict";

var upload = null;
var uploadIsRunning = false;
var toggleBtn = document.querySelector("#inputGroupFileAddon02");
var input = document.querySelector("input[type=file]");
var progress = document.querySelector(".progress");
var progressBar = progress.querySelector(".progress-bar");
var subButton = document.querySelector("#subButton");
var inputLabel = document.querySelector(".custom-file-label");
var notice = document.querySelector("#emailHelp");
var filenameInput = document.querySelector("#filename");
var usernameInput = document.querySelector("#username");

if (!toggleBtn) {
    throw new Error("Toggle button not found on this page. Aborting upload-demo. ");
}


toggleBtn.addEventListener("click", function (e) {
    e.preventDefault();

    if (upload) {
        if (uploadIsRunning) {
            upload.abort();
            toggleBtn.textContent = "Resume";
            uploadIsRunning = false;
        } else {
            upload.start();
            toggleBtn.textContent = "Pause";
            uploadIsRunning = true;
        }
    } else {
        if (input.files.length > 0) {
            startUpload();
        }
        else {
            input.click();
        }
    }
});

input.addEventListener("change", startUpload);

function startUpload() {
    var file = input.files[0];
    // Only continue if a file has actually been selected.
    // IE will trigger a change event even if we reset the input element
    // using reset() and we do not want to blow up later.
    if (!file) {
        return;
    }

    var endpoint = "/file-upload";
    var chunkSize = 50 * 1024 * 1024;
    var parallelUploads = 1;
    var username = usernameInput.value;
    var filename = file.name;

    if(username) {
        filename = username + "_" + filename;
    }

    toggleBtn.textContent = "Pause";

    var options = {
        endpoint: endpoint,
        chunkSize: chunkSize,
        retryDelays: [0, 1000, 3000, 5000],
        parallelUploads: parallelUploads,
        metadata: {
            filename: filename,
            filetype: file.type
        },
        onError: function (error) {
            if (error.originalRequest) {
                if (window.confirm("Failed because: " + error + "\nDo you want to retry?")) {
                    upload.start();
                    uploadIsRunning = true;
                    return;
                }
            } else {
                window.alert("Failed because: " + error);
            }
            reset();
        },
        onProgress: function (bytesUploaded, bytesTotal) {
            var percentage = (bytesUploaded / bytesTotal * 100).toFixed(2);
            progressBar.style.width = percentage + "%";
            //progressBar.setAttribute("aria-valuenow", percentage.toString());
            progressBar.textContent = percentage + "%";
            console.log(bytesUploaded, bytesTotal, percentage + "%");
        },
        onSuccess: function () {
            subButton.removeAttribute("disabled");
            toggleBtn.setAttribute("disabled", true);
            input.setAttribute("disabled", true);
            inputLabel.textContent = file.name;
            filenameInput.value = filename;
            notice.textContent = notice.textContent + "File successfully uploaded."
            reset();
        }
    };

    upload = new tus.Upload(file, options);
    upload.findPreviousUploads().then((previousUploads) => {
        askToResumeUpload(previousUploads, upload);
        upload.start();
        uploadIsRunning = true;
    });

}

function reset() {
    input.value = "";
    toggleBtn.textContent = "Upload";
    upload = null;
    uploadIsRunning = false;
}


function askToResumeUpload(previousUploads, upload) {
    if (previousUploads.length === 0) return;

    let text = "You tried to upload this file previously at these times:\n\n";
    previousUploads.forEach((previousUpload, index) => {
        text += "[" + index + "] " + previousUpload.creationTime + "\n";
    });
    text += "\nEnter the corresponding number to resume an upload or press Cancel to start a new upload";

    const answer = prompt(text);
    const index = parseInt(answer, 10);

    if (!isNaN(index) && previousUploads[index]) {
        upload.resumeFromPreviousUpload(previousUploads[index]);
    }
}
