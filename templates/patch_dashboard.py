#!/usr/bin/env python3
path = '/opt/RepeaterWatch/static/js/dashboard.js'
content = open(path).read()

OLD = """            document.getElementById('di-name').textContent = d.name || '--';
            document.getElementById('di-firmware').textContent = d.firmware || '--';
            document.getElementById('di-board').textContent = d.board || '--';
            document.getElementById('di-radio-config').textContent = d.radio_config || '--';"""

NEW = """            document.getElementById('di-name').textContent = d.name || '--';
            document.getElementById('di-firmware').textContent = d.firmware || '--';
            document.getElementById('di-board').textContent = d.board || '--';
            (function(rc) {
                var parts = (rc || '').split(',');
                var freq = parseFloat(parts[0]);
                document.getElementById('di-freq').textContent = freq ? freq.toFixed(3) + ' MHz' : '--';
                document.getElementById('di-bw').textContent  = parts[1] ? parts[1] + ' kHz' : '--';
                document.getElementById('di-sf').textContent  = parts[2] ? 'SF' + parts[2] : '--';
                document.getElementById('di-cr').textContent  = parts[3] ? '4/' + parts[3] : '--';
            })(d.radio_config);"""

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    open(path, 'w').write(content)
    print("dashboard.js patched OK")
else:
    print("NOT FOUND - checking what is there:")
    idx = content.find("di-name")
    if idx >= 0:
        print(repr(content[idx-20:idx+300]))
    else:
        print("di-name not found at all")
