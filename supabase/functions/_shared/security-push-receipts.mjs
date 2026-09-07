export const SECURITY_PUSH_RECEIPT_MAX_BATCH = 1000;

function normalizeReceiptId(value) {
  const id = typeof value === 'string' ? value.trim() : '';
  if (id.length < 8 || id.length > 200) {
    throw new TypeError('INVALID_EXPO_RECEIPT_ID');
  }
  return id;
}

function endpointId(value) {
  return typeof value === 'string' ? value.trim() : '';
}

export function buildSecurityPushReceiptRequest(receiptIds) {
  if (!Array.isArray(receiptIds) || receiptIds.length < 1 || receiptIds.length > SECURITY_PUSH_RECEIPT_MAX_BATCH) {
    throw new TypeError('INVALID_EXPO_RECEIPT_BATCH');
  }
  const ids = receiptIds.map(normalizeReceiptId);
  if (new Set(ids).size !== ids.length) {
    throw new TypeError('DUPLICATE_EXPO_RECEIPT_ID');
  }
  return { ids };
}

export function resolveSecurityPushTickets(tickets, endpointRows) {
  if (!Array.isArray(tickets) || !Array.isArray(endpointRows)) {
    throw new TypeError('INVALID_PUSH_TICKET_BATCH');
  }
  const receiptRows = [];
  const invalidEndpointIds = [];

  tickets.forEach((ticket, index) => {
    const currentEndpointId = endpointId(endpointRows[index]?.id);
    if (!currentEndpointId) return;

    if (ticket?.status === 'error' && ticket?.details?.error === 'DeviceNotRegistered') {
      invalidEndpointIds.push(currentEndpointId);
      return;
    }
    if (ticket?.status !== 'ok') return;

    try {
      receiptRows.push({
        expo_receipt_id: normalizeReceiptId(ticket?.id),
        endpoint_id: currentEndpointId,
      });
    } catch {
      // Un ticket Expo sans ID de reçu valide n'est pas persisté.
    }
  });

  return {
    receiptRows,
    invalidEndpointIds: Array.from(new Set(invalidEndpointIds)),
  };
}

export function classifySecurityPushReceipt(receipt) {
  if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)) return 'invalid';
  if (receipt.status === 'ok') return 'provider_accepted';
  if (receipt.status !== 'error') return 'invalid';
  if (receipt.details?.error === 'DeviceNotRegistered') return 'device_not_registered';
  return 'provider_error';
}

export function resolveSecurityPushReceipts(pendingRows, receiptData) {
  if (!Array.isArray(pendingRows)) throw new TypeError('INVALID_PENDING_RECEIPTS');
  const data = receiptData && typeof receiptData === 'object' && !Array.isArray(receiptData) ? receiptData : {};
  const handledReceiptIds = [];
  const invalidEndpointIds = [];

  for (const row of pendingRows) {
    const receiptId = normalizeReceiptId(row?.expo_receipt_id);
    const currentEndpointId = endpointId(row?.endpoint_id);
    if (!currentEndpointId) throw new TypeError('INVALID_PUSH_ENDPOINT_ID');
    if (!Object.hasOwn(data, receiptId)) continue;

    handledReceiptIds.push(receiptId);
    if (classifySecurityPushReceipt(data[receiptId]) === 'device_not_registered') {
      invalidEndpointIds.push(currentEndpointId);
    }
  }

  return {
    handledReceiptIds,
    invalidEndpointIds: Array.from(new Set(invalidEndpointIds)),
  };
}
