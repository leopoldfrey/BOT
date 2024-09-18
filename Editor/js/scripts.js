var ContentsData;
var $data = $("#data");
var $header = $("#header");
var modalContent = $('#modalContent');
var modalAdmin = $('#modalAdmin');
var stateBut = $("#socketState");
var oldQ = "";
var Contents = new Array();
var mod = false;
var cat = "sequence";
var currRow;
var editing = false;

const rgb2hex = (rgb) => `#${rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/).slice(1).map(n => parseInt(n, 10).toString(16).padStart(2, '0')).join('')}`

function sel(o) {
  currRow.removeClass("selected");
  currRow = o;
  currRow.addClass("selected");
  $("html, body").animate({ scrollTop: currRow.position.top });
}

function change(o) {
  if(o.html().includes("span"))
    o.html("");
  else
    o.html("<span class='icon-check'>");
}

function set(o) {
  o.html("<span class='icon-check'>");
}

function clear(o) {
  o.html("");
}

function load()
{
  urlFill = ""
  switch(cat)
  {
    default:
      case "sequence":
        urlFill = "/getSequence";
        history.pushState({}, null, "index.html?cat=sequence");
        break;  
    case "sentences":
      urlFill = "/getSentences";
      history.pushState({}, null, "index.html?cat=sentences");
      break;
  }
  $.ajax({
      url: urlFill,
      type: "GET",
      success: function(response) {
          fillContents(response);
          $("html, body").animate({ scrollTop: 0 });
      },
      error: function(jqXHR, textStatus, errorMessage) {
          console.log(errorMessage); // Optional
      }
  });
}

function fillContents(data) {
  $data.empty();
  $header.empty();
  ContentsData = data;
  len = Object.keys(ContentsData).length;

  switch(cat){
    default:
    case "sequence":
      $("#info").html("Sequence ("+len+")");
      $("#sentences").removeClass("selbut");
      $("#sequence").addClass("selbut");
      $header.append("<th scope='col'>Part</th><th scope='col'>Prompt</th><th scope='col'>First</th><th scope='col'>Max Interactions</th><th scope='col'>Video Sequence</th>"); //<th scope='col'>Max Duration (s)</th>
      break;
    case "sentences":
      $("#info").html("Characters ("+len+")");
      $("#sentences").addClass("selbut");
      $("#sequence").removeClass("selbut");
      $header.append("<th scope='col'>Type</th><th scope='col'>List</th>");
      break;
  }

  Object.keys(ContentsData).forEach((idx) => {

    switch(cat){
      default:
        case "sequence":
          //console.log(ContentsData);
          $data.append(
            "<tr class='ContentRow'><th class='ContentNum' scope='row'>" + idx + "</th>" +
            "<td class='ContentElem contentPrompt'>" + ContentsData[idx]["prompt"] + "</td>"+
            "<td class='ContentElem contentFirst'>" + ContentsData[idx]["first"] + "</td>"+
            "<td class='ContentElem contentInter'>" + ContentsData[idx]["nb_inter"] + "</td>"+
            /*"<td class='ContentElem contentDur'>" + ContentsData[idx]["dur_max"] + "</td>"+*/
            "<td class='ContentElem contentVideo'>" + ContentsData[idx]["video"] + "</td>"+
            "</tr>");
          break;
        case "sentences":
          //console.log(ContentsData);
          str = "";
          ContentsData[idx].forEach((elem) => {
            str += " - "+elem+"</br>";
          });
          $data.append("<tr class='ContentRow'><th class='ContentNum' scope='row'>" + idx + "</th><td class='ContentElem contentValue'>"+str+"</td></tr>");
          break;
          }
    
  });
    

  $('td').dblclick(function() {
    edit();
  });
  
  $('.ContentNum').dblclick(function() {
    edit();
  });

  currRow = $('.ContentRow').first();
  currRow.addClass("selected");
  $('.ContentRow').click(function() {
    sel($(this));
  });
}

function next() {
  c = currRow.next();
  if (c.length > 0) {
    sel(c);
  }
}

function prev() {
  c = currRow.prev();
  if (c.length > 0) {
    sel(c);
  }
}

$(window).keydown(function (e) {
    if(editing)
      return;
    // console.log(e.which);
    shifted = e.shiftKey;
    var c = "";
    if (e.which == 13) { // Enter
      edit();
    } else if (e.which == 38) { // Up Arrow
      prev();
    } else if (e.which == 40 || e.which == 32) { // Down Arrow
      next();
    } else if (e.which == 83 && e.shiftKey) {
      //save();
    } else if (e.which == 65) { // a
      modalAdmin.modal('show');
    }
});

$(window).on('load', function() {
  url = new URL(window.location.href);
  cat = url.searchParams.get('cat');
  if(!cat)
    cat = "sequence";
  load();
});

$("#admin").click(function(){
  $.ajax({
    url: "/getSettings",
    type: "GET",
    success: function(response) {
      //console.log("response", response);
      $("#max_inter").val(response.max_inter);
      $("#max_inter_s").val(response.max_inter_s);
      $("#max_silence").val(response.max_silence);
      $("#max_relance_quit").val(response.max_relance_quit);
      $("#speed").val(response.speed);
      $("#lang").val(response.lang);
      if($("#voiceChoo").children('option').length == 0)
        $("#voiceChoo").append("<option value='"+response.voice+"'>"+response.voice+"</option>");
      $("#voiceChoo").val(response.voice);
      $("#model").val(response.model);
      $("#botname").val(response.botname);
      $("#username").val(response.username);
      $("#end_prompt").val(response.end_prompt);
      modalAdmin.modal('show');
    },
    error: function(jqXHR, textStatus, errorMessage) {
        console.log(errorMessage); // Optional
    }
  });
});

$("#sequence").click(function(){
  // console.log("Edit sequence");
  $(".seqBut").show();
  $(".editBut").show();
  cat = "sequence";
  history.pushState({}, null, "index.html?cat=sequence");
  $.ajax({
      url: "/getSequence",
      type: "GET",
      success: function(response) {
          fillContents(response);
          $("html, body").animate({ scrollTop: 0 });
      },
      error: function(jqXHR, textStatus, errorMessage) {
          console.log(errorMessage); // Optional
      }
  });
});

$("#sentences").click(function(){
  // console.log("Edit sentences");
  $(".seqBut").hide();
  $(".editBut").hide();
  cat = "sentences";
  history.pushState({}, null, "index.html?cat=sentences");
  $.ajax({
      url: "/getSentences",
      type: "GET",
      success: function(response) {
          fillContents(response);
          $("html, body").animate({ scrollTop: 0 });
      },
      error: function(jqXHR, textStatus, errorMessage) {
          console.log(errorMessage); // Optional
      }
  });
});

$("#plus").click(function(){
  //console.log("PLUS !", cat);
  currRow.removeClass("selected");

  idx = $('.ContentRow').length + 1;
  switch(cat){
    default:
      case "sequence":
        $data.append(
          "<tr class='ContentRow'><th class='ContentNum' scope='row'>" + idx + "</th>" +
          "<td class='ContentElem contentPrompt'></td>"+
          "<td class='ContentElem contentFirst'></td>"+
          "<td class='ContentElem contentInter'></td>"+
        /* "<td class='ContentElem contentDur'></td>"+*/
          "<td class='ContentElem contentVideo'></td>"+
          "</tr>");
        break;
  }
  currRow = $('.ContentRow').last();
  currRow.addClass("selected");
  currRow.get(0).scrollIntoView();
  currRow.click(function() {
    sel($(this));
  });

  $('td').dblclick(function() {
    console.log("CLICK HERE");
    edit();
  });

  $('tr').dblclick(function() {
    console.log("CLICK HERE");
    edit();
  });

  setTimeout(function(){
    edit();
  }, 300);
});

$("#del").click(function(){
  idx = currRow.children(".ContentNum").html();
  if(idx == 0) {
    alert("You can not delete prompt 0 !");
  } else {
    cc = ""
    switch(cat){
      case "sequence":
        cc = "part ";
        break;
    }
    if(confirm("Delete "+cc+idx+" ?") == true)
    {
      $.ajax({
          url: "/delSequence",
          type: "POST",
          data: JSON.stringify({
            "idx": escape(idx)
          }),
          success: function(response) {
              console.log(response['msg']);
              load();
          },
          error: function(jqXHR, textStatus, errorMessage) {
              console.log(errorMessage); // Optional
          }
      });
    }
  }
});

// MODAL Content INPUT
function selectElement(id, valueToSelect)
{    
  let element = document.getElementById(id);
  element.value = valueToSelect;
}

function edit()
{
  editing = true;
  $("#mb-Sentences").hide();
  $("#mb-Sequence").hide();
      
  switch(cat) {
    case "sequence" :
      $("#modalTitle").html("Edit Part");
      $("#num").val(currRow.children(".ContentNum").html());
      $("#prompt").val(currRow.children(".contentPrompt").html());
      $("#first").val(currRow.children(".contentFirst").html());
      $("#nb_inter").val(currRow.children(".contentInter").html());
      /*$("#dur_max").val(currRow.children(".contentDur").html());*/
      selectElement("video", currRow.children(".contentVideo").html());
      $("#mb-Sequence").show();
      setTimeout(function(){$("#prompt").focus();}, 500);
      break;
    case "sentences" : 
      $("#modalTitle").html("Edit "+currRow.children(".ContentNum").html());
      str = currRow.children(".contentValue").html().replaceAll('<br>','\n');
      console.log(str);
      $("#sentenceContent").val(str);
      $("#mb-Sentences").show();
      break;
  }  
  modalContent.modal('show');
}

function validContent(ev) {
  ev.preventDefault();
  switch(cat) {
    case "sentences":
      currRow.children(".contentValue").html($("#sentenceContent").val().replaceAll("\n","<br>"));
      break;
    case "sequence":
      currRow.children(".ContentNum").html($("#num").val());
      currRow.children(".contentPrompt").html($("#prompt").val());
      currRow.children(".contentFirst").html($("#first").val());
      currRow.children(".contentInter").html($("#nb_inter").val());
      /*currRow.children(".contentDur").html($("#dur_max").val());*/
      currRow.children(".contentVideo").html($("#video").val());
      break;
  }
  modalContent.modal('hide');
  save();
}

function save() {
  idx = currRow.children(".ContentNum").html();
  switch(cat) 
  {
    case "sequence":
      $.ajax({
        url: "/modSequence",
        type: "POST",
        data: JSON.stringify({
          "idx": idx,
          "prompt": escape(currRow.children(".contentPrompt").html()),
          "first": escape(currRow.children(".contentFirst").html()),
          "nb_inter": escape(currRow.children(".contentInter").html()),
          /*"dur_max": escape(currRow.children(".contentDur").html()),*/
          "video": escape(currRow.children(".contentVideo").html()),
        }),
        success: function(response) {
            console.log(response['msg']);
        },
        error: function(jqXHR, textStatus, errorMessage) {
            console.log(errorMessage); // Optional
        }
      });
      break;
    case "sentences":
      var filtered = currRow.children(".contentValue").html().replaceAll(" - ","").replaceAll("- ","").split("<br>").filter(function (el) {
        return el != "";
      });
      $.ajax({
        url: "/modSentence",
        type: "POST",
        data: JSON.stringify({
          "idx": idx,
          "sentence": escape(filtered)
        }),
        success: function(response) {
            console.log(response['msg']);
        },
        error: function(jqXHR, textStatus, errorMessage) {
            console.log(errorMessage); // Optional
        }
      });
      break;
  }

}

function cancel(ev) {
  //
}

modalContent.on("hide.bs.modal", function(){
  // console.log("HIDE", $('.ContentRow').last().is(currRow), "("+newContent.val()+")");
  /*if($('.ContentRow').last().is(currRow) && newContent.val() == "")
  {
    idx = currRow.children(".ContentNum").html();
    currRow.remove()
    console.log("REMOVE LAST", idx);
  }*/
  editing = false;
});

$("#Close").click(function(ev)
{
  // console.log("CLOSE");
  cancel(ev);
});

$('#Cancel').click(function(ev)
{
  // console.log("CANCEL");
  cancel(ev);
});
/*
$("#up").click(function(ev){
  idx = currRow.children(".ContentNum").html();
  var row = currRow.closest('tr');
  var prev = row.prev();
  var prevVc = prev.children();//".contentValue");
  var prevV = prevVc.html();
  var rowVc = row.children();//".contentValue");
  var rowV = rowVc.html();
  console.log("PREV", prevVc, "ROW", rowVc);
  prevVc.html(rowV);
  rowVc.html(prevV);
  save();
  sel(prev);
  save();
  //console.log("Up", idx, prevV, rowV);
});

$("#down").click(function(ev){
  idx = currRow.children(".ContentNum").html();
  var row = currRow.closest('tr');
  var next = row.next();
  var nextVc = next.children(".contentValue");
  var nextV = nextVc.html();
  var rowVc = row.children(".contentValue");
  var rowV = rowVc.html();
  nextVc.html(rowV);
  rowVc.html(nextV);
  save();
  sel(next);
  save();
  //console.log("Down", idx, rowV, nextV);
});*/

$("#sort").click(function(ev){
  $.ajax({
    url: "/clear",
    type: "POST",
    data: "",
    success: function(response) {
        console.log(response['msg']);
    },
    error: function(jqXHR, textStatus, errorMessage) {
        console.log(errorMessage); // Optional
    }
  });
  count = 0;
  $("#data").children('tr').each(function() {
    $(this).children(".ContentNum").html(count);
    sel($(this));
    save();
    count++;
  });
});

modalContent.submit(function(ev)
{
  // console.log("SUBMIT");
  validContent(ev);
});

$('#Ok').click(function(ev)
{
  // console.log("OK");
  validContent(ev);
});

$("#reload").click(function(ev)
{
  load();
  reloadBrain();
});

function reloadBrain(){
  socket.send(JSON.stringify({'command':'reload'}));
}

function saveConfig() {
  conf = JSON.stringify({
    'command':            'saveConfig',
    'max_inter':          $("#max_inter").val(),
    'max_inter_s':        $("#max_inter_s").val(),
    'speed':              $("#speed").val(),
    'max_silence':        $("#max_silence").val(),
    'max_relance_quit':   $("#max_relance_quit").val(),
    'pitch':              0,
    'voice':              $("#voiceChoo").val(),
    'lang':               $("#lang").val(),
    'model':              $("#model").val(),
    'botname':            $("#botname").val(),
    'username':           $("#username").val(),
    'end_prompt':         $("#end_prompt").val()
  })
  console.log("CONFIG", conf);
  modalAdmin.modal('hide');
  socket.send(conf);
}

$("#load").click(function(){
  var input = document.createElement('input');
  input.type = 'file';
  input.onchange = e => { 
    var reader = new FileReader();
    reader.readAsText(e.target.files[0],'UTF-8');
    reader.onload = readerEvent => {
       $.ajax({
        url: "/openFile",
        type: "POST",
        data: readerEvent.target.result,
        success: function(response) {
            console.log(response['msg']);
            reloadBrain();
            setTimeout(function(){
              location.reload();
            },500);
            
        },
        error: function(jqXHR, textStatus, errorMessage) {
            console.log(errorMessage); // Optional
        }
      });
    }
  }
  input.click();
});

$("#saveas").click(function(){
  $.ajax({
    url: "/saveFile",
    type: "POST",
    data: prompt("Name this file :", "MySuperBotConfiguration"),
    success: function(response) {
      console.log(response['msg']);
    },
    error: function(jqXHR, textStatus, errorMessage) {
        console.log(errorMessage); // Optional
    }
  });
});

// WEBSOCKET

var socket;

function connectToWS()
{
  socket = new WebSocket("ws://localhost:9001");

  socket.onopen = function(e) {
    stateBut.html("Open :)");
    stateBut.css("background", "lightgreen");
    console.log("[open] Connection established");
    socket.send(JSON.stringify({'command':'connect'}));
    socket.send(JSON.stringify({'command':'getConfig'}));
    /*setTimeout(function(){
      socket.send(JSON.stringify({'command':'getConfig'}));
    }, 200);*/
    
  };

  socket.onmessage = function(event) {
    // console.log(`[message] Data received from server: ${event.data}`);
    data = JSON.parse(event.data);
    if(data.command == "on") {
      console.log("PHONE ON", data.value);
      $("#phone").prop("checked", data.value);
    } else if(data.command == "message") {
      console.log("[ws]", data);
    } else if(data.command == "voice") {
      console.log("VOICE SET", typeof(data.value), data.value);
      $("#voiceChoo>option[val="+data.value+"]").prop("selected", true);//(data.value);
    } else if(data.command == "params") {
      $("#max_inter").val(data.max_inter);
      $("#max_inter_s").val(data.max_inter_s);
      $("#max_silence").val(data.max_silence);
      $("#max_relance_quit").val(data.max_relance_quit);
      $("#speed").val(data.speed);
      $("#lang").val(data.lang);
      console.log("VOICE HERE", data.voice);
      $("#voiceChoo").val(data.voice);
      $("#model").val(data.model);
      $("#botname").val(data.botname);
      $("#username").val(data.username);
      $("#end_prompt").val(data.end_prompt);
    } else if(data.command == "timers") {
    } else if(data.command == "silent") {
    } else if(data.command == "step") {
    } else if(data.command == "voices") {
      console.log("VOICE LIST");
      
      $('#voiceChoo').empty();
      (data.value).forEach((elem)=>{
        $('#voiceChoo').append("<option value='"+elem+"'>"+elem+"</option>");
      });
    } else {
      console.log("[ws]", data);
    }
  };

  socket.onclose = function(event) {
    stateBut.html("Closed :(");
    stateBut.css("background", "#ff9797");
    // console.log('[close] Connection closed');
    setTimeout(function(){
        checkSocket(socket.readyState);
    }, 3000);
  };

  socket.onerror = function(error) {
    stateBut.html("Error :(");
    stateBut.css("background", "#ff9797");
    // console.log(`[error] ${error.message}`);
    setTimeout(function(){
        checkSocket(socket.readyState);
    }, 3000);
  };
}

function checkSocket(state) {
    switch(state) {
        case socket.CONNECTING:
            stateBut.html("Connecting...");
            stateBut.css("background", "orange");
            console.log("- WebSocket Connecting...");
            break;
        case socket.OPEN:
            stateBut.html("Open :)");
            stateBut.css("background", "lightgreen");
            console.log("- WebSocket Open :)");
            break;
        case socket.CLOSING:
            stateBut.html("Closing...");
            stateBut.css("background", "orange");
            console.log("- WebSocket Closing...");
            break;
        case socket.CLOSED:
            stateBut.html("Closed :(");
            stateBut.css("background", "#ff9797");
            console.log("* WebSocket Closed :(");
            connectToWS();
            break;
    }
}

connectToWS();