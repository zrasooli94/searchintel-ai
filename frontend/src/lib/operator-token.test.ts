import assert from "node:assert/strict";
import test from "node:test";

import {
  createOperatorToken,
  passphrasesMatch,
  verifyOperatorToken,
} from "./operator-token.ts";


test("operator token verifies only with the server secret", () => {
  const token = createOperatorToken("private-secret", 100);
  assert.equal(verifyOperatorToken(token, "private-secret", 101), true);
  assert.equal(verifyOperatorToken(token, "wrong-secret", 101), false);
});


test("expired operator token is rejected", () => {
  const token = createOperatorToken("private-secret", 100);
  assert.equal(verifyOperatorToken(token, "private-secret", 100000), false);
});


test("operator passphrase comparison does not accept mismatches", () => {
  assert.equal(passphrasesMatch("correct", "correct"), true);
  assert.equal(passphrasesMatch("incorrect", "correct"), false);
});
