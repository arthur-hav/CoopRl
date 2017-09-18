var cells = []

var mapentities = {}
var centerx, centery;
var losmap = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]

//PC is standing on (8, 7)
var STEPS = [[8,6], [9,6], [9,7], [8,8], [7,7], [7,6]]
var DIAGONAL_STEPS = [[9,5], [10,7], [9,8], [7,8], [6,7], [7,5]]

var COLS = [5,8,11,12,13,14,15,14,15,14,15,14,13,12,11,8,5]
var MOVE_KEYS = ['p','o','e','i','u',decodeURIComponent(escape('é'))]
var hovered = null
var ws = null
var pc = null

function gen_column (header, size, offset){
    var buf = "<table style='left:"+offset*30+"px'>"
    if(header)
        buf += "<tr><th></th></tr>"
    for (var i=0;i<7-(size-1+header)/2;i++)
        buf += "<tr><td></td></tr>";
    for (var i=0;i<size;i++)
        buf += "<tr><td><div class='cell'></div></td></tr>";
    buf += "</table>";
    return buf;
}

function popup_remap_keys () {
    $("#remap_popup").toggle();
    refresh_keymap();
}
function refresh_keymap () {
    $("#top-center").text(MOVE_KEYS[0]);
    $("#top-right").text(MOVE_KEYS[1]);
    $("#bottom-right").text(MOVE_KEYS[2]);
    $("#bottom-center").text(MOVE_KEYS[3]);
    $("#bottom-left").text(MOVE_KEYS[4]);
    $("#top-left").text(MOVE_KEYS[5]);
}

function capture_key (index) {
    $(document).unbind("keydown")
        .keydown ({index:index}, function (ev) {
            MOVE_KEYS[ev.data.index] = ev.key 
            refresh_keymap();
            $(document).unbind("keydown")
            $(document).keydown (game_keydown);
        });
}

function hover_update(){
    var cr = mapentities[hovered];
    if (!cr || cr.health <= 0 || !losmap[cr.x][cr.y]){
        $("#hover_popup").fadeOut(300);
        hovered=null;
    }
    else {
        var rect = cells[cr.x][cr.y][0].getBoundingClientRect()
        $("#hover_popup").css("left",rect.right).css("top",rect.top)
        $("#hover_popup .popup-bar.red").width(cr.health*100/cr.max_health+"%").text(Math.round(cr.health))
    }
}

function hover_popin (event){
    hovered = null
    for (var cr_id in mapentities){
        if (mapentities[cr_id].x == event.data.x && mapentitites[i].y == event.data.y) {
           hovered = cr_id
           $("#hover_popup").stop(true, true).fadeIn(300)
           hover_update()
        }
    }
}

function send_start (){
    ws.send(JSON.stringify({start:"now"}))
}

function on_recv(event) {
    //console.log(event.data)
    var jdata = JSON.parse (event.data);
    if (jdata.game == "over")
        window.location = "gameover.html"; 
    if (jdata.game == "queuing"){
        $(".game-container").hide();
        $("#preloader").show();
        $("#preloader .playnum").text(jdata.players + " / 5");
        if (jdata.players == 1){
            $("#startbtn").css("display","inline-block");
        }
    }
    else {
        $(".game-container").show();
        $("#preloader").hide();
        $("#startbtn").hide();
    }
    console.log(jdata);
    for (var i in jdata.lit){
        var c = jdata.lit[i];
        cells[c[0]][c[1]].parent().removeClass("darkness")
        cells[c[0]][c[1]].addClass("floor")
    }
    for (i in jdata.unlit){
        var c = jdata.unlit[i]
        cells[c[0]][c[1]].parent().addClass("darkness")
    }
    //cells[i][j].removeClass("ennemy darkness floor wall");
    
    /*
    for (wall in jdata.map){
        var ctx = $("#minimap")[0].getContext("2d");
        ctx.fillStyle = "#888888";
        ctx.fillRect (62+4*jdata.map[wall][0], 62+4*jdata.map[wall][1],4,4);
    }
    */
    if (jdata.center) {
        var ctx = $("#minimap")[0].getContext("2d");
        ctx.fillStyle = "#222222";
        ctx.fillRect (62+4*centerx, 62+4*centery,4,4);
        if (jdata.center.x != null)
            centerx = jdata.center.x
        if (jdata.center.y != null)
            centery = jdata.center.y
        ctx.fillStyle = "#ffffff";
        ctx.fillRect (62+4*centerx, 62+4*centery,4,4);
    }
    if (jdata.lives) 
        $("#lives-text").text("Lives: "+jdata.lives);
    hover_update()
    for (i in jdata.mapentities){
        var ent = jdata.mapentities[i];
        if (!mapentities[i] || ent.reset)
            mapentities[i] = ent;
        else
            for (j in ent)
                mapentities[i][j] = ent[j];
    }
    $(".foreground").remove()
    for (i in mapentities){
        var x = mapentities[i].x;
        var y = mapentities[i].y;
        if (x == 8 && y == 7)
            pc = mapentities[i]
        else if ('ap' in mapentities[i]) {
            cells[x][y].addClass("ennemy")
        }
        if (mapentities[i].image ){
            cells[x][y].removeClass('floor')
            cells[x][y].append("<img class='foreground' src='"+mapentities[i].image+"'></img>")
            //cells[x][y].css('background-image', 'url(' + mapentities[i].image + ')')
            //cells[x][y].on("mouseover", {x:x, y:y}, hover_popin);
            //cells[x][y].on("mouseout", function(){$("#hover_popup").fadeOut(300);hovered=null;})
        }
    }
    if (pc){
        $("#health_bar").width(pc.health*100/pc.max_health+"%").text(Math.round(pc.health))
        if (pc.ap >= 4){
            for (i in STEPS)
                cells[STEPS[i][0]][STEPS[i][1]].addClass('step');
        }
        if (pc.ap >= 7){
            for (i in DIAGONAL_STEPS)
                cells[DIAGONAL_STEPS[i][0]][DIAGONAL_STEPS[i][1]].addClass('d-step');
        }
    }
    //$("div.p-bar.green").width((pc.ap*100/12.0)+"%").text(pc.ap)
}

function gen_table() {
    var buf = ""
    for (i in COLS){
        buf += gen_column(i%2,COLS[i],i);
        cells.push([]);
    }
    $("#rogue_board").html(buf);
    for (i in COLS)
        for (j = 0; j < COLS[i]; j++)
            cells[i].push($('table:eq('+i+') div.cell:eq('+j+')'));

}

$(document).ready (function (){
    gen_table();
    for (i in cells){
        for (j in cells[i]){
            cells[i][j].click({x:i, y:j}, 
                function(event){
                    var o = {x: event.data.x, y:event.data.y}
                    if (cells[o.x][o.y].hasClass('ennemy')) {
                        o.action = 'attack';
                    }
                    else if (cells[o.x][o.y].hasClass('step')) {
                        o.action = 'step';
                    }
                    /*
                    else if (cells[o.x][o.y].hasClass('d-step')){
                        o.action = 'diagonal_step'
                    }
                    */
                    ws.send(JSON.stringify(o));
            });
        }
    }
    if ("WebSocket" in window){
        //ws = new WebSocket("ws://192.168.0.24:8888/socket");
        //ws = new WebSocket("ws://195.154.45.210:8888/socket");
        ws = new WebSocket("ws://localhost:8888/socket");
    }
    ws.onmessage = on_recv
    //$(document).keydown (game_keydown);
});
