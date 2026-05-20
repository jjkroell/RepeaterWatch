var NeighbourSignalCharts = (function () {
    var snrChart = null;
    var rssiChart = null;

    var COLORS = ['#06d6a0', '#ef476f', '#ffd166', '#00b4d8', '#a78bfa', '#fb923c', '#f472b6', '#34d399'];

    var TT = { trigger: 'axis', backgroundColor: 'rgba(30,30,50,0.95)', borderColor: '#555', textStyle: { color: '#e0e0e0' } };
    var AX = { axisLine: { lineStyle: { color: '#888' } }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } } };

    function makeBaseOption(yName) {
        return {
            backgroundColor: 'transparent',
            tooltip: TT,
            legend: {
                textStyle: { fontSize: 11, color: '#aaa' },
                top: 0,
            },
            xAxis: { type: 'time', axisLine: AX.axisLine, splitLine: AX.splitLine },
            yAxis: {
                type: 'value',
                name: yName,
                nameTextStyle: { color: '#888' },
                axisLine: AX.axisLine,
                splitLine: AX.splitLine,
            },
            dataZoom: [
                { type: 'inside', xAxisIndex: 0 },
                { type: 'slider', xAxisIndex: 0, height: 20, bottom: 5 },
            ],
            series: [],
            grid: { left: 55, right: 20, top: 30, bottom: 50 },
        };
    }

    function init(snrEl, rssiEl) {
        snrChart = echarts.init(snrEl);
        snrChart.setOption(makeBaseOption('dB'));

        rssiChart = echarts.init(rssiEl);
        rssiChart.setOption(makeBaseOption('dBm'));
    }

    function update(data) {
        if (!snrChart || !rssiChart) return;

        var keys = Object.keys(data || {});
        var snrSeries = [];
        var rssiSeries = [];
        var legendNames = [];

        for (var i = 0; i < keys.length; i++) {
            var pubkey = keys[i];
            var neighbour = data[pubkey];
            var color = COLORS[i % COLORS.length];
            var name = neighbour.name || pubkey;
            var timestamps = neighbour.timestamps || [];
            var snrVals = neighbour.snr || [];
            var rssiVals = neighbour.rssi || [];

            var snrData = [];
            var rssiData = [];

            for (var j = 0; j < timestamps.length; j++) {
                var t = timestamps[j] * 1000;
                if (snrVals[j] !== null && snrVals[j] !== undefined) {
                    snrData.push([t, snrVals[j]]);
                }
                if (rssiVals[j] !== null && rssiVals[j] !== undefined) {
                    rssiData.push([t, rssiVals[j]]);
                }
            }

            legendNames.push(name);

            snrSeries.push({
                name: name,
                type: 'line',
                smooth: true,
                symbol: 'none',
                lineStyle: { width: 2, color: color },
                itemStyle: { color: color },
                data: snrData,
            });

            rssiSeries.push({
                name: name,
                type: 'line',
                smooth: true,
                symbol: 'none',
                lineStyle: { width: 2, color: color },
                itemStyle: { color: color },
                data: rssiData,
            });
        }

        snrChart.setOption({ legend: { data: legendNames }, series: snrSeries }, { replaceMerge: ['series'] });
        rssiChart.setOption({ legend: { data: legendNames }, series: rssiSeries }, { replaceMerge: ['series'] });
    }

    function resize() {
        if (snrChart) snrChart.resize();
        if (rssiChart) rssiChart.resize();
    }

    return { init: init, update: update, resize: resize };
})();
