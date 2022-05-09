var canvas       = document.getElementById('shared_canvas');
var ctx          = canvas.getContext('2d');
var width        = canvas.clientWidth;
var height       = canvas.clientHeight;
var imagedata    = ctx.getImageData(0, 0, 640, 480);
var newImageData = ctx.createImageData(640, 480);

// This is the raw shared memory buffer
var pyWebMemSharedBuffer = new Uint8ClampedArray(12 + (width * height * 4));
// Magic Start Long
let magicStart = new Uint8Array(new Int32Array([1234567890]).buffer);
pyWebMemSharedBuffer[0] = magicStart[0];
pyWebMemSharedBuffer[1] = magicStart[1];
pyWebMemSharedBuffer[2] = magicStart[2];
pyWebMemSharedBuffer[3] = magicStart[3];

// Header info
pyWebMemSharedBuffer[4] = 128; // This signifies ownership; 128 means Javascript owns it, 0 means Python owns it
pyWebMemSharedBuffer[5] = 0;   // These are unused
pyWebMemSharedBuffer[6] = 0;   // These are unused
pyWebMemSharedBuffer[7] = 0;   // These are unused

// Magic End Long
let magicEnd   = new Uint8Array(new Int32Array([987654321 ]).buffer);
pyWebMemSharedBuffer[pyWebMemSharedBuffer.length - 4] = magicEnd[0];
pyWebMemSharedBuffer[pyWebMemSharedBuffer.length - 3] = magicEnd[1];
pyWebMemSharedBuffer[pyWebMemSharedBuffer.length - 2] = magicEnd[2];
pyWebMemSharedBuffer[pyWebMemSharedBuffer.length - 1] = magicEnd[3];

// Begin checking for modifications to the shared memory buffer!
function update() {
    // If the fifth element is "128", then Python has released control of of the buffer back to us
    if (pyWebMemSharedBuffer[4] == 128) {
        console.log("Updating Image!");
        newImageData.data.set(pyWebMemSharedBuffer.slice(8, pyWebMemSharedBuffer.length-4));
        ctx.putImageData(newImageData, 0, 0);
        pyWebMemSharedBuffer[4] = 0; // Release control of the buffer back to Python
    }
    window.requestAnimationFrame(update);
}
window.requestAnimationFrame(update);
