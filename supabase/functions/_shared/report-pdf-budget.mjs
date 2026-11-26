// Shared server quota: only a strict success may start expensive PDF work.
export async function consumeReportBudget(service, authenticated, timeoutMs = 1500) {
  if (typeof authenticated !== 'boolean' || !Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 1500) return 'unavailable';
  const controller = new AbortController();
  let timer;
  try {
    const timeout = new Promise(resolve => {
      timer = setTimeout(() => { controller.abort(); resolve(null); }, timeoutMs);
    });
    const request = Promise.resolve().then(() => service.rpc('consume_report_pdf_budget', {
      p_authenticated: authenticated
    }).abortSignal(controller.signal));
    const result = await Promise.race([request, timeout]);
    if (!result || result.error || typeof result.data !== 'boolean') return 'unavailable';
    return result.data === true ? 'allowed' : 'limited';
  } catch {
    return 'unavailable';
  } finally {
    clearTimeout(timer);
  }
}
