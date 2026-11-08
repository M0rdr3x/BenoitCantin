/* Actions publiques explicites sans gestionnaire HTML inline.
 * Les seules commandes autorisées sont celles définies dans ce fichier.
 */
document.addEventListener('click', (event) => {
  if (!(event.target instanceof Element)) return;
  const button = event.target.closest('button[data-static-action]');
  if (!(button instanceof HTMLButtonElement) || button.disabled) return;
  const action = button.dataset.staticAction;
  if (action === 'reload') {
    window.location.reload();
  } else if (action === 'print') {
    window.print();
  }
});
