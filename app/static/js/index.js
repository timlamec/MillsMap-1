// toggle the left-side navbar
$(document).ready(function () {
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').toggleClass('hide');
        $('#mapbar').toggleClass('col-8');
        $('#left-arrow').toggleClass('hide');
        $('#right-arrow').toggleClass('hide');
    });
});

$(document).ready(function () {
    $('#sidebarOpen').on('click', function () {
        $('#sidebar').toggleClass('hide');
        $('#mapbar').toggleClass('col-8');
        $('#left-arrow').toggleClass('hide');
        $('#right-arrow').toggleClass('hide');
    });
});

// center of the map
var center = [-6.23, 34.9];
// Create the map
var map = new L.map('mapid', {
    fullscreenControl: true
    }).setView(center, 6);
// Set up the OSM layer
L.tileLayer(
  'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'Data © <a href="http://osm.org/copyright">OpenStreetMap</a>',
    maxZoom: 18,
  }).addTo(map);
// L.tileLayer.bing(bing_key).addTo(map)
//var bing = new L.BingLayer(bing_key);

var osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; <a href="https://openstreetmap.org/copyright" target="_blank">OpenStreetMap contributors' +
        '</a> ',
    tileSize: 256,
});
var googleSat = L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
    maxZoom: 20,
    subdomains:['mt0','mt1','mt2','mt3']
});
var googleTer = L.tileLayer('http://{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}', {
    maxZoom: 20,
    subdomains:['mt0','mt1','mt2','mt3']
});
var hotLayer = L.tileLayer('http://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
    maxZoom: 20,
})
var mqi = L.tileLayer("http://{s}.mqcdn.com/tiles/1.0.0/sat/{LOD}/{X}/{Y}.png", {
    subdomains: ['otile1','otile2','otile3','otile4']
});
var baseMaps = {
    "OpenStreetMap": osmLayer,
    "HOTOSM": hotLayer
} //here more layers: https://www.tutorialspoint.com/leafletjs/leafletjs_getting_started.htm

L.control.layers(baseMaps).addTo(map);
osmLayer.addTo(map);

// add a scale at at your map.
var scale = L.control.scale().addTo(map);

var markers = new L.MarkerClusterGroup();
markers.addTo(map);

// Launch fetch of mills and machines
// Note that this happens concurrently, but we'll only use the
// machines after the mills download is complete
var subs
var machines
mills_promise = $.get('/get_merged_dictionaries')
machines_promise = $.get('/machines')

<!--$.ajax({-->
<!--    type: "POST",-->
<!--    url: '/file_names',-->
<!--    contentType: 'application/json;charset:UTF-8',-->
<!--    success: function (form_names) {-->
<!--        console.log(form_names);-->
<!--        $('#download-info').toggleClass('hide');-->
<!--        var download_info = document.getElementById('download-info')-->
<!--        download_info.innerHTML = form_names-->
<!--        }-->
<!--    });-->

<!--var chart = new dc.BarChart("#peopleBar");-->
<!--d3.csv("{{url_for('static', filename='people.csv')}}").then(function(people) {-->
<!--    var mycrossfilter = crossfilter(people);-->
<!--    var ageDimension = mycrossfilter.dimension(function(data) {-->
<!--       return ~~((Date.now() - new Date(data.DOB)) / (31557600000))-->
<!--    });-->
<!--    var ageGroup = ageDimension.group().reduceCount();-->
<!--    chart-->
<!--       .width(800)-->
<!--       .height(300)-->
<!--       .brushOn(false)-->
<!--       .yAxisLabel("Count")-->
<!--       .xAxisLabel("Age")-->
<!--       .x(d3.scaleLinear().domain([15,70]))-->
<!--       .dimension(ageDimension)-->
<!--       .group(ageGroup)-->
<!--       .yAxisLabel("This is the Y Axis!")-->
<!--       .on('renderlet', function(chart) {-->
<!--          chart.selectAll('rect').on('click', function(d) {-->
<!--             console.log('click!', d);-->
<!--          });-->
<!--       });-->
<!--    chart.render();-->
<!-- });-->

<!--var pieChart = new dc.PieChart("#peoplePie");-->
<!--d3.csv("{{url_for('static', filename='people.csv')}}").then(function(people) {-->
<!--    var mycrossfilter = crossfilter(people);-->
<!--    var ageDimension = mycrossfilter.dimension(function(data) {-->
<!--       return ~~((Date.now() - new Date(data.DOB)) / (31557600000))-->
<!--    });-->
<!--    var ageGroup = ageDimension.group().reduceCount();-->
<!--    pieChart-->
<!--    .width(768)-->
<!--    .height(480)-->
<!--    .slicesCap(4)-->
<!--    .innerRadius(100)-->
<!--    .dimension(ageDimension)-->
<!--    .group(ageGroup)-->
<!--    .legend(dc.legend().highlightSelected(true))-->
<!--    // workaround for #703: not enough data is accessible through .label() to display percentages-->
<!--    .on('pretransition', function(chart) {-->
<!--        chart.selectAll('text.pie-slice').text(function(d) {-->
<!--            return d.data.key + ' ' + dc.utils.printSingleValue((d.endAngle - d.startAngle) / (2*Math.PI) * 100) + '%';-->
<!--        })-->
<!--    });-->
<!--    pieChart.render();-->
<!-- });-->

// Now the promise chain that uses the mills and machines
mills_promise.then(function(subs_json) {
    // Get the filenames for mills folder
    var element = document.getElementById("spin");
    element.classList.toggle("hide");
    subs = JSON.parse(subs_json)
    subs = crossfilter(subs)
//    console.log(subs.all())
    machine_index = 0
    let dimensionPackaging = subs.dimension(item => item.phonenumber)
    dimensionPackaging.filterExact("");
    filtered = (dimensionPackaging.top(Infinity))

<!--    fortifiedFlourChart chart   -->
    var fortifiedFlourChart = new dc.PieChart('#fortifiedFlour');
    var fortifiedDimension = subs.dimension(function(data) {
       return data.Packaging_flour_fortified;
    });
    var fortifiedGroup = fortifiedDimension.group().reduceCount();
    fortifiedFlourChart
        .slicesCap(4)
        .innerRadius(50)
       .dimension(fortifiedDimension)
       .group(fortifiedGroup)
      .legend(dc.legend().highlightSelected(true))
        .on('pretransition', function(fortifiedFlourChart) {
            fortifiedFlourChart.selectAll('text.pie-slice').text(function(d) {
                return d.data.key + ' ' + dc.utils.printSingleValue((d.endAngle - d.startAngle) / (2*Math.PI) * 100) + '%';
            })
        });
        fortifiedFlourChart.render();

<!--    functionalMillsChart chart   -->
    // Now comes the work with the nested data:
<!--    var machines = subs.all().data(function(d) {-->
<!--      return d.modules-->
<!--    })-->
<!--    var functionalMillsChart = new dc.PieChart('#functionalMills');-->
<!--    var functionalMillsDimension = machines.dimension(function(data) {-->
<!--       return data.operational_mill;-->
<!--    });-->
<!--    var functionalMillsGroup = functionalMillsDimension.group().reduceCount();-->
<!--    functionalMillsChart-->
<!--        .slicesCap(4)-->
<!--        .innerRadius(50)-->
<!--       .dimension(functionalMillsDimension)-->
<!--       .group(functionalMillsGroup)-->
<!--      .legend(dc.legend().highlightSelected(true))-->
<!--        .on('pretransition', function(functionalMillsChart) {-->
<!--            functionalMillsChart.selectAll('text.pie-slice').text(function(d) {-->
<!--                return d.data.key + ' ' + dc.utils.printSingleValue((d.endAngle - d.startAngle) / (2*Math.PI) * 100) + '%';-->
<!--            })-->
<!--        });-->
<!--        functionalMillsChart.render();-->
<!--        console.log(subs.values())-->

for (subindex in subs.all()) {
//    for (subindex in filtered){
        var sub = subs.all()[subindex]
        try {
            var coords = sub['Location_mill_gps_coordinates']
        }
        catch(err) {
            console.log("No GPS coordinates found for this submission", sub)
        }
        color = 'blue'
        var lon = coords[1]
        var lat = coords[0]
        var marker = L.circleMarker([lon, lat],{stroke: false, fillOpacity: 0.8});
        marker.setStyle({fillColor: color});
        markers.addLayer(marker)
        markers.addLayer(marker)
        var toolTip = "<dt>Number of milling machines:" + sub['machines_machine_count'] + "</dt>"
        counter = 0
        for (machine_index in sub['machines']){
            counter += 1
            toolTip += "<dt> Machine: " + counter + "</dt>";
            toolTip += "<div> ID: " + sub['machines'][machine_index]['__id'] + "</div>";
            toolTip += "<div> Type of mill: ";
            toolTip += sub['machines'][machine_index]['mill_type'] + "</div>";
            toolTip += "<div> Operational: ";
            toolTip += sub['machines'][machine_index]['operational_mill'] + "</div>";
            toolTip += "<div> Energy source: ";
            toolTip += sub['machines'][machine_index]['energy_source'] + "</div>";
        }
        marker.bindTooltip(toolTip);
<!--        Filtering-->
<!--        var ndx = crossfilter(subs_json);-->
<!--        var totalDim = ndx.dimension(function(d) { return d.interviewee.ownership; });-->
<!--        var ownership_yes = totalDim.filter('yes');-->
<!--        console.log("ownership_yes");-->
    }
});

let supermarketItems = crossfilter([
  {name: "banana", category:"fruit", country:"Malta", outOfDateQuantity:3, quantity: 12},
  {name: "apple", category:"fruit", country:"Spain", outOfDateQuantity:1, quantity: 9},
  {name: "tomato", category:"vegetable", country:"Spain", outOfDateQuantity:2, quantity: 25}
])
let dimensionCategory = supermarketItems.dimension(item => item.category)
let quantityByCategory = dimensionCategory.group().reduceSum(item => item.quantity)
console.log(quantityByCategory.all())

let dimensionCountry = supermarketItems.dimension(item => item.country)
dimensionCountry.filterExact("Spain");
console.log(dimensionCountry.top(Infinity))







// promise = $.get('/mill_points')
// promise.then(function(submissions_filtered) {
//     var element = document.getElementById("spin");
//     element.classList.toggle("hide");
//
//     var submissions_filtered_json = JSON.parse(submissions_filtered)
//
//     for (submission_index in submissions_filtered_json){
//         var submission = submissions_filtered_json[submission_index]
//         try {
//             var coordinates = submission['coordinates']
//         }
//         catch(err) {
//             console.log("No GPS coordinates found for the submission", submission)
//         }
//         color = 'blue'
//
//         var lng = coordinates[1]
//         var lat = coordinates[0]
//         var marker = L.circleMarker([lng, lat],{stroke: false, fillOpacity: 0.8});
//         marker.setStyle({fillColor: color});
//         markers.addLayer(marker);
//
//         var toolTip =
//             "<dt>Number of milling machines:" + submission['number_milling_machines'] + "</dt>"
//         toolTip += "<hr>"
//         counter = 0
//         for (machine_index in submission['machines']){
//             counter += 1
//             toolTip += "<dt> Machine: " + counter + "</dt>";
//             toolTip += "<div> ID: " + submission['machines'][machine_index]['__id'] + "</div>";
//             toolTip += "<div> Type of mill: ";
//             toolTip += submission['machines'][machine_index]['mill_type'] + "</div>";
//             toolTip += "<div> Operational: ";
//             toolTip += submission['machines'][machine_index]['operational_mill'] + "</div>";
//             toolTip += "<div> Energy source: ";
//             toolTip += submission['machines'][machine_index]['energy_source'] + "</div>";
//
//             //console.log(submission['machines'][machine_index]['energy_source'])
//             //console.log(submission['machines'][machine_index])
//         }
//         marker.bindTooltip(toolTip);
//
//     }
//
//     map.isFullscreen() // Is the map fullscreen?
//     map.toggleFullscreen() // Either go fullscreen, or cancel the existing fullscreen.
//     L.Control.Fullscreen
//     map.fitBounds(markers.getBounds())
// });


// // `fullscreenchange` Event that's fired when entering or exiting fullscreen.
// map.on('fullscreenchange', function () {
//     if (map.isFullscreen()) {
//         console.log('entered fullscreen');
//     } else {
//         console.log('exited fullscreen');
//     }
// });
