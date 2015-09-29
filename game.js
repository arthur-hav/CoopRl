function ajaxSend (url, args) {
    var xmlhttp = new XMLHttpRequest(); 
    xmlhttp.open("POST",url,true);
    xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
    xmlhttp.send(args);
}

if ("WebSocket" in window){
    var source = new WebSocket("ws://localhost:8888/socket");
    //var source = new WebSocket("ws://arthur.modulix.org/socket");
    //var source = new WebSocket("ws://195.154.45.210:8888/socket");
    //    }
    source.onmessage = function(event) {
        terminal.innerHTML = event.data;
    }
    document.onkeydown = function(evt) {
        source.send (evt.keyCode);
        //evt = evt || window.event;
        //if (evt.ctrlKey && evt.keyCode == 90) {
    }
} 
else {
    alert ("WebSocket not supported! You can't play the game until a workararound is implemented. Mail the project owner!")
}

