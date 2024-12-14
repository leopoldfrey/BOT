const { Server } = require('node-osc');
const { exec } = require("child_process");

console.log("[Led] Starting...")

var IP = "192.168.1.44";
var OSC_PORT = 14005;
var oscServer = new Server(OSC_PORT, '0.0.0.0', () => {
  console.log('[Led] OSC Server is listening on port ', OSC_PORT);
});

oscServer.on('message', function (msg) {
  if(msg[0] == '/on') {
    if(msg[1] == 1) {
      ledOn();
    } else {
      ledOff();
    }
  } else if(msg[0] == '/brightness') {
    bright(msg[1]);
  }
});


function ledOn() {
  exec("node cli.js --bytes -A 12 on "+IP, (err, stdout, stderr) => {
    if(err) {
      console.error(`exec error: ${err}`);
      return;
    }
    console.log("[Led] On");
  });
}

function ledOff() {
  exec("node cli.js --bytes -A 12 off "+IP, (err, stdout, stderr) => {
    if(err) {
      console.error(`exec error: ${err}`);
      return;
    }
    console.log("[Led] Off");
  });
}

function bright(v) {
  exec("node cli.js --bytes -A 12 color "+IP+" "+v+" 0 0", (err, stdout, stderr) => {
    if(err) {
      console.error(`exec error: ${err}`);
      return;
    }
    console.log("[Led] Brightness", v);
  });
}
