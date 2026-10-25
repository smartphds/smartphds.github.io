/* Print button on the checklist page (kept out of the HTML so the security policy can block inline scripts). */
(function () {
  var b = document.getElementById("print-btn");
  if (b) b.addEventListener("click", function () { window.print(); });
})();
