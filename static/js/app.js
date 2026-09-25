/* CIVIC-AI CI — frontend vanilla, communique avec l'API réelle. */
(function () {
  "use strict";

  var input = document.getElementById("query");
  var button = document.getElementById("search-btn");
  var errorBox = document.getElementById("error");
  var result = document.getElementById("result");
  var title = document.getElementById("result-title");
  var badge = document.getElementById("badge");
  var message = document.getElementById("result-message");
  var details = document.getElementById("result-details");
  var sources = document.getElementById("result-sources");

  function showError(text) {
    errorBox.textContent = text;
    errorBox.hidden = !text;
  }

  function valueOrUnknown(value) {
    if (value === null || value === undefined || value === "") {
      return '<span class="unknown-text">Non vérifié</span>';
    }
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function render(data) {
    result.hidden = false;
    if (data.match_status === "UNKNOWN" || !data.procedure) {
      title.textContent = "Aucune démarche reconnue";
      badge.textContent = "UNKNOWN";
      badge.className = "badge unknown";
      message.textContent = data.message;
      details.innerHTML = "";
      sources.textContent = "Aucune source disponible pour cette demande.";
      return;
    }
    var p = data.procedure;
    title.textContent = p.name;
    badge.textContent = p.verification_status;
    badge.className = "badge " + (p.verification_status === "VERIFIED" ? "verified" : "unknown");
    message.textContent = data.message;

    var docs = Array.isArray(p.requirements) && p.requirements.length
      ? p.requirements.map(function (d) {
          return "<li>" + valueOrUnknown(d) + "</li>";
        }).join("")
      : '<span class="unknown-text">Non vérifié — aucune liste officielle renseignée.</span>';

    details.innerHTML =
      "<dt>Résumé</dt><dd>" + valueOrUnknown(p.summary) + "</dd>" +
      "<dt>Documents requis</dt><dd><ul>" + docs + "</ul></dd>" +
      "<dt>Coût</dt><dd>" + valueOrUnknown(p.cost) + "</dd>" +
      "<dt>Délai</dt><dd>" + valueOrUnknown(p.delay) + "</dd>" +
      "<dt>Autorité compétente</dt><dd>" + valueOrUnknown(p.competent_authority) + "</dd>";

    sources.textContent = Array.isArray(p.sources) && p.sources.length
      ? p.sources.join(", ")
      : "Aucune source vérifiée pour le moment.";
  }

  async function search(query) {
    showError("");
    if (!query || !query.trim()) {
      showError("Veuillez saisir votre besoin administratif.");
      return;
    }
    button.disabled = true;
    try {
      var res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query })
      });
      if (!res.ok) {
        var detail = "Erreur " + res.status;
        try {
          var err = await res.json();
          if (err && err.detail) detail = JSON.stringify(err.detail);
        } catch (e) { /* réponse non JSON */ }
        showError("La recherche a échoué : " + detail);
        return;
      }
      var data = await res.json();
      render(data);
    } catch (e) {
      showError("Impossible de contacter le service. Vérifiez que le serveur est démarré.");
    } finally {
      button.disabled = false;
    }
  }

  button.addEventListener("click", function () { search(input.value); });
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") search(input.value);
  });
  document.querySelectorAll(".example").forEach(function (el) {
    el.addEventListener("click", function () {
      input.value = el.getAttribute("data-query");
      search(input.value);
    });
  });
})();
