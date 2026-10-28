/* =====================================================================
   SmartPhDs payment links
   Paste each Stripe Payment Link between the quotes, then upload this file.
   A link looks like: https://buy.stripe.com/abc123...
   Until a link is added, its button opens an email to smartphds1@gmail.com
   so visitors can still order.
   ===================================================================== */
var SMARTPHDS_PAYMENT_LINKS = {
  launch: "https://buy.stripe.com/fZu4gz2v1cdj1Ade8nak000",        // Launch (Beginner), $99
  accelerate: "https://buy.stripe.com/8x26oH5Hdb9ffr34xNak001",    // Accelerate (Intermediate), $300
  breakthrough: "https://buy.stripe.com/4gM9AT3z57X3fr3d4jak002"   // Breakthrough (Advanced), $600
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
