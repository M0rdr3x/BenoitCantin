// Local admission control for expensive PDF work. No queue, identity or shared state.
export function createPdfAdmissionGate(maxConcurrent) {
  if (!Number.isSafeInteger(maxConcurrent) || maxConcurrent < 1 || maxConcurrent > 8) {
    throw new TypeError('INVALID_PDF_ADMISSION_LIMIT');
  }
  let inFlight = 0;
  return function acquire() {
    if (inFlight >= maxConcurrent) return null;
    inFlight += 1;
    let released = false;
    return function release() {
      if (released) return;
      released = true;
      inFlight -= 1;
    };
  };
}
