var NeighbourSignalCharts = (function () {
    var snrChart = null;
    var rssiChart = null;
    var _data = {};

    var AX = { axisLine: { lineStyle: { color: '#888' } }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } } };

    function colorFromKey(key) {
        var hash = 0;
        for (var i = 0; i < key.length; i++) {
            hash = Math.imul(31, hash) + key.charCodeAt(i) | 0;
        }
        var hue = (hash >>> 0) % 360;
        return 'hsl(' + hue + ', 72%, 62%)';
    }

    function fmtTime(tsMs) {
        var d = new Date(tsMs);
        var hh = d.getHours().toString().padStart(2, '0');
        var mm = d.getMinutes().toString().padStart(2, '0');
        var ss = d.getSeconds().toString().padStart(2, '0');
        return (d.getMonth() + 1) + '/' + d.getDate() + '  ' + hh + ':' + mm + ':' + ss;
    }

    function makeBaseOption(yName, unit) {
        return {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'item',
                backgroundColor: 'rgba(30,30,50,0.95)',
                borderColor: '#555',
                textStyle: { color: '#e0e0e0' },
                formatter: function (p) {
                    var d = new Date(p.value[0]);
                    var hh = d.getHours().toString().padStart(2, '0');
                    var mm = d.getMinutes().toString().padStart(2, '0');
                    var dd = (d.getMonth() + 1) + '/' + d.getDate();
                    return p.marker + ' <b>' + p.seriesName + '</b><br/>'
                         + dd + ' ' + hh + ':' + mm + ' &nbsp;·&nbsp; ' + p.value[1] + ' ' + unit;
                },
            },
            legend: {
                type: 'scroll',
                top: 0,
                textStyle: { fontSize: 11, color: '#aaa' },
                pageTextStyle: { color: '#aaa' },
                pageIconColor: '#aaa',
                pageIconInactiveColor: '#555',
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
            grid: { left: 55, right: 20, top: 50, bottom: 50 },
        };
    }

    function makeSeries(name, color, data) {
        return {
            name: name,
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 5,
            itemStyle: { color: color, opacity: 0.55 },
            lineStyle: { width: 2, color: color },
            emphasis: {
                focus: 'series',
                symbolSize: 9,
                itemStyle: { opacity: 1, color: color },
                lineStyle: { width: 3.5, color: color },
            },
            blur: {
                lineStyle: { opacity: 0.12, width: 1 },
                itemStyle: { opacity: 0.1 },
            },
            data: data,
        };
    }

    /* ── Modal ──────────────────────────────────────────────── */

    function findPubkey(seriesName) {
        var keys = Object.keys(_data);
        for (var i = 0; i < keys.length; i++) {
            if ((_data[keys[i]].name || keys[i]) === seriesName) return keys[i];
        }
        return null;
    }

    function nearestValue(pubkey, field, tsMs) {
        var n = _data[pubkey];
        if (!n) return null;
        var ts = n.timestamps || [];
        var vals = n[field] || [];
        var tsS = tsMs / 1000;
        var minDiff = Infinity, best = null;
        for (var i = 0; i < ts.length; i++) {
            var diff = Math.abs(ts[i] - tsS);
            if (diff < minDiff) { minDiff = diff; best = vals[i]; }
        }
        return best;
    }

    function calcStats(arr) {
        var clean = arr.filter(function (v) { return v !== null && v !== undefined; });
        if (!clean.length) return null;
        var sum = 0, mn = Infinity, mx = -Infinity;
        clean.forEach(function (v) { sum += v; if (v < mn) mn = v; if (v > mx) mx = v; });
        return { min: mn, max: mx, avg: sum / clean.length, n: clean.length };
    }

    function setText(id, val) {
        var el = document.getElementById(id);
        if (el) el.textContent = val;
    }

    function showModal(seriesName, pubkey, tsMs, snrVal, rssiVal) {
        var n = _data[pubkey] || {};
        var color = colorFromKey(pubkey);
        var snrStats  = calcStats(n.snr  || []);
        var rssiStats = calcStats(n.rssi || []);

        function fmtSNR(v)  { return v !== null && v !== undefined ? v.toFixed(1) + ' dB'  : '—'; }
        function fmtRSSI(v) { return v !== null && v !== undefined ? v.toFixed(1) + ' dBm' : '—'; }
        function fmtStat(s, fmt) {
            if (!s) return { min: '—', avg: '—', max: '—' };
            return { min: fmt(s.min), avg: fmt(s.avg), max: fmt(s.max) };
        }

        var ss = fmtStat(snrStats,  fmtSNR);
        var rs = fmtStat(rssiStats, fmtRSSI);

        var swatch = document.getElementById('modal-nb-swatch');
        if (swatch) swatch.style.background = color;

        setText('modal-nb-name',    seriesName);
        setText('modal-nb-pubkey',  pubkey);
        setText('modal-nb-time',    fmtTime(tsMs));
        setText('modal-nb-snr-pt',  fmtSNR(snrVal));
        setText('modal-nb-rssi-pt', fmtRSSI(rssiVal));
        setText('modal-nb-snr-min',  ss.min);
        setText('modal-nb-snr-avg',  ss.avg);
        setText('modal-nb-snr-max',  ss.max);
        setText('modal-nb-rssi-min', rs.min);
        setText('modal-nb-rssi-avg', rs.avg);
        setText('modal-nb-rssi-max', rs.max);
        setText('modal-nb-sightings', (n.timestamps || []).length);

        var overlay = document.getElementById('nb-signal-modal');
        if (overlay) overlay.classList.add('open');
    }

    function closeModal() {
        var overlay = document.getElementById('nb-signal-modal');
        if (overlay) overlay.classList.remove('open');
    }

    function setupModal() {
        var overlay = document.getElementById('nb-signal-modal');
        if (!overlay) return;
        document.getElementById('nb-modal-close').addEventListener('click', closeModal);
        overlay.addEventListener('click', function (e) { if (e.target === overlay) closeModal(); });
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeModal(); });
    }

    /* ── Init ───────────────────────────────────────────────── */

    function init(snrEl, rssiEl) {
        snrChart = echarts.init(snrEl);
        snrChart.setOption(makeBaseOption('dB', 'dB'));
        snrChart.on('click', function (p) {
            var pubkey = findPubkey(p.seriesName);
            if (!pubkey) return;
            var rssiVal = nearestValue(pubkey, 'rssi', p.value[0]);
            showModal(p.seriesName, pubkey, p.value[0], p.value[1], rssiVal);
        });

        rssiChart = echarts.init(rssiEl);
        rssiChart.setOption(makeBaseOption('dBm', 'dBm'));
        rssiChart.on('click', function (p) {
            var pubkey = findPubkey(p.seriesName);
            if (!pubkey) return;
            var snrVal = nearestValue(pubkey, 'snr', p.value[0]);
            showModal(p.seriesName, pubkey, p.value[0], snrVal, p.value[1]);
        });

        setupModal();
    }

    function update(data) {
        if (!snrChart || !rssiChart) return;
        _data = data || {};

        var keys = Object.keys(_data);
        var snrSeries = [], rssiSeries = [], legendNames = [];

        for (var i = 0; i < keys.length; i++) {
            var pubkey = keys[i];
            var neighbour = _data[pubkey];
            var color = colorFromKey(pubkey);
            var name = neighbour.name || pubkey;
            var timestamps = neighbour.timestamps || [];
            var snrVals  = neighbour.snr  || [];
            var rssiVals = neighbour.rssi || [];

            var snrData = [], rssiData = [];
            for (var j = 0; j < timestamps.length; j++) {
                var t = timestamps[j] * 1000;
                if (snrVals[j]  !== null && snrVals[j]  !== undefined) snrData.push([t,  snrVals[j]]);
                if (rssiVals[j] !== null && rssiVals[j] !== undefined) rssiData.push([t, rssiVals[j]]);
            }

            legendNames.push(name);
            snrSeries.push(makeSeries(name, color, snrData));
            rssiSeries.push(makeSeries(name, color, rssiData));
        }

        snrChart.setOption( { legend: { data: legendNames }, series: snrSeries  }, { replaceMerge: ['series'] });
        rssiChart.setOption({ legend: { data: legendNames }, series: rssiSeries }, { replaceMerge: ['series'] });
    }

    function resize() {
        if (snrChart)  snrChart.resize();
        if (rssiChart) rssiChart.resize();
    }

    return { init: init, update: update, resize: resize };
})();
