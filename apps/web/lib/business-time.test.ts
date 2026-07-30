import assert from "node:assert/strict";
import test from "node:test";

import {
  addBusinessDays,
  BUSINESS_TIME_ZONE,
  formatBusinessDate,
  isBusinessDate,
  isInstantOnBusinessDate,
  nextSevenBusinessDates,
  resolveBusinessDateSelection,
  toBusinessDate
} from "./business-time.ts";

test("centralizes the Kinshasa business timezone", () => {
  assert.equal(BUSINESS_TIME_ZONE, "Africa/Kinshasa");
});

test("changes business day exactly at midnight in Kinshasa", () => {
  assert.equal(toBusinessDate("2026-07-30T22:59:59Z"), "2026-07-30");
  assert.equal(toBusinessDate("2026-07-30T23:00:00Z"), "2026-07-31");
  assert.equal(
    toBusinessDate("2026-07-31T00:00:00+01:00"),
    "2026-07-31"
  );
});

test("rejects naive or impossible dates and instants", () => {
  assert.equal(isBusinessDate("2026-07-31"), true);
  assert.equal(isBusinessDate("2026-02-29"), false);
  assert.equal(isBusinessDate("2026-7-31"), false);
  assert.equal(isBusinessDate("0001-01-01"), false);
  assert.equal(isBusinessDate("9999-12-31"), false);
  assert.equal(toBusinessDate("2026-07-31T00:00:00"), null);
  assert.equal(toBusinessDate("not-an-instant"), null);
});

test("adds civil business days without depending on the host timezone", () => {
  assert.equal(addBusinessDays("2026-07-31", 1), "2026-08-01");
  assert.equal(addBusinessDays("2028-02-28", 1), "2028-02-29");
  assert.deepEqual(nextSevenBusinessDates("2026-07-30"), [
    "2026-07-30",
    "2026-07-31",
    "2026-08-01",
    "2026-08-02",
    "2026-08-03",
    "2026-08-04",
    "2026-08-05"
  ]);
});

test("resolves today, tomorrow and one selected day independently", () => {
  assert.equal(
    resolveBusinessDateSelection({ kind: "today" }, "2026-07-30"),
    "2026-07-30"
  );
  assert.equal(
    resolveBusinessDateSelection({ kind: "tomorrow" }, "2026-07-30"),
    "2026-07-31"
  );
  assert.equal(
    resolveBusinessDateSelection(
      { kind: "date", date: "2026-08-04" },
      "2026-07-30"
    ),
    "2026-08-04"
  );
});

test("keeps a kickoff in exactly one Kinshasa business day", () => {
  assert.equal(
    isInstantOnBusinessDate("2026-07-30T22:59:59Z", "2026-07-30"),
    true
  );
  assert.equal(
    isInstantOnBusinessDate("2026-07-30T23:00:00Z", "2026-07-30"),
    false
  );
  assert.equal(
    isInstantOnBusinessDate("2026-07-30T23:00:00Z", "2026-07-31"),
    true
  );
  assert.match(formatBusinessDate("2026-07-31") ?? "", /31/);
});
