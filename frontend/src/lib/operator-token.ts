import {
  createHmac,
  timingSafeEqual,
} from "node:crypto";


export const OPERATOR_SESSION_SECONDS = 8 * 60 * 60;


function signature(
  expiresAt: number,
  secret: string,
): string {
  return createHmac("sha256", secret)
    .update(String(expiresAt))
    .digest("hex");
}


export function createOperatorToken(
  secret: string,
  nowSeconds = Math.floor(Date.now() / 1000),
): string {
  const expiresAt = nowSeconds + OPERATOR_SESSION_SECONDS;
  return `${expiresAt}.${signature(expiresAt, secret)}`;
}


export function verifyOperatorToken(
  token: string | undefined,
  secret: string | undefined,
  nowSeconds = Math.floor(Date.now() / 1000),
): boolean {
  if (!token || !secret) {
    return false;
  }
  const [rawExpiry, supplied, extra] = token.split(".");
  const expiresAt = Number(rawExpiry);
  if (
    extra !== undefined
    || !Number.isSafeInteger(expiresAt)
    || expiresAt <= nowSeconds
    || !supplied
  ) {
    return false;
  }
  const expected = signature(expiresAt, secret);
  const suppliedBuffer = Buffer.from(supplied, "utf8");
  const expectedBuffer = Buffer.from(expected, "utf8");
  return (
    suppliedBuffer.length === expectedBuffer.length
    && timingSafeEqual(suppliedBuffer, expectedBuffer)
  );
}


export function passphrasesMatch(
  supplied: string,
  expected: string,
): boolean {
  const suppliedDigest = createHmac("sha256", "searchintel-operator")
    .update(supplied)
    .digest();
  const expectedDigest = createHmac("sha256", "searchintel-operator")
    .update(expected)
    .digest();
  return timingSafeEqual(suppliedDigest, expectedDigest);
}
