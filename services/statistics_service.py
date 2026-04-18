"""
Statistics Service — session comparison business logic.
No Flask, no SQL. Calls ApplicantService and SessionService.
"""

from datetime import date

from services.applicant_service import ApplicantService
from services.session_service import SessionService
from services.status_service import StatusService

_applicant_svc = ApplicantService()
_session_svc = SessionService()
_status_svc = StatusService()


class StatisticsService:

    # ── Public API ──────────────────────────────────────────────────────────

    def compare_sessions(
        self, session_a_id: int, session_b_id: int, cutoff_month: int | None = None
    ) -> dict:
        """Return computed stats for two sessions, optionally filtered by cutoff_month (1–12)."""
        status_names = self._active_status_names()
        session_a = _session_svc.get_session_by_id(session_a_id)
        session_b = _session_svc.get_session_by_id(session_b_id)
        return {
            "session_a": self._session_payload(session_a_id, session_a, status_names, cutoff_month),
            "session_b": self._session_payload(session_b_id, session_b, status_names, cutoff_month),
            "cutoff_month": cutoff_month,
        }

    def compare_sessions_timeline(self, session_a_id: int, session_b_id: int) -> dict:
        """Return month-by-month cumulative stats for two sessions (submitted by 1st of each month)."""
        status_names = self._active_status_names()
        session_a = _session_svc.get_session_by_id(session_a_id)
        session_b = _session_svc.get_session_by_id(session_b_id)
        a_all = _applicant_svc.get_all(session_id=session_a_id)
        b_all = _applicant_svc.get_all(session_id=session_b_id)
        today = date.today()
        a_year = session_a.get("year")
        b_year = session_b.get("year")
        months = []
        for m in range(1, 13):
            a_cutoff = date(a_year, m, 1) if a_year else None
            b_cutoff = date(b_year, m, 1) if b_year else None
            if (a_cutoff is None or a_cutoff > today) and (b_cutoff is None or b_cutoff > today):
                break
            months.append({
                "month": m,
                "a_stats": self._stats_from_applicants(self._filter_by_cutoff(a_all, a_cutoff), status_names),
                "b_stats": self._stats_from_applicants(self._filter_by_cutoff(b_all, b_cutoff), status_names),
            })
        return {
            "session_a": {"id": session_a_id, "name": session_a.get("name", f"Session {session_a_id}")},
            "session_b": {"id": session_b_id, "name": session_b.get("name", f"Session {session_b_id}")},
            "months": months,
        }

    def compare_range(self, session_id: int, year_from: int, year_to: int) -> dict:
        """Return current session stats vs averaged stats of sessions in a year range."""
        if year_from > year_to:
            raise ValueError("year_from must be less than or equal to year_to")

        status_names = self._active_status_names()
        current = _session_svc.get_session_by_id(session_id)
        past_sessions = self._sessions_in_range(
            session_id, current.get("campus", ""), year_from, year_to
        )

        past_stats = [
            self._stats_from_applicants(
                _applicant_svc.get_all(session_id=s["id"]), status_names
            )
            for s in past_sessions
        ]
        n = len(past_sessions)
        return {
            "session": self._session_payload(session_id, current, status_names),
            "range": {
                "label": self._range_label(n, year_from, year_to),
                "session_count": n,
                "session_names": [s.get("name", "") for s in past_sessions],
                "stats": self._average_stats(past_stats) if past_stats else None,
            },
        }

    # ── Private helpers ──────────────────────────────────────────────────────

    def _active_status_names(self) -> list[str]:
        return [s["status_name"] for s in _status_svc.get_active_statuses()]

    def _session_payload(
        self, session_id: int, session: dict, status_names: list, cutoff_month: int | None = None
    ) -> dict:
        applicants = _applicant_svc.get_all(session_id=session_id)
        if cutoff_month is not None:
            year = session.get("year")
            applicants = self._filter_by_cutoff(applicants, date(year, cutoff_month, 1) if year else None)
        return {
            "id": session_id,
            "name": session.get("name", f"Session {session_id}"),
            "stats": self._stats_from_applicants(applicants, status_names),
        }

    @staticmethod
    def _filter_by_cutoff(applicants: list, cutoff: date | None) -> list:
        if cutoff is None:
            return applicants
        result = []
        for a in applicants:
            sd = a.get("submit_date")
            if not sd:
                continue
            sd_date = sd.date() if hasattr(sd, "date") else sd
            if sd_date <= cutoff:
                result.append(a)
        return result

    def _sessions_in_range(
        self, current_id: int, campus: str, year_from: int, year_to: int
    ) -> list:
        all_by_campus = _session_svc.get_all_sessions(include_archived=True)
        campus_sessions = all_by_campus.get(campus, [])  # already year DESC
        return [
            s for s in campus_sessions
            if s["id"] != current_id and s.get("year") is not None
            and year_from <= s["year"] <= year_to
        ]

    @staticmethod
    def _range_label(n: int, year_from: int, year_to: int) -> str:
        if n == 0:
            return f"No sessions found ({year_from}–{year_to})"
        return f"Avg. {year_from}–{year_to} ({n} session{'s' if n != 1 else ''})"

    # ── Stats computation ────────────────────────────────────────────────────

    def _stats_from_applicants(self, applicants: list, status_names: list) -> dict:
        total = len(applicants)
        return {
            "total": total,
            **self._submission_counts(applicants, total),
            **self._residency_counts(applicants, total),
            **self._gender_counts(applicants, total),
            "review_status_counts": self._review_status_counts(applicants, status_names),
            "top_countries": self._top_countries(applicants),
            **self._rating_stats(applicants, total),
        }

    def _submission_counts(self, applicants: list, total: int) -> dict:
        submitted = sum(1 for a in applicants if self._is_submitted(a.get("status", "")))
        return {"submitted": submitted, "unsubmitted": total - submitted}

    def _residency_counts(self, applicants: list, total: int) -> dict:
        domestic = sum(
            1 for a in applicants
            if a.get("canadian") == "Yes" or a.get("visa") == "PERM"
        )
        return {"domestic": domestic, "international": total - domestic}

    def _gender_counts(self, applicants: list, total: int) -> dict:
        male = sum(1 for a in applicants if a.get("gender") == "Male")
        female = sum(1 for a in applicants if a.get("gender") == "Female")
        return {"male": male, "female": female, "gender_not_specified": total - male - female}

    @staticmethod
    def _review_status_counts(applicants: list, status_names: list) -> dict:
        counts = {s: 0 for s in status_names}
        for a in applicants:
            s = a.get("review_status") or "Not Reviewed"
            if s in counts:
                counts[s] += 1
        return counts

    @staticmethod
    def _top_countries(applicants: list, top_n: int = 10) -> list:
        country_counts: dict = {}
        for a in applicants:
            c = a.get("citizenship_country") or "Not Specified"
            country_counts[c] = country_counts.get(c, 0) + 1
        return [
            {"country": c, "count": n}
            for c, n in sorted(country_counts.items(), key=lambda x: -x[1])[:top_n]
        ]

    @staticmethod
    def _rating_stats(applicants: list, total: int) -> dict:
        ratings = []
        for a in applicants:
            try:
                r = a.get("overall_rating")
                if r is not None:
                    ratings.append(float(r))
            except (ValueError, TypeError):
                pass
        rated_count = len(ratings)
        return {
            "avg_rating": round(sum(ratings) / rated_count, 2) if rated_count else 0,
            "rated_count": rated_count,
            "rated_percent": round(rated_count / total * 100, 1) if total else 0,
        }

    # ── Averaging ────────────────────────────────────────────────────────────

    def _average_stats(self, stats_list: list) -> dict:
        n = len(stats_list)
        scalar_keys = [
            "total", "submitted", "unsubmitted", "domestic", "international",
            "male", "female", "gender_not_specified", "rated_count",
        ]
        float_keys = ["avg_rating", "rated_percent"]
        return {
            **{k: round(sum(s[k] for s in stats_list) / n) for k in scalar_keys},
            **{k: round(sum(s[k] for s in stats_list) / n, 2) for k in float_keys},
            "review_status_counts": self._average_review_counts(stats_list, n),
            "top_countries": self._average_countries(stats_list, n),
        }

    @staticmethod
    def _average_review_counts(stats_list: list, n: int) -> dict:
        all_keys: set = set()
        for s in stats_list:
            all_keys.update(s["review_status_counts"].keys())
        return {
            k: round(sum(s["review_status_counts"].get(k, 0) for s in stats_list) / n)
            for k in all_keys
        }

    @staticmethod
    def _average_countries(stats_list: list, n: int) -> list:
        avg_total = round(sum(s["total"] for s in stats_list) / n) or 1
        pct_sums: dict = {}
        for s in stats_list:
            session_total = s["total"] or 1
            for entry in s["top_countries"]:
                c = entry["country"]
                pct_sums[c] = pct_sums.get(c, 0) + entry["count"] / session_total
        return [
            {"country": c, "count": round(pct / n * avg_total)}
            for c, pct in sorted(pct_sums.items(), key=lambda x: -x[1])[:10]
        ]

    @staticmethod
    def _is_submitted(status: str) -> bool:
        if not status or status == "N/A" or "unsubmitted" in status.lower():
            return False
        return "submitted" in status.lower()
