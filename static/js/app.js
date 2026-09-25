/* CIVIC-AI CI — interface citoyenne (vanilla JS, API réelle, rien en dur). */
(function () {
  "use strict";

  var input = document.getElementById("query");
  var button = document.getElementById("search-btn");
  var errorBox = document.getElementById("error");
  var loadingBox = document.getElementById("loading");
  var result = document.getElementById("result");
  var resultBody = document.getElementById("result-body");
  var intro = document.getElementById("intro");

  var UNKNOWN_TEXT = "Information non disponible ou non encore vérifiée";

  var STATUS_COPY = {
    VERIFIED: {
      icon: "✓",
      css: "verified",
      title: "Informations de cette démarche vérifiées",
      detail: "Ces informations ont été vérifiées à partir des sources officielles indiquées ci-dessous."
    },
    PARTIALLY_VERIFIED: {
      icon: "⚠",
      css: "partial",
      title: "Certaines informations restent à vérifier",
      detail: "Une partie des informations est vérifiée. Ce qui n'a pas pu être vérifié est signalé plutôt qu'inventé."
    },
    UNVERIFIED: {
      icon: "○",
      css: "unverified",
      title: "Informations non encore vérifiées",
      detail: "Cette démarche est identifiée, mais ses informations détaillées n'ont pas encore été vérifiées. Consultez la source officielle."
    }
  };

  // Phrases internes de gouvernance de données : restent dans le JSON,
  // ne sont jamais affichées au citoyen.
  var INTERNAL_NOTE_PATTERN =
    /ne pas fusionner|dans cette mission|non fournis|non v[eé]rifi[eé]s?,?\s+donc non encod|encod[eé]e?s?|UNKNOWN|FAUX|arbitrairement\s*\(principe/i;

  var VARIANT_QUERY_BY_ID = {
    "premiere-demande": "Je veux ma première CNI",
    "renouvellement": "Je veux renouveler ma CNI",
    "duplicata-perte": "J'ai perdu ma CNI",
    "copie-extrait-egare": "J'ai perdu mon extrait de naissance"
  };

  function showError(text) {
    errorBox.textContent = text || "";
    errorBox.hidden = !text;
  }

  function setLoading(active) {
    loadingBox.hidden = !active;
    button.disabled = !!active;
    result.setAttribute("aria-busy", active ? "true" : "false");
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function sanitizePublicText(value) {
    // Défense : même si l'API renvoyait un jour une formulation interne,
    // l'interface publique ne l'affiche jamais telle quelle.
    return String(value || "")
      .replace(/\(principe\s+UNKNOWN\s*>\s*FAUX\)/gi, "")
      .replace(/principe\s*:\s*UNKNOWN\s*>\s*FAUX/gi, "")
      .replace(/UNKNOWN\s*>\s*FAUX/gi, "")
      .replace(/\s{2,}/g, " ")
      .trim();
  }

  function cleanCitizenNote(note) {
    if (!note) return "";
    var sentences = String(note).split(/(?<=[.!?])\s+/);
    var kept = sentences.filter(function (s) {
      var t = s.trim();
      if (!t) return false;
      return !INTERNAL_NOTE_PATTERN.test(t);
    });
    return kept.join(" ").trim();
  }

  function formatVerifiedDate(iso) {
    if (!iso) return "";
    var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso));
    if (!m) return String(iso);
    var months = [
      "janvier", "février", "mars", "avril", "mai", "juin",
      "juillet", "août", "septembre", "octobre", "novembre", "décembre"
    ];
    var day = parseInt(m[3], 10);
    var month = months[parseInt(m[2], 10) - 1] || m[2];
    return "Vérifié le " + day + " " + month + " " + m[1];
  }

  function statusCopy(status) {
    return STATUS_COPY[status] || STATUS_COPY.UNVERIFIED;
  }

  function renderTrustStatus(status) {
    var copy = statusCopy(status);
    return (
      '<div class="trust-status ' + copy.css + '" role="status">' +
      '<span class="status-icon" aria-hidden="true">' + copy.icon + "</span>" +
      "<div><strong>" + escapeHtml(copy.title) + "</strong>" +
      "<span>" + escapeHtml(copy.detail) + "</span></div>" +
      "</div>"
    );
  }

  function renderDocs(requirements) {
    if (Array.isArray(requirements) && requirements.length) {
      return (
        '<ul class="docs-list">' +
        requirements.map(function (d) { return "<li>" + escapeHtml(d) + "</li>"; }).join("") +
        "</ul>"
      );
    }
    return '<p class="unknown-text">' + escapeHtml(UNKNOWN_TEXT) + " — aucune liste officielle renseignée pour ce cas.</p>";
  }

  function renderSimpleValue(value, strong) {
    if (value === null || value === undefined || value === "") {
      return '<p class="unknown-text">' + escapeHtml(UNKNOWN_TEXT) + "</p>";
    }
    if (strong) {
      return '<p class="cost-value">' + escapeHtml(value) + "</p>";
    }
    return "<p>" + escapeHtml(value) + "</p>";
  }

  function firstCitizenNote(procNote, variantNote) {
    // Priorité à la note de la variante, sinon note générique, nettoyée.
    var cleaned = cleanCitizenNote(variantNote) || cleanCitizenNote(procNote);
    if (!cleaned) return "";
    return (
      '<div class="journey-block"><h3>Informations utiles</h3>' +
      "<p>" + escapeHtml(cleaned) + "</p></div>"
    );
  }

  function renderSources(list) {
    var items = Array.isArray(list) ? list : [];
    var html =
      '<div class="sources-block"><h3>Sources officielles</h3>' +
      "<p class=\"sources-intro\">Ces informations ont été établies à partir des sources ci-dessous.</p>";
    if (!items.length) {
      html += '<p class="unknown-text">Aucune source vérifiée pour le moment. Consultez directement l\u2019organisme compétent.</p></div>';
      return html;
    }
    html += '<ul class="sources-list">';
    items.forEach(function (s) {
      var title = (s && s.title) || "Source officielle";
      var org = (s && s.organization) || "";
      var date = formatVerifiedDate(s && s.verified_at);
      html += '<li class="source-item">';
      html += '<p class="source-title">' + escapeHtml(title) + "</p>";
      if (org) html += '<p class="source-org">' + escapeHtml(org) + "</p>";
      if (date) html += '<p class="source-date">' + escapeHtml(date) + "</p>";
      if (s && s.url) {
        html += '<a class="source-link" href="' + escapeHtml(s.url) + '" target="_blank" rel="noopener noreferrer">Consulter la source officielle</a>';
      }
      html += "</li>";
    });
    html += "</ul></div>";
    return html;
  }

  function showResult(html) {
    result.hidden = false;
    resultBody.innerHTML = html;
    if (intro) intro.hidden = true;
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderUnknown(data) {
    var msg = sanitizePublicText(data && data.message) ||
      "Nous n'avons pas reconnu votre demande. Reformulez avec, par exemple, « CNI », « passeport », « extrait de naissance », « certificat de nationalité » ou « casier judiciaire ».";
    showResult(
      '<p class="result-eyebrow neutral"><span aria-hidden="true">○</span> Demande non reconnue</p>' +
      "<h2 class=\"result-title\">Nous n'avons pas identifié de démarche</h2>" +
      '<p class="result-understand">' + escapeHtml(msg) + "</p>" +
      '<p class="result-understand">Aucune information n\u2019a été inventée : essayez l\u2019un des exemples ci-dessus.</p>'
    );
  }

  function renderNeedsClarification(data) {
    var p = data.procedure;
    var variants = (p && Array.isArray(p.variants) ? p.variants : []).filter(function (v) { return v && v.id && v.name; });
    var names = variants.map(function (v) { return v.name; }).join(", ");
    var buttons = variants.map(function (v) {
      return '<button type="button" class="variant-choice" data-variant-id="' + escapeHtml(v.id) + '">' + escapeHtml(v.name) + "</button>";
    }).join("");
    showResult(
      '<p class="result-eyebrow warn"><span aria-hidden="true">⚠</span> Précision nécessaire</p>' +
      "<h2 class=\"result-title\">" + escapeHtml(p.name) + "</h2>" +
      '<p class="result-understand">Nous avons identifié la démarche ' + escapeHtml(p.name) +
      ", mais nous avons besoin de préciser votre situation" + (names ? " (" + escapeHtml(names) + ")" : "") + ".</p>" +
      '<div class="journey-block highlight"><h3>Quelle est votre situation ?</h3>' +
      '<p>Choisissez la situation qui correspond à votre cas :</p>' +
      '<div class="variant-choices">' + (buttons || '<span class="unknown-text">Aucune variante proposée.</span>') + "</div></div>" +
      renderTrustStatus(data.verification_status || (p && p.verification_status)) +
      renderSources(p.sources)
    );
    resultBody.querySelectorAll(".variant-choice").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-variant-id");
        var q = VARIANT_QUERY_BY_ID[id];
        if (q) {
          input.value = q;
          search(q);
        } else {
          var v = variants.filter(function (x) { return x.id === id; })[0];
          input.value = (data.query || "") + " — " + ((v && v.name) || "");
          search(input.value);
        }
      });
    });
  }

  function renderMatched(data) {
    var p = data.procedure;
    var v = data.variant || null;
    var shown = v || p;
    var effectiveStatus = data.verification_status || shown.verification_status;

    var html =
      '<p class="result-eyebrow"><span aria-hidden="true">✓</span> Démarche identifiée</p>' +
      "<h2 class=\"result-title\">" + escapeHtml(p.name) + "</h2>";
    if (v && v.name) {
      html += '<p class="result-variant">' + escapeHtml(v.name) + "</p>";
    }
    html += '<p class="result-understand">D\u2019après votre message : « ' + escapeHtml(data.query) + " ».</p>";
    html += renderTrustStatus(effectiveStatus);

    html += '<div class="journey">';
    html += '<div class="journey-block highlight"><h3>Ce que vous devez préparer</h3>' + renderDocs(shown.requirements) + "</div>";
    html += '<div class="journey-block"><h3>Coût</h3>' + renderSimpleValue(shown.cost, true) + "</div>";
    html += '<div class="journey-block"><h3>Délai</h3>' + renderSimpleValue(shown.delay, false) + "</div>";
    html += '<div class="journey-block"><h3>Où effectuer la démarche</h3>' + renderSimpleValue(shown.competent_authority, false) + "</div>";
    html += firstCitizenNote(p.notes, v && v.notes);
    var sources = (v && v.sources && v.sources.length ? v.sources : p.sources);
    html += renderSources(sources);
    html += "</div>";

    showResult(html);
  }

  function render(data) {
    if (!data || data.match_status === "UNKNOWN" || !data.procedure) {
      renderUnknown(data);
      return;
    }
    if (data.match_status === "NEEDS_CLARIFICATION" || data.needs_clarification) {
      renderNeedsClarification(data);
      return;
    }
    renderMatched(data);
  }

  async function search(query) {
    showError("");
    if (!query || !query.trim()) {
      showError("Veuillez décrire votre besoin, par exemple : J'ai perdu ma CNI.");
      input.focus();
      return;
    }
    setLoading(true);
    try {
      var res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim() })
      });
      if (!res.ok) {
        var detail = "Erreur " + res.status;
        try {
          var err = await res.json();
          if (err && err.detail) detail = Array.isArray(err.detail)
            ? err.detail.map(function (d) { return d.msg || JSON.stringify(d); }).join(" ")
            : String(err.detail);
        } catch (e) { /* réponse non JSON */ }
        showError("La recherche a échoué (" + detail + "). Vérifiez votre saisie puis réessayez.");
        return;
      }
      var data = await res.json();
      render(data);
    } catch (e) {
      showError("Impossible de contacter le service. Vérifiez votre connexion puis réessayez.");
    } finally {
      setLoading(false);
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
