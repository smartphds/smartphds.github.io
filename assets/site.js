/* SmartPhDs homepage interactions: rotating resume examples and the role finder. */
(function () {
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Rotating before/after examples */
  var examples = Array.prototype.slice.call(document.querySelectorAll(".redline .ex"));
  var count = document.getElementById("ex-count");
  if (examples.length && count) {
    var current = 0, timer = null;
    var show = function (i) {
      current = (i + examples.length) % examples.length;
      examples.forEach(function (ex, n) {
        ex.hidden = n !== current;
        if (n === current && !reduceMotion) {
          ex.classList.remove("enter");
          void ex.offsetWidth; // restart animation
          ex.classList.add("enter");
        }
      });
      count.textContent = (current + 1) + " / " + examples.length;
    };
    var start = function () { if (!reduceMotion && !timer) timer = setInterval(function () { show(current + 1); }, 6500); };
    var stop = function () { clearInterval(timer); timer = null; };
    document.getElementById("ex-prev").addEventListener("click", function () { stop(); show(current - 1); });
    document.getElementById("ex-next").addEventListener("click", function () { stop(); show(current + 1); });
    var card = document.querySelector(".redline");
    card.addEventListener("mouseenter", stop);
    card.addEventListener("focusin", stop);
    start();
  }

  /* Role finder */
  var form = document.getElementById("finder-form");
  if (!form) return;
  var roles = {
    RA: { name: "Regulatory Affairs", desc: "You turn research data into the submissions that get drugs approved." },
    QA: { name: "Quality Assurance / Control", desc: "You make sure every batch is right before it reaches patients." },
    AD: { name: "Analytical Development", desc: "You build and validate the methods that test every drug." },
    MSL: { name: "Medical Science Liaison", desc: "You meet physicians and explain the science behind new treatments." },
    MW: { name: "Medical Writing", desc: "You write the documents regulators and doctors rely on." },
    CMC: { name: "CMC & Tech Transfer", desc: "You move drugs from the lab into manufacturing." }
  };
  var bar = document.getElementById("progress-bar");
  var empty = document.getElementById("result-empty");
  var full = document.getElementById("result-full");

  var update = function () {
    var answered = ["q1", "q2", "q3"].map(function (q) { return form.querySelector('input[name="' + q + '"]:checked'); });
    var done = answered.filter(Boolean).length;
    bar.style.width = (done / 3 * 100) + "%";
    if (done < 3) { empty.hidden = false; full.hidden = true; return; }
    var score = {};
    answered.forEach(function (input) {
      input.value.split(",").forEach(function (pair) {
        var p = pair.split(":"); score[p[0]] = (score[p[0]] || 0) + Number(p[1]);
      });
    });
    var ranked = Object.keys(score).sort(function (a, b) { return score[b] - score[a]; });
    var best = roles[ranked[0]];
    document.getElementById("result-role").textContent = best.name;
    document.getElementById("result-desc").textContent = best.desc;
    document.getElementById("result-alt").textContent = ranked[1] ? "Also worth a look: " + roles[ranked[1]].name : "";
    empty.hidden = true; full.hidden = false;
  };
  form.addEventListener("change", update);
  document.getElementById("finder-reset").addEventListener("click", function () {
    form.reset(); update(); document.getElementById("q1a").focus();
  });
  update();
})();
