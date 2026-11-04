/* Projet NOVA — simulation de navigation strictement locale.
 * AUCUN vote, aucune connexion, aucun stockage, aucun partage des réponses.
 * Les formulations sont présentes dans le HTML; rien n'est chargé en réseau.
 */
(() => {
  "use strict";
  const OPINION = [
    ["-3","Tout à fait en désaccord"],["-2","En désaccord"],
    ["-1","Plutôt en désaccord"],["0","Ni d’accord ni en désaccord"],
    ["1","Plutôt d’accord"],["2","D’accord"],["3","Tout à fait d’accord"],
    ["skip","Sans opinion / passer"]
  ];
  const CONSULTATION = [
    ["pour","Pour"],["contre","Contre"],["sans_opinion","Sans opinion"]
  ];
  function init() {
    const root = document.getElementById("draft-root");
    if(!root) return;
    const kind = root.dataset.kind;
    const expected = kind === "opinion" ? 64 : kind === "consultation" ? 40 : 0;
    const options = kind === "opinion" ? OPINION : CONSULTATION;
    const source = document.getElementById("draft-source");
    const player = document.getElementById("draft-player");
    const status = document.getElementById("draft-status");
    const heading = document.getElementById("draft-step-heading");
    const legend = document.getElementById("draft-question");
    const choices = document.getElementById("draft-choices");
    const progress = document.getElementById("draft-progress");
    const previous = document.getElementById("draft-prev");
    const next = document.getElementById("draft-next");
    const reset = document.getElementById("draft-reset");
    const fieldset = document.getElementById("draft-fieldset");
    const summary = document.getElementById("draft-summary");
    const required = [source,player,status,heading,legend,choices,progress,
      previous,next,reset,fieldset,summary];
    if(!expected || required.some(node=>!node)) return;
    const rows = Array.from(source.querySelectorAll("li[data-id]"));
    const questions = rows.map(row=>({
      id: row.dataset.id,
      text: row.textContent.trim()
    }));
    if(questions.length !== expected || questions.some((q,i)=>
       q.id !== "q"+String(i+1).padStart(2,"0") || q.text.length < 15)) {
      status.textContent = "Questionnaire incomplet. Le parcours d’essai est indisponible.";
      return; // La liste des questions reste visible, sans formulaire.
    }

    // État éphémère, uniquement dans la mémoire de cette page.
    // Ne jamais ajouter d'enregistrement persistant ni d'envoi HTTP.
    const answers = new Map();
    let index = 0;
    const focusHeading = () => {
      if(typeof heading.focus === "function") heading.focus({preventScroll:true});
    };
    function render(focus=false) {
      const finished = index === questions.length;
      progress.max = questions.length;
      progress.value = finished ? questions.length : index+1;
      heading.textContent = finished
        ? "Parcours d’essai terminé"
        : "Question "+(index+1)+" sur "+questions.length;
      fieldset.hidden = finished;
      summary.hidden = !finished;
      previous.disabled = index === 0;
      next.hidden = finished;
      if(finished) {
        summary.textContent = "Vous avez parcouru les "+questions.length+
          " propositions. Aucune réponse n’a été envoyée, enregistrée ou "+
          "comptabilisée. Cette page n’est pas un sondage ouvert et ne produit "+
          "aucun résultat électoral. Vous pouvez revenir aux questions ou "+
          "recommencer. Le rechargement de la page efface les choix d’essai.";
        status.textContent = "Fin de la démonstration locale, sans soumission.";
      } else {
        const question = questions[index];
        legend.textContent = question.text;
        choices.replaceChildren();
        for(const [value,caption] of options) {
          const label = document.createElement("label");
          label.className = "draft-choice";
          const input = document.createElement("input");
          input.type = "radio";
          input.name = "draft-choice";
          input.value = value;
          input.checked = answers.get(question.id) === value;
          input.addEventListener("change",() => {
            if(input.checked && options.some(([allowed])=>allowed===value)) {
              answers.set(question.id,value);
              next.disabled = false;
              status.textContent = "Choix temporaire conservé uniquement dans cette page.";
            }
          });
          const text = document.createElement("span");
          text.textContent = caption;
          label.append(input,text);
          choices.append(label);
        }
        next.disabled = !answers.has(question.id);
        next.textContent = index === questions.length-1
          ? "Terminer l’essai — aucun vote envoyé"
          : "Question suivante";
        status.textContent = "Démonstration locale : réponses non transmises.";
      }
      if(focus) focusHeading();
    }
    next.addEventListener("click",() => {
      if(index >= questions.length || !answers.has(questions[index].id)) return;
      index++;
      render(true);
    });
    previous.addEventListener("click",() => {
      if(index === 0) return;
      index--;
      render(true);
    });
    reset.addEventListener("click",() => {
      answers.clear();
      index = 0;
      render(true);
    });
    source.hidden = true;
    player.hidden = false;
    render(false);
  }
  document.addEventListener("DOMContentLoaded",init,{once:true});
})();
