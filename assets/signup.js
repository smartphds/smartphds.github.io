/* SmartPhDs email sign-up (MailerLite). Sends the form in the background and shows a thank-you message.
   Without JavaScript the form still works: it opens MailerLite's confirmation in a new tab. */
(function () {
  var forms = document.querySelectorAll("form.signup-form");
  Array.prototype.forEach.call(forms, function (form) {
    form.addEventListener("submit", function (e) {
      var email = form.querySelector('input[type="email"]');
      if (!email || !email.value || !email.checkValidity()) return; // let the browser show its message
      e.preventDefault();
      var btn = form.querySelector("button");
      var msg = form.parentNode.querySelector(".signup-msg");
      if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }
      fetch(form.action, { method: "POST", mode: "no-cors", body: new FormData(form) })
        .then(function () {
          form.hidden = true;
          if (msg) { msg.hidden = false; msg.textContent = "You're in. Check your inbox for the checklist and your first tips."; msg.focus(); }
        })
        .catch(function () {
          if (btn) { btn.disabled = false; btn.textContent = "Send me the tips"; }
          if (msg) { msg.hidden = false; msg.textContent = "Something went wrong. Please try again, or email smartphds1@gmail.com."; }
        });
    });
  });
})();
