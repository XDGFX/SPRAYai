`
generate_charts.js

Generates example charts for the UI, using charts.js.

Callum Morrison, 2021
`

var ctx1 = document.getElementById('chart_performance_1');
var ctx2 = document.getElementById('chart_performance_2');
var d = new Date()
var today = d.getDay();

var days = new Array()

// For some reason day 0 is Sunday...
weekday = [
    "SUN",
    "MON",
    "TUE",
    "WED",
    "THU",
    "FRI",
    "SAT"
]

// Count back five days from today
for (var i = 0; i < 6; i++) {
    days[i] = weekday[(today + i - 5 + 7) % 7]
}

// Setup chart style
Chart.defaults.global.defaultFontFamily = 'Kanit';
Chart.defaults.global.defaultFontWeight = 'lighter';
Chart.defaults.global.defaultFontColor = '#fff';
Chart.defaults.borderColor = '#fff';

default_chart_options = {
    legend: {
        display: false
    },
    scales: {
        yAxes: [{
            ticks: {
                beginAtZero: true,
                maxTicksLimit: 3
            },
            gridLines: {
                color: "#fff",
                borderDash: [1, 82],
            }
        }],
        xAxes: [{
            gridLines: {
                display: false,
            }
        }]
    }
}

var chart_performance_1 = new Chart(ctx1, {
    type: 'line',
    data: {
        labels: days,
        datasets: [{
            data: [11, 7, 3, 5, 2, 3],
            borderColor: '#fff',
            borderWidth: 1
        }],
    },
    options: default_chart_options
});

var chart_performance_2 = new Chart(ctx2, {
    type: 'line',
    data: {
        labels: days,
        datasets: [{
            data: [48, 51, 32, 26, 29, 38],
            borderColor: '#fff',
            borderWidth: 1
        }],
    },
    options: default_chart_options
});