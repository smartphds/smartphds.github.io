/* =====================================================================
   SmartPhDs payment links
   Paste each Stripe Payment Link between the quotes, then upload this file.
   A link looks like: https://buy.stripe.com/abc123...
   Until a link is added, its button opens an email to smartphds1@gmail.com
   so visitors can still order.
   ===================================================================== */
var SMARTPHDS_PAYMENT_LINKS = {
  launch: "",        // Launch (Beginner), $99
  accelerate: "",    // Accelerate (Intermediate), $300
  breakthrough: ""   // Breakthrough (Advanced), $600
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
      var body = "Hi SmartPhDs,\n\nI'd like the " + plan + " package.\n\nTarget role(s): \nIndustry or field: \nLinks to 2-3 job postings: \nDeadline, if any: \n\nI've attached my current CV.\n";
      el.setAttribute("href", "mailto:smartphds1@gmail.com?subject=" + encodeURIComponent("Order: " + plan + " package") + "&body=" + encodeURIComponent(body));
    }
  });
})();
