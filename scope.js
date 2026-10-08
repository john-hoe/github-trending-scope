/* Trending Scope · 星光画布（一闪一闪的星点 + 偶尔一颗流星）与章节跳转。无依赖。 */
(function () {
  var cv = document.getElementById('stars');
  if (cv && cv.getContext) {
    var cx = cv.getContext('2d'), W = 0, H = 0, dpr = Math.min(window.devicePixelRatio || 1, 2), stars = [], meteors = [], nextMeteor = 3;
    var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var rnd = function (a, b) { return a + Math.random() * (b - a); };
    var seed = function () {
      W = innerWidth; H = innerHeight; cv.width = W * dpr; cv.height = H * dpr; cx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var n = Math.round(Math.min(260, W * H / 6000)); stars = [];
      for (var i = 0; i < n; i++) {
        var onBand = i < n * 0.7, x = rnd(0, W), y = onBand ? H * 0.55 - (x - W / 2) * 0.16 + (rnd(-1, 1) + rnd(-1, 1)) * H * 0.14 : rnd(0, H);
        stars.push({ x: x, y: y, r: Math.random() > 0.85 ? 3 : Math.random() > 0.5 ? 2 : 1.4, base: rnd(0.3, 0.55), peak: rnd(0.9, 1), sp: rnd(0.5, 1.6), ph: rnd(0, 6.28), cross: Math.random() > 0.93 });
      }
    };
    var frame = function (t) {
      t /= 1000; cx.clearRect(0, 0, W, H);
      for (var i = 0; i < stars.length; i++) {
        var s = stars[i], k = still ? 0.4 : (Math.sin(t * s.sp + s.ph) + 1) / 2, a = s.base + (s.peak - s.base) * k * k;
        cx.fillStyle = 'rgba(255,255,255,' + a.toFixed(3) + ')'; cx.fillRect(s.x, s.y, s.r, s.r);
        if (s.cross && k > 0.7) { cx.strokeStyle = 'rgba(255,255,255,' + (a * 0.9).toFixed(3) + ')'; cx.lineWidth = 1.4; cx.beginPath(); cx.moveTo(s.x - 15, s.y + s.r / 2); cx.lineTo(s.x + 15, s.y + s.r / 2); cx.moveTo(s.x + s.r / 2, s.y - 15); cx.lineTo(s.x + s.r / 2, s.y + 15); cx.stroke(); }
      }
      if (!still) {
        if (t > nextMeteor) { var len = rnd(120, 220), ang = rnd(24, 36) * Math.PI / 180; meteors.push({ x: rnd(W * 0.35, W), y: rnd(-20, H * 0.4), vx: -Math.cos(ang), vy: Math.sin(ang), len: len, t0: t, life: rnd(0.7, 1.1) }); nextMeteor = t + rnd(4, 9); }
        for (var j = meteors.length - 1; j >= 0; j--) {
          var m = meteors[j], p = (t - m.t0) / m.life; if (p >= 1) { meteors.splice(j, 1); continue; }
          var d = p * 900, hx = m.x + m.vx * d, hy = m.y + m.vy * d, al = (1 - p) * 0.9, g = cx.createLinearGradient(hx, hy, hx - m.vx * m.len, hy - m.vy * m.len);
          g.addColorStop(0, 'rgba(255,255,255,' + al.toFixed(3) + ')'); g.addColorStop(1, 'rgba(255,255,255,0)');
          cx.strokeStyle = g; cx.lineWidth = 1.5; cx.beginPath(); cx.moveTo(hx, hy); cx.lineTo(hx - m.vx * m.len, hy - m.vy * m.len); cx.stroke();
        }
        requestAnimationFrame(frame);
      }
    };
    seed(); addEventListener('resize', function () { seed(); if (still) frame(0); });
    if (still) frame(0); else requestAnimationFrame(frame);
  }
  // 章节：点击跳到长视频对应时间；播放时高亮当前章节
  var v = document.getElementById('long-video'), list = document.getElementById('chapters');
  if (v && list) {
    var btns = [].slice.call(list.querySelectorAll('button[data-t]'));
    btns.forEach(function (b) { b.addEventListener('click', function () { v.currentTime = parseFloat(b.dataset.t); var p = v.play(); if (p && p.catch) p.catch(function () {}); }); });
    v.addEventListener('timeupdate', function () {
      var cur = -1; btns.forEach(function (b, i) { if (v.currentTime + 0.3 >= parseFloat(b.dataset.t)) cur = i; });
      btns.forEach(function (b, i) { b.classList.toggle('on', i === cur); });
    });
  }
})();
