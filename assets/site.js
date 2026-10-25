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
    DS: { name: "Data Scientist / Machine Learning", desc: "You turn messy data into answers. Data scientists build models and analyses for tech, biotech, finance and almost every other industry." },
    CON: { name: "Management Consultant", desc: "You like solving new problems with smart people. Consultants break down business questions fast, and firms actively recruit PhDs." },
    PM: { name: "Product Manager", desc: "You want to build things people use. Product managers decide what gets built and why, working between users, engineers and business teams." },
    RD: { name: "Industry R&D Scientist", desc: "You love the bench. Industry scientists run experiments that lead to real products, in biotech, chemicals, materials, food, energy and more." },
    RA: { name: "Regulatory Affairs / Quality", desc: "You care about getting it right. Regulatory and quality professionals make sure products meet the rules before they reach people." },
    MSL: { name: "Medical Science Liaison", desc: "You enjoy explaining science to experts. MSLs discuss clinical data with physicians and researchers on behalf of life-science companies." },
    WR: { name: "Science or Medical Writer", desc: "Writing is your strength. Science writers produce documents, content and communications for companies, publishers and agencies." },
    PAT: { name: "Patent Agent / IP Specialist", desc: "You combine deep science with precise writing. Patent professionals help protect inventions, and many law firms train PhDs." },
    FIN: { name: "Quant / Finance Analyst", desc: "You think in models and numbers. Quantitative and research analysts apply PhD-level math and data skills to markets and investments." },
    POL: { name: "Science Policy Advisor", desc: "You want your expertise to shape decisions. Policy roles in government, non-profits and think tanks turn evidence into guidance." }
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
