export const BUSINESS_TIME_ZONE = "Africa/Kinshasa" as const;

const BUSINESS_DATE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;
const EXPLICIT_INSTANT_PATTERN = /(?:Z|[+-]\d{2}:\d{2})$/;
const MAX_DAY_OFFSET = 3_660;
const MIN_BUSINESS_YEAR = 1_900;
const MAX_BUSINESS_YEAR = 2_100;

type DateStyle = "full" | "long" | "medium" | "short";

export type BusinessDateSelection =
  | { kind: "today" }
  | { kind: "tomorrow" }
  | { kind: "date"; date: string };

type BusinessDateParts = {
  year: number;
  month: number;
  day: number;
};

export function isBusinessDate(value: unknown): value is string {
  if (typeof value !== "string") {
    return false;
  }
  const parts = parseBusinessDate(value);
  if (
    parts === null ||
    parts.year < MIN_BUSINESS_YEAR ||
    parts.year > MAX_BUSINESS_YEAR
  ) {
    return false;
  }
  const roundTrip = new Date(
    Date.UTC(parts.year, parts.month - 1, parts.day, 12)
  );
  return (
    roundTrip.getUTCFullYear() === parts.year &&
    roundTrip.getUTCMonth() === parts.month - 1 &&
    roundTrip.getUTCDate() === parts.day
  );
}

export function toBusinessDate(
  value: Date | string | number
): string | null {
  const parsed = parseExplicitInstant(value);
  if (parsed === null) {
    return null;
  }
  const fields = new Intl.DateTimeFormat("en-CA", {
    day: "2-digit",
    month: "2-digit",
    timeZone: BUSINESS_TIME_ZONE,
    year: "numeric"
  })
    .formatToParts(parsed)
    .reduce<Record<string, string>>((result, part) => {
      if (part.type !== "literal") {
        result[part.type] = part.value;
      }
      return result;
    }, {});
  if (!fields.year || !fields.month || !fields.day) {
    return null;
  }
  return `${fields.year}-${fields.month}-${fields.day}`;
}

export function isInstantOnBusinessDate(
  value: string,
  businessDate: string
): boolean {
  return isBusinessDate(businessDate) && toBusinessDate(value) === businessDate;
}

export function addBusinessDays(
  businessDate: string,
  dayOffset: number
): string {
  const parts = parseBusinessDate(businessDate);
  if (
    parts === null ||
    !isBusinessDate(businessDate) ||
    !Number.isSafeInteger(dayOffset) ||
    Math.abs(dayOffset) > MAX_DAY_OFFSET
  ) {
    throw new RangeError("La date métier ou le décalage est invalide.");
  }
  const shifted = new Date(
    Date.UTC(parts.year, parts.month - 1, parts.day + dayOffset, 12)
  );
  return [
    shifted.getUTCFullYear().toString().padStart(4, "0"),
    (shifted.getUTCMonth() + 1).toString().padStart(2, "0"),
    shifted.getUTCDate().toString().padStart(2, "0")
  ].join("-");
}

export function nextSevenBusinessDates(businessToday: string): string[] {
  return Array.from({ length: 7 }, (_, index) =>
    addBusinessDays(businessToday, index)
  );
}

export function resolveBusinessDateSelection(
  selection: BusinessDateSelection,
  businessToday: string
): string {
  if (selection.kind === "today") {
    return businessToday;
  }
  if (selection.kind === "tomorrow") {
    return addBusinessDays(businessToday, 1);
  }
  if (!isBusinessDate(selection.date)) {
    throw new RangeError("La date consultée est invalide.");
  }
  return selection.date;
}

export function formatBusinessDate(
  businessDate: string,
  dateStyle: DateStyle = "long"
): string | null {
  const parts = parseBusinessDate(businessDate);
  if (parts === null || !isBusinessDate(businessDate)) {
    return null;
  }
  const calendarAnchor = new Date(
    Date.UTC(parts.year, parts.month - 1, parts.day, 12)
  );
  return new Intl.DateTimeFormat("fr-CD", {
    dateStyle,
    timeZone: "UTC"
  }).format(calendarAnchor);
}

export function formatBusinessDateTime(
  value: Date | string | number,
  dateStyle: DateStyle = "medium"
): string | null {
  const parsed = parseExplicitInstant(value);
  if (parsed === null) {
    return null;
  }
  return new Intl.DateTimeFormat("fr-CD", {
    dateStyle,
    timeStyle: "short",
    timeZone: BUSINESS_TIME_ZONE
  }).format(parsed);
}

export function formatBusinessTime(
  value: Date | string | number
): string | null {
  const parsed = parseExplicitInstant(value);
  if (parsed === null) {
    return null;
  }
  return new Intl.DateTimeFormat("fr-CD", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: BUSINESS_TIME_ZONE,
    timeZoneName: "short"
  }).format(parsed);
}

function parseBusinessDate(value: string): BusinessDateParts | null {
  const match = BUSINESS_DATE_PATTERN.exec(value);
  if (match === null) {
    return null;
  }
  return {
    year: Number(match[1]),
    month: Number(match[2]),
    day: Number(match[3])
  };
}

function parseExplicitInstant(
  value: Date | string | number
): Date | null {
  if (typeof value === "string" && !EXPLICIT_INSTANT_PATTERN.test(value)) {
    return null;
  }
  const parsed = value instanceof Date ? new Date(value.getTime()) : new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}
