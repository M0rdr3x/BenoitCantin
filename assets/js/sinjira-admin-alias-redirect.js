// Redirections administrateur historiques sans JavaScript inline.
// Le chemin cible vient exclusivement des attributs figés du site.
(() => {
  const targetPath = document.currentScript?.dataset?.adminRedirectTarget || '';
  if (!/^\/admin\/[A-Za-z0-9._/-]*$/.test(targetPath) || targetPath.includes('..')) return;
  const target = new URL(targetPath, window.location.origin);
  if (target.origin !== window.location.origin) return;
  target.search = window.location.search;
  target.hash = window.location.hash;
  window.location.replace(target.href);
})();
