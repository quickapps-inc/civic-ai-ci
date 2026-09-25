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

  var STATUS_LABELS = {
    VERIFIED: "Information vérifiée",
    PARTIALLY_VERIFIED: "Information partiellement vérifiée",
    UNVERIFIED: "Information non encore vérifiée"
  };
  var UNKNOWN_TEXT = "Information non disponible / non vérifiée";

  function showError(text) {
    errorBox.textContent = text;
    errorBox.hidden = !text;
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function valueOrUnknown(value) {
    if (value === null || value === undefined || value === "") {
      return '<span class="unknown-text">' + UNKNOWN_TEXT + "</span>";
    }
    return escapeHtml(value);
  }

  function statusLabel(status) {
    return STATUS_LABELS[status] || status || UNKNOWN_TEXT;
  }

  function badgeClass(status) {
    if (status === "VERIFIED") return "badge verified";
    if (status === "PARTIALLY_VERIFIED") return "badge partial";
    return "badge unknown";
  }

  function renderSources(list) {
    if (!Array.isArray(list) || !list.length) {
      sources.textContent = "Aucune source vérifiée pour le moment.";
      return;
    }
    sources.innerHTML = "";
    var ul = document.createElement("ul");
    ul.className = "sources-list";
    list.forEach(function (s) {
      var li = document.createElement("li");
      if (s && typeof s === "object" && s.url) {
        var a = document.createElement("a");
        a.href = s.url;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.textContent = s.title || s.url;
        li.appendChild(a);
        var meta = [];
        if (s.organization) meta.push(s.organization);
        if (s.verified_at) meta.push("vérifié le " + s.verified_at);
        if (meta.length) {
          li.appendChild(document.createTextNode(" — " + meta.join(" — ")));
        }
      } else {
        li.textContent = String(s);
      }
      ul.appendChild(li);
    });
    sources.innerHTML = "";
    sources.appendChild(ul);
  }

  function render(data) {
    result.hidden = false;
    if (data.match_status === "UNKNOWN" || !data.procedure) {
      title.textContent = "Aucune démarche reconnue";
      badge.textContent = "UNKNOWN";
      badge.className = "badge unknown";
      message.textContent = data.message;
      details.innerHTML = "";
      renderSources([]);
      return;
    }
    var p = data.procedure;
    var v = data.variant || null;
    // La fiche affichée : la variante si connue, sinon la procédure générique.
    var shown = v || p;
    var effectiveStatus = data.verification_status || p.verification_status;

    title.textContent = p.name;
    badge.textContent = statusLabel(effectiveStatus);
    badge.className = badgeClass(effectiveStatus);
    message.textContent = data.message;

    var variantRow;
    if (v) {
      variantRow = escapeHtml(v.name);
    } else if (data.needs_clarification) {
      variantRow = '<span class="unknown-text">À préciser — aucune variante choisie arbitrairement. Voir message ci-dessus.</span>';
    } else if (Array.isArray(p.variants) && p.variants.length) {
      variantRow = '<span class="unknown-text">Fiche générique — précisez votre situation pour afficher une variante.</span>';
    } else {
      variantRow = '<span class="unknown-text">Sans objet (pas de variante pour cette démarche).</span>';
    }

    var docs = Array.isArray(shown.requirements) && shown.requirements.length
      ? shown.requirements.map(function (d) {
          return "<li>" + escapeHtml(d) + "</li>";
        }).join("")
      : '<span class="unknown-text">' + UNKNOWN_TEXT + " — aucune liste officielle renseignée.</span>";

    var verifiedAt = shown.verified_at || p.verified_at;

    details.innerHTML =
      "<dt>Procédure</dt><dd>" + escapeHtml(p.name) + "</dd>" +
      "<dt>Variante</dt><dd>" + variantRow + "</dd>" +
      "<dt>Résumé</dt><dd>" + valueOrUnknown(p.summary) + "</dd>" +
      (v && v.notes ? "<dt>Note (variante)</dt><dd>" + escapeHtml(v.notes) + "</dd>" : "") +
      (!v && p.notes ? "<dt>Note</dt><dd>" + escapeHtml(p.notes) + "</dd>" : "") +
      "<dt>Documents / informations requis</dt><dd><ul>" + docs + "</ul></dd>" +
      "<dt>Coût</dt><dd>" + valueOrUnknown(shown.cost) + "</dd>" +
      "<dt>Délai</dt><dd>" + valueOrUnknown(shown.delay) + "</dd>" +
      "<dt>Autorité compétente</dt><dd>" + valueOrUnknown(shown.competent_authority) + "</dd>" +
      "<dt>Statut de vérification</dt><dd>" + escapeHtml(statusLabel(effectiveStatus)) + " (" + escapeHtml(effectiveStatus || "?") + ")</dd>" +
      "<dt>Date de vérification</dt><dd>" + valueOrUnknown(verifiedAt) + "</dd>";

    renderSources(v && v.sources && v.sources.length ? v.sources : p.sources);
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
