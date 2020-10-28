let socket;

const now = new Date()
var last_ts = Math.round(now.getTime())
var n = 0
var avg = 0
var avg_lat = 0

function ws_onopen (e) {
    socket.send('{"cmd": "connected", "data": "watching"}');
};

var statsFields = []

function reset_con() {
    let port = document.getElementById('inpPort');
    console.log(port);
    port = port.value;
    if (socket) socket.close();
    socket = new WebSocket("ws://192.168.1.2:"+port);

    socket.onopen = ws_onopen;
    socket.onmessage = ws_onmessage;
    socket.onclose = ws_onclose;
    socket.onerror = ws_onerror;
}
//reset_con();

const treshold = 100
function ws_onmessage (event) {
    let now = new Date()
    let cur_ts = Math.round(now.getTime())
    let d = cur_ts - last_ts;

    let packet = {ts: 0, data: ""}
    
    try {
        packet = JSON.parse(event.data)
    } catch (err) {
        console.log('Failed to parse Packet')
    }
    
    document.getElementById("ItemPreview").src = "data:image/jpeg;base64," + packet.data;


    let lat = cur_ts - packet.ts;
    //console.log(`MSG #${packet.stats[0].tick}! ServerTS: ${packet.ts} (lat: ${lat} lat_avg: ${avg_lat}) Прошло с предыдущего ${d} (avg: ${avg})`);
    //<p>MSG #<span id="tick"></span> ! ServerTS: <span id="servts"></span> (lat: <span id="lat"></span> lat_avg: <span id="alat"></span>) Прошло с предыдущего <span id="d"></span> (avg: <span id="ad"></span>)</p>
    
    let elm = document.getElementById('statsGen')
    elm.getElementsByClassName('tick')[0].innerHTML = packet.stats[0].tick;
    elm.getElementsByClassName('servts')[0].innerHTML = packet.ts;
    elm.getElementsByClassName('lat')[0].innerHTML = lat;
    elm.getElementsByClassName('alat')[0].innerHTML = avg_lat;
    elm.getElementsByClassName('d')[0].innerHTML = d;
    elm.getElementsByClassName('ad')[0].innerHTML = avg;

    if (packet.stats[0].tick % treshold == 0) {
        elm = document.getElementById('saveGen')
        elm.getElementsByClassName('tick')[0].innerHTML = packet.stats[0].tick;
        elm.getElementsByClassName('servts')[0].innerHTML = packet.ts;
        elm.getElementsByClassName('lat')[0].innerHTML = lat;
        elm.getElementsByClassName('alat')[0].innerHTML = avg_lat;
        elm.getElementsByClassName('d')[0].innerHTML = d;
        elm.getElementsByClassName('ad')[0].innerHTML = avg;
    }
    
    //console.log(packet.stats)

    
    for (let index = 0; index < packet.stats.length; index++) {
        const stat = packet.stats[index];
        idx = statsFields.indexOf(stat.label)
        if (idx<0) {
            let row = document.getElementsByTagName("tr")[0];
            let x = row.insertCell(-1);
            x.innerHTML=stat.label;
            x.id = "sl"+stat.idx;

            row = document.getElementsByTagName("tr")[1];
            x = row.insertCell(-1);
            x.id = "sv"+stat.idx;
            
            row = document.getElementsByTagName("tr")[2];
            x = row.insertCell(-1);
            x.id = "ss"+stat.idx;
        }

        cell = document.getElementById('sv'+stat.idx)
        cell.innerHTML = stat.stats

        if (stat.tick % treshold == 0) {
            cell = document.getElementById('ss'+stat.idx)
            cell.innerHTML = stat.stats
        }

        statsFields.push(stat.label)
    }
    

    avg = (avg * n + d) / (n + 1)
    avg_lat = (avg_lat * n + d) / (n + 1)
    n = n + 1;

    last_ts = cur_ts
};

function ws_onclose (event) {
    if (event.wasClean) {
        console.log(`[close] Соединение закрыто чисто, код=${event.code} причина=${event.reason}`);
    } else {
        // например, сервер убил процесс или сеть недоступна
        // обычно в этом случае event.code 1006
        console.log('[close] Соединение прервано');
    }
};

function ws_onerror (error) {
    alert(`[error] ${error.message}`);
};