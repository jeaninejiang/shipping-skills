// Turning provider failures into something a person can read.
//
// These functions used to pass the model provider's response straight
// through to the UI, so a tester saw:
//
//   Failed to generate the birth chart insight: 401 {"type":"error",
//   "error":{"type":"authentication_error","message":"invalid x-api-key"},
//   "request_id":"req_011CgCJam3B5zALTFw7NXf6k"}
//
// That tells the reader nothing they can act on, makes a temporary
// outage look like a broken app, and leaks which provider we use plus
// internal request ids. The detail belongs in the logs, where it's
// useful; the screen gets a sentence.

/// A sentence safe to show anyone, chosen by what actually went wrong so
/// "try again" isn't advice when retrying can't help.
///
/// Deliberately never says the key is invalid or missing. That's not
/// something the reader can fix, it's a detail worth not advertising,
/// and "we're having trouble" is the honest shape of it from where they
/// sit — someone has to fix it on our side either way.
export function readerFacing(err: unknown): string {
  const status = statusOf(err);

  if (status === 401 || status === 403) {
    // Our configuration, not theirs. Nothing to retry into.
    return "Readings are temporarily unavailable. We've been notified — please try again later.";
  }
  if (status === 429) {
    return "We're writing a lot of readings right now. Give it a minute and try again.";
  }
  if (status !== undefined && status >= 500) {
    return "We couldn't write your reading just now. Give it a minute and try again.";
  }
  if (isTimeout(err)) {
    return "That took longer than expected. Give it a minute and try again.";
  }
  return "We couldn't write your reading just now. Give it a minute and try again.";
}

function statusOf(err: unknown): number | undefined {
  if (typeof err !== "object" || err === null) return undefined;
  const e = err as { status?: unknown; statusCode?: unknown; message?: unknown };
  for (const v of [e.status, e.statusCode]) {
    if (typeof v === "number") return v;
  }
  // SDK errors don't always carry a status field — some only put the
  // code at the front of the message ("401 {...}").
  if (typeof e.message === "string") {
    const m = e.message.match(/^\s*(\d{3})\b/);
    if (m) return Number(m[1]);
  }
  return undefined;
}

function isTimeout(err: unknown): boolean {
  const name = (err as { name?: unknown })?.name;
  const message = (err as { message?: unknown })?.message;
  return name === "TimeoutError" || name === "AbortError" ||
    (typeof message === "string" && /timed? ?out|aborted/i.test(message));
}
