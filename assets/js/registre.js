(() => {
  const form = document.querySelector('#questionnaire');
  if (!form) return;

  const steps = [...form.querySelectorAll('[data-step]')];
  const progressBar = document.querySelector('[data-progress-bar]');
  const progressLabel = document.querySelector('[data-progress-label]');
  const progressPercent = document.querySelector('[data-progress-percent]');
  const errorSummary = document.querySelector('[data-error-summary]');
  const minorSection = form.querySelector('[data-minor-section]');
  const adultMessage = form.querySelector('[data-adult-message]');
  const jsonField = form.querySelector('[data-json-field]');
  const draftToggle = document.querySelector('[data-enable-draft]');
  const clearDraft = document.querySelector('[data-clear-draft]');
  const draftStatusNodes = [...document.querySelectorAll('[data-draft-status]')];
  const storageKey = 'registre-consciences-draft-v1';
  let current = 0;
  let saveTimer = null;

  const setDraftStatus = (text) => draftStatusNodes.forEach((node) => { node.textContent = text; });

  function showStep(index, focus = true) {
    current = Math.max(0, Math.min(index, steps.length - 1));
    steps.forEach((step, i) => step.classList.toggle('active', i === current));
    const percent = Math.round(((current + 1) / steps.length) * 100);
    progressBar.style.width = `${percent}%`;
    progressLabel.textContent = `Étape ${current + 1} sur ${steps.length}`;
    progressPercent.textContent = `${percent} %`;
    errorSummary.classList.remove('visible');
    if (focus) {
      steps[current].querySelector('.form-step-header h2')?.focus?.({preventScroll: true});
      window.scrollTo({ top: document.querySelector('.progress-wrap').offsetTop - 68, behavior: 'smooth' });
    }
  }

  function getAgeGroup() {
    return form.querySelector('input[name="groupe_age"]:checked')?.value || '';
  }

  function updateMinorSection() {
    const group = getAgeGroup();
    const minor = group && !group.startsWith('J’ai 18 ans');
    minorSection?.classList.toggle('hidden', !minor);
    adultMessage?.classList.toggle('hidden', minor);
    minorSection?.querySelectorAll('input').forEach((input) => {
      if (['parent_nom','parent_lien','parent_courriel','parent_signature','parent_date'].includes(input.name)) {
        input.required = minor;
      }
    });
    return minor;
  }

  function validateStep(step) {
    errorSummary.classList.remove('visible');
    const required = [...step.querySelectorAll('[required]')].filter((node) => !node.closest('.hidden'));
    for (const field of required) {
      if (!field.checkValidity()) {
        errorSummary.classList.add('visible');
        errorSummary.textContent = 'Veuillez compléter les champs obligatoires de cette étape avant de continuer.';
        field.reportValidity();
        field.focus({preventScroll: false});
        return false;
      }
    }

    if (step.dataset.step === '1') {
      const originality = [...form.querySelectorAll('input[name="originalite"]')];
      if (originality.some((item) => !item.checked)) {
        errorSummary.classList.add('visible');
        errorSummary.textContent = 'Veuillez confirmer toutes les déclarations d’originalité avant de continuer.';
        originality.find((item) => !item.checked)?.focus();
        return false;
      }
    }

    if (step.dataset.step === String(steps.length)) {
      const consents = [...form.querySelectorAll('input[name="consentements"]')];
      if (consents.some((item) => !item.checked)) {
        errorSummary.classList.add('visible');
        errorSummary.textContent = 'Toutes les déclarations de consentement doivent être acceptées pour transmettre la participation.';
        consents.find((item) => !item.checked)?.focus();
        return false;
      }
      if (updateMinorSection()) {
        const parentConsents = [...form.querySelectorAll('input[name="parent_consentements"]')];
        if (parentConsents.some((item) => !item.checked)) {
          errorSummary.classList.add('visible');
          errorSummary.textContent = 'Le parent ou tuteur doit accepter toutes les déclarations d’autorisation parentale.';
          parentConsents.find((item) => !item.checked)?.focus();
          return false;
        }
      }
    }
    return true;
  }

  function serializeForm() {
    const data = {};
    const fd = new FormData(form);
    for (const [key, value] of fd.entries()) {
      if (value instanceof File) {
        if (value.name) data[key] = {name: value.name, type: value.type, size: value.size};
        continue;
      }
      if (['form-name', 'bot-field', 'reponses_json'].includes(key)) continue;
      if (Object.prototype.hasOwnProperty.call(data, key)) {
        data[key] = Array.isArray(data[key]) ? [...data[key], value] : [data[key], value];
      } else {
        data[key] = value;
      }
    }
    return data;
  }

  function saveDraft() {
    if (!draftToggle?.checked) return;
    const payload = {savedAt: new Date().toISOString(), step: current, data: serializeForm()};
    try {
      localStorage.setItem(storageKey, JSON.stringify(payload));
      setDraftStatus(`Brouillon enregistré à ${new Date().toLocaleTimeString('fr-CA', {hour:'2-digit', minute:'2-digit'})}`);
    } catch {
      setDraftStatus('Le navigateur a refusé la sauvegarde locale.');
    }
  }

  function queueSave() {
    if (!draftToggle?.checked) return;
    clearTimeout(saveTimer);
    setDraftStatus('Enregistrement du brouillon…');
    saveTimer = setTimeout(saveDraft, 450);
  }

  function restoreDraft(payload) {
    if (!payload?.data) return;
    for (const [name, value] of Object.entries(payload.data)) {
      const nodes = [...form.querySelectorAll(`[name="${CSS.escape(name)}"]`)];
      if (!nodes.length) continue;
      const values = Array.isArray(value) ? value : [value];
      nodes.forEach((node) => {
        if (node.type === 'file') return;
        if (node.type === 'checkbox' || node.type === 'radio') {
          node.checked = values.includes(node.value);
        } else if (typeof value === 'string') {
          node.value = value;
        }
      });
    }
    draftToggle.checked = true;
    updateMinorSection();
    showStep(Number.isInteger(payload.step) ? payload.step : 0, false);
    const date = payload.savedAt ? new Date(payload.savedAt) : null;
    setDraftStatus(date && !Number.isNaN(date.valueOf()) ? `Brouillon restauré du ${date.toLocaleString('fr-CA')}` : 'Brouillon restauré');
  }

  steps.forEach((step) => {
    step.querySelector('[data-next]')?.addEventListener('click', () => {
      if (validateStep(step)) showStep(current + 1);
    });
    step.querySelector('[data-prev]')?.addEventListener('click', () => showStep(current - 1));
  });

  form.addEventListener('change', (event) => {
    if (event.target.name === 'groupe_age') updateMinorSection();
    queueSave();
  });
  form.addEventListener('input', queueSave);

  draftToggle?.addEventListener('change', () => {
    if (draftToggle.checked) {
      setDraftStatus('Brouillon local activé');
      saveDraft();
    } else {
      localStorage.removeItem(storageKey);
      setDraftStatus('Brouillon local désactivé');
    }
  });

  clearDraft?.addEventListener('click', () => {
    if (!confirm('Effacer le brouillon enregistré dans ce navigateur? Les réponses déjà inscrites dans la page resteront visibles jusqu’à ce que vous les effaciez ou rechargiez la page.')) return;
    localStorage.removeItem(storageKey);
    if (draftToggle) draftToggle.checked = false;
    setDraftStatus('Brouillon local effacé');
  });

  form.addEventListener('submit', (event) => {
    updateMinorSection();
    for (let i = 0; i < steps.length; i += 1) {
      if (!validateStep(steps[i])) {
        event.preventDefault();
        showStep(i, false);
        window.scrollTo({ top: document.querySelector('.progress-wrap').offsetTop - 68, behavior: 'smooth' });
        return;
      }
    }
    jsonField.value = JSON.stringify(serializeForm());
    localStorage.removeItem(storageKey);
  });

  updateMinorSection();
  showStep(0, false);

  try {
    const saved = JSON.parse(localStorage.getItem(storageKey));
    if (saved?.data && confirm('Un brouillon du Registre des Consciences existe dans ce navigateur. Voulez-vous le restaurer?')) {
      restoreDraft(saved);
    } else if (saved) {
      localStorage.removeItem(storageKey);
    }
  } catch {
    localStorage.removeItem(storageKey);
  }
})();
