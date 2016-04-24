var cells = []
var creatures = {}
var tiles = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
var STEPS = [[8,6], [9,6], [9,7], [8,8], [7,7], [7,6]]
var COLS = [5,8,11,12,13,14,15,14,15,14,15,14,13,12,11,8,5]
var MOVE_KEYS = ['p','o','e','i','u','é']
var hovered = null
var ws = null

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

function hover_update(cr){
    var rect = cells[cr.x][cr.y][0].getBoundingClientRect()
    $("#hover_popup").css("left",rect.right).css("top",rect.top)
    $("#hover_popup .popup-bar.red").width(cr.health+"%").text(cr.health)
    $("#hover_popup .popup-bar.blue").width(cr.mana+"%").text(cr.mana)
    if (cr.health <= 0 || tiles[cr.x][cr.y] == "_"){
        $("#hover_popup").fadeOut(300);hovered=null;
    }
}

function hover_popin (event){
    var cr = event.data.cr
    hovered = cr.id
    $("#hover_popup").stop(true, true).fadeIn(300)
    hover_update(cr)
}

function on_recv(event) {
    var jdata = JSON.parse (event.data);
    
    for (i in jdata.board){
        for (j=0;j<jdata.board[i].length;j++){
            var chr = jdata.board[i][j];
            if (chr == '_')
                cells[i][j].css('background','black').text(' ');
            else
                cells[i][j].css('background','#444444').text(chr);
            tiles[i][j] = chr;
        }
    }
    if (hovered)
        hover_update(creatures[hovered])
    for (i in jdata.creatures){
        cr = jdata.creatures[i];
        if (!creatures[i])
            creatures[i] = cr;
        if (cr.x || cr.y || cr.health <= 0){
            old_x = creatures[i].x;
            old_y = creatures[i].y;
            cells[old_x][old_y].text(tiles[old_x][old_y]).removeClass("ennemy").unbind("mouseover mouseout");
            if (i == hovered){
                $("#hover_popup").fadeOut(300);hovered=null;
            }
        }
        for (j in cr)
            creatures[i][j] = cr[j];
        x = creatures[i].x;
        y = creatures[i].y;
        if (creatures[i].health > 0){
            cells[x][y].text(creatures[i].chr)
            if (i == 0)
                continue
            cells[x][y].addClass("ennemy")
            cells[x][y].on("mouseover", {cr:creatures[i]}, hover_popin);
            cells[x][y].on("mouseout", function(){$("#hover_popup").fadeOut(300);hovered=null;})
            cells[x][y].click({cr:creatures[i]}, function(event){
                var o = { attack: {x: event.data.cr.x, y: event.data.cr.y}};
                ws.send(JSON.stringify(o));
            });
        }
            //cells[x][y].html("<img src='icon.jpg' style='border-radius:16px'></img>");
    }

    pc = creatures[0]
    $("div.p-bar.red").width(pc.health+"%").text(pc.health)
    $("div.p-bar.blue").width(pc.mana+"%").text(pc.mana)
    $("div.p-bar.green").width((pc.ap*100/12.0)+"%").text(pc.ap)
    for (i in STEPS)
        cells[STEPS[i][0]][STEPS[i][1]].removeClass("ally");
    for (i in pc.short_steps){
        var step = STEPS[pc.short_steps[i]];
        if (tiles[step[0]][step[1]] == '#')
            continue
        var addclass = true
        for (j in creatures)
            if (creatures[j].x == step[0] && creatures[j].y == step[1]){
                addclass = false
                break
            }
        if (addclass)
            cells[step[0]][step[1]].addClass("ally");
    }
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
    if ("WebSocket" in window){
        //ws = new WebSocket("ws://192.168.0.24:8888/socket");
        //ws = new WebSocket("ws://195.154.45.210:8888/socket");
        ws = new WebSocket("ws://localhost:8888/socket");
    }
    ws.onmessage = on_recv
    $(document).keydown (function (ev) {
        for (i in MOVE_KEYS){
            console.log(ev.key, MOVE_KEYS[5], ev.key==MOVE_KEYS[5])
            if (MOVE_KEYS[i] == ev.key){
                var o = {step: i}
                ws.send(JSON.stringify(o));
                break;
            }
        }
    });
});
