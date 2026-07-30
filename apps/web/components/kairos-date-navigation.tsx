"use client";

import { useEffect, useMemo, useState } from "react";
import {
  addBusinessDays,
  BUSINESS_TIME_ZONE,
  type BusinessDateSelection,
  formatBusinessDate,
  formatBusinessTime,
  nextSevenBusinessDates,
  toBusinessDate
} from "../lib/business-time";

export function KairosDateNavigation({
  businessToday,
  consultedDate,
  onBusinessTodayChange,
  onSelectionChange,
  selection
}: {
  businessToday: string | null;
  consultedDate: string | null;
  onBusinessTodayChange: (date: string) => void;
  onSelectionChange: (selection: BusinessDateSelection) => void;
  selection: BusinessDateSelection;
}) {
  const [clock, setClock] = useState<Date | null>(null);
  const [weekOpen, setWeekOpen] = useState(selection.kind === "date");

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const currentBusinessDate = toBusinessDate(now);
      setClock(now);
      if (currentBusinessDate !== null) {
        onBusinessTodayChange(currentBusinessDate);
      }
    };
    updateClock();
    const interval = window.setInterval(updateClock, 1_000);
    return () => window.clearInterval(interval);
  }, [onBusinessTodayChange]);

  const tomorrow =
    businessToday === null ? null : addBusinessDays(businessToday, 1);
  const weekDates = useMemo(
    () =>
      businessToday === null ? [] : nextSevenBusinessDates(businessToday),
    [businessToday]
  );
  const selectedDate =
    selection.kind === "today"
      ? businessToday
      : selection.kind === "tomorrow"
        ? tomorrow
        : selection.date;
  const todaySelected =
    selection.kind === "today" ||
    (selection.kind === "date" && selection.date === businessToday);
  const tomorrowSelected =
    selection.kind === "tomorrow" ||
    (selection.kind === "date" && selection.date === tomorrow);
  const weekDateSelected =
    selection.kind === "date" && weekDates.includes(selection.date);

  return (
    <section className="kairos-date-navigation" aria-label="Navigation par date">
      <div className="kairos-date-navigation-main">
        <div className="kairos-date-actions">
          <button
            aria-pressed={todaySelected}
            className={todaySelected ? "is-selected" : ""}
            onClick={() => {
              setWeekOpen(false);
              if (selection.kind !== "today") {
                onSelectionChange({ kind: "today" });
              }
            }}
            type="button"
          >
            Aujourd’hui
          </button>
          <button
            aria-pressed={tomorrowSelected}
            className={tomorrowSelected ? "is-selected" : ""}
            disabled={tomorrow === null}
            onClick={() => {
              setWeekOpen(false);
              if (selection.kind !== "tomorrow") {
                onSelectionChange({ kind: "tomorrow" });
              }
            }}
            type="button"
          >
            Demain
          </button>
          <button
            aria-expanded={weekOpen}
            aria-pressed={weekDateSelected}
            className={weekDateSelected ? "is-selected" : ""}
            disabled={businessToday === null}
            onClick={() => setWeekOpen((current) => !current)}
            type="button"
          >
            Prochains 7 jours
          </button>
        </div>
        <div className="kairos-date-context" aria-live="polite">
          <span>
            Date consultée
            <strong>
              {consultedDate === null
                ? "Chargement…"
                : (formatBusinessDate(consultedDate) ?? consultedDate)}
            </strong>
          </span>
          <span>
            Heure locale {BUSINESS_TIME_ZONE}
            <strong>
              {clock === null
                ? "Synchronisation…"
                : (formatBusinessTime(clock) ?? "Indisponible")}
            </strong>
          </span>
        </div>
      </div>
      {weekOpen && weekDates.length > 0 && (
        <div className="kairos-week-days" aria-label="Dates des sept prochains jours">
          {weekDates.map((date, index) => (
            <button
              aria-pressed={selectedDate === date}
              className={selectedDate === date ? "is-selected" : ""}
              key={date}
              onClick={() => {
                if (selection.kind !== "date" || selection.date !== date) {
                  onSelectionChange({ kind: "date", date });
                }
              }}
              type="button"
            >
              <span>
                {index === 0 ? "Aujourd’hui" : index === 1 ? "Demain" : `J+${index}`}
              </span>
              <strong>{formatBusinessDate(date, "medium") ?? date}</strong>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
