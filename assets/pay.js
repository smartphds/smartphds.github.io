/* =====================================================================
   SmartPhDs payment links
   Paste each Stripe Payment Link between the quotes, then upload this file.
   A link looks like: https://buy.stripe.com/abc123...
   Until a link is added, its button opens an email to hello@smartphds.com
   so visitors can still order.
   ===================================================================== */
var SMARTPHDS_PAYMENT_LINKS = {
  launch: "",        // Launch (Beginner), $39
  accelerate: "",    // Accelerate (Intermediate), $149
  breakthrough: ""   // Breakthrough (Advanced), $199
};

(function () {
  var ok = /^https:\/\/(buy|checkout)\.stripe\.com\/[A-Za-z0-9_\/-]+(\?[^\s"'<>]*)?$/;
  var buttons = document.querySelectorAll("[data-pay]");
  Array.prototype.forEach.call(buttons, function (el) {
    var url = SMARTPHDS_PAYMENT_LINKS[el.getAttribute("data-pay")] || "";
    if (ok.test(url)) {
      el.setAttribute("href", url);
    } else {
      var plan = el.getAttribute("data-plan") || "SmartPhDs";
      el.setAttribute("href", "mailto:hello@smartphds.com?subject=" + encodeURIComponent("Order: " + plan + " package"));
    }
  });
})();
