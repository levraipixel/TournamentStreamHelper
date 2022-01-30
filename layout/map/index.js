// See https://github.com/xtk93x/Leaflet.TileLayer.ColorFilter to colorize your map
let myFilter = [
]

var baseMap = L.tileLayer.colorFilter(
    "http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 6,
        zoomSnap: 0,
        zoomControl: false,
        id: "osm.streets",
        filter: myFilter
    }
);

var map = L.map('map', {
    maxZoom: 6,
    zoomControl: false
}).setView([0, 0], 2);

baseMap.addTo(map);

(($) => { 
    function Start(){
        pingData = getPings().then((pingData)=>{
            console.log(pingData)

            let servers = []
            let positions = []

            Object.values(data.score.team).forEach((team)=>{
                Object.values(team.players).forEach((player)=>{
                    let pos = [
                        player.state.latitude? player.state.latitude : player.country.latitude,
                        player.state.longitude? player.state.longitude : player.country.latitude,
                    ]
                    positions.push(pos)

                    let server = findClosestServer(pingData, pos[0], pos[1])
                    servers.push(server)

                    L.marker(pos, { icon: L.icon({
                        iconUrl: "./marker.svg",
                        iconSize: [12, 12],
                        iconAnchor: [6, 6],
                    }) }).addTo(map)
                        .bindTooltip(player.name, { direction: "top", className: 'leaflet-tooltip-own', offset: [0, -12] })
                        .openTooltip();
                })
            })

            let maxPing = 0;

            servers.forEach((server1)=>{
                servers.forEach((server2)=>{
                    if(server1 != server2){
                        let ping = pingBetweenServers(server1, server2);
                        if(ping > maxPing){
                            maxPing = ping;
                        }
                    }
                })
            })

            console.log("Ping: "+ping);

            let pingString = maxPing < 10 ? "< 10" : maxPing.toFixed(2);
            $("#ping").html("Estimated ping: "+pingString+" ms")

            let maxDistance = 0;

            positions.forEach((pos1)=>{
                positions.forEach((pos2)=>{
                    if(pos1 != pos2){
                        let distance = distanceInKm(pos1, pos2);
                        if(distance > maxDistance){
                            maxDistance = distance;
                        }
                    }
                })
            })

            console.log("Distance: "+maxDistance);

            let distanceString = ""
            
            if(maxDistance < 100){
                distanceString = "< 100 Km / < 62 mi"
            } else {
                distanceString = maxDistance.toFixed(2)+" Km"+" / "+(maxDistance*0.621371).toFixed(2)+" mi"
            }

            if(positions.length == 2){
                $("#distance").html("Distance: "+distanceString)
            } else {
                $("#distance").html("Max distance: "+distanceString)
            }

            gsap.timeline()
                .to(['.overlay-element'], { duration: 1, autoAlpha: 1 }, 0)
            
            map.on("zoomend", ()=>{
                var polyline = L.polyline(getPairs(positions), {color: 'blue', dashArray: '5,10'}).addTo(map);
            })

            map.flyToBounds(L.latLngBounds(positions), {
                paddingTopLeft: [80 + $(".overlay").outerHeight(), 80],
                paddingBottomRight: [80, 80],
                duration: 2,
                easeLinearity: 0.000001
            })
        })
    }

    function findClosestServer(pingData, lat, lng){
        let closest = pingData[0]
        let closestVal = Math.getDistance(lat, lng, parseFloat(pingData[0].latitude), parseFloat(pingData[0].longitude))

        pingData.forEach((server)=>{
            let distance = Math.getDistance(lat, lng, parseFloat(server.latitude), parseFloat(server.longitude));
            if(distance < closestVal){
                closestVal = distance;
                closest = server;
            }
        })

        return closest;
    }

    function pingBetweenServers(server1, server2){
        return server1.pings[server2.id]
    }

    function distanceInKm(origin, destination) {
        var lon1 = toRadian(origin[1]),
            lat1 = toRadian(origin[0]),
            lon2 = toRadian(destination[1]),
            lat2 = toRadian(destination[0]);
    
        var deltaLat = lat2 - lat1;
        var deltaLon = lon2 - lon1;
    
        var a = Math.pow(Math.sin(deltaLat/2), 2) + Math.cos(lat1) * Math.cos(lat2) * Math.pow(Math.sin(deltaLon/2), 2);
        var c = 2 * Math.asin(Math.sqrt(a));
        var EARTH_RADIUS = 6371;
        return c * EARTH_RADIUS;
    }
    function toRadian(degree) {
        return degree*Math.PI/180;
    }

    var data = {}
    var oldData = {}

    async function Update(){
        oldData = data;
        data = await getData();

        if(oldData == {}){
            
        }
    }

    Math.getDistance = function( x1, y1, x2, y2 ) {
        var xs = x2 - x1, ys = y2 - y1;		
        xs *= xs;
        ys *= ys;
        return Math.sqrt( xs + ys );
    };

    function getPairs(arr) {
        var res = [],
            l = arr.length;
        for(var i=0; i<l; ++i)
            for(var j=i+1; j<l; ++j)
                res.push([arr[i], arr[j]]);
        return res;
    }

    function getPings() {
        return $.ajax({
            dataType: 'json',
            url: './pings.json',
            cache: false,
        });
    }

    Update();
    $(window).on("load", () => {
        $('body').fadeTo(500, 1, async () => {
            Start();
            setInterval(Update, 1000);
        });
    });
})(jQuery);