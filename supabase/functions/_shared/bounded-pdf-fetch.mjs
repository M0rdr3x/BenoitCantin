/* Fetch de PDF de référence : origine validée par l'appelant, aucune
 * redirection, limite en flux AVANT toute allocation et délai global.
 * Le contenu n'est jamais logué. Compatible Deno et tests Node locaux.
 */
export async function fetchBoundedPdf(url, maxBytes, timeoutMs=15000) {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 5 || maxBytes > 15*1024*1024)
    throw new Error('REMOTE_PDF_TOO_LARGE');
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 30000)
    throw new Error('REMOTE_PDF_TIMEOUT');
  const controller=new AbortController();
  let timeout;
  const deadline=new Promise((_,reject)=>{
    timeout=setTimeout(()=>{
      controller.abort();
      reject(new Error('REMOTE_PDF_TIMEOUT'));
    },timeoutMs);
  });
  let reader;
  try {
    const response=await Promise.race([
      fetch(url,{cache:'no-store',redirect:'error',signal:controller.signal}),
      deadline
    ]);
    if (!response.ok) throw new Error('REMOTE_PDF_FETCH_FAILED');
    const declared=response.headers.get('content-length');
    if (declared!==null && (
        !/^[0-9]+$/.test(declared) ||
        !Number.isSafeInteger(Number(declared)) ||
        Number(declared)>maxBytes))
      throw new Error('REMOTE_PDF_TOO_LARGE');
    if (!response.body || typeof response.body.getReader!=='function')
      throw new Error('REMOTE_PDF_INVALID');
    reader=response.body.getReader();
    let total=0;
    let chunks=0;
    const parts=[];
    for (;;) {
      const {done,value}=await Promise.race([reader.read(),deadline]);
      if (done) break;
      if (++chunks>4096 || !(value instanceof Uint8Array))
        throw new Error('REMOTE_PDF_INVALID');
      total+=value.byteLength;
      if (total>maxBytes) throw new Error('REMOTE_PDF_TOO_LARGE');
      parts.push(value);
    }
    if (total<5) throw new Error('REMOTE_PDF_INVALID');
    const bytes=new Uint8Array(total);
    let offset=0;
    for (const part of parts) {
      bytes.set(part,offset);
      offset+=part.byteLength;
    }
    if (String.fromCharCode(...bytes.subarray(0,5))!=='%PDF-')
      throw new Error('REMOTE_PDF_NOT_PDF');
    return bytes;
  } catch(error) {
    controller.abort();
    if (reader) {
      try {Promise.resolve(reader.cancel()).catch(()=>{});} catch {}
    }
    throw error;
  } finally {
    clearTimeout(timeout);
    if (reader) reader.releaseLock();
  }
}
