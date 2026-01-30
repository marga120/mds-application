"""
English Status Computation

This module handles computation and update of English language proficiency
status for applicants based on their test scores (TOEFL, IELTS, MELAB, PTE, CAEL).
"""

from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor

# Test score thresholds
TOEFL_LR_MIN = 22  # listening & reading
TOEFL_WS_MIN = 21  # writing & speaking
TOEFL_TOTAL_MIN = 90

IELTS_EACH_MIN = 6.0
IELTS_TOTAL_MIN = 6.5

MELAB_TOTAL_MIN = 64
PTE_TOTAL_MIN = 65
CAEL_EACH_MIN = 60


def safe_int(value):
    """Safely convert value to int."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_float(value):
    """Safely convert value to float."""
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def check_toefl_pass(row):
    """
    Check if TOEFL scores meet the requirements.

    @return: Tuple of (passed, description, failed_sections)
    """
    L = safe_int(row["listening"])
    W = safe_int(row["structure_written"])
    R = safe_int(row["reading"])
    S = safe_int(row["speaking"])
    T = safe_int(row["total_score"])

    mL = safe_int(row["mybest_listening"])
    mW = safe_int(row["mybest_writing"])
    mR = safe_int(row["mybest_reading"])
    mS = safe_int(row["mybest_speaking"])
    mT = safe_int(row["mybest_total"])

    num = row["toefl_number"] or 1

    # Regular attempt
    if all(v is not None for v in (L, W, R, S, T)):
        if (L >= TOEFL_LR_MIN and R >= TOEFL_LR_MIN and
            W >= TOEFL_WS_MIN and S >= TOEFL_WS_MIN and T >= TOEFL_TOTAL_MIN):
            return True, f"TOEFL{num}, score is above the minimum requirement (90)", []

    # MyBest composite
    if all(v is not None for v in (mL, mW, mR, mS, mT)):
        if (mL >= TOEFL_LR_MIN and mR >= TOEFL_LR_MIN and
            mW >= TOEFL_WS_MIN and mS >= TOEFL_WS_MIN and mT >= TOEFL_TOTAL_MIN):
            return True, f"TOEFL{num} (MyBest), score is above the minimum requirement (90)", []

    # Track failures
    failed_sections = []
    total_failed = False

    if all(v is not None for v in (L, W, R, S, T)):
        if L < TOEFL_LR_MIN:
            failed_sections.append("Listening")
        if R < TOEFL_LR_MIN:
            failed_sections.append("Reading")
        if W < TOEFL_WS_MIN:
            failed_sections.append("Writing")
        if S < TOEFL_WS_MIN:
            failed_sections.append("Speaking")
        if T < TOEFL_TOTAL_MIN:
            total_failed = True

    if total_failed and failed_sections:
        return False, None, [f"TOEFL{num} (Total)"]
    elif failed_sections:
        return False, None, [f"TOEFL{num} ({', '.join(failed_sections)})"]
    elif total_failed:
        return False, None, [f"TOEFL{num} (Total)"]
    else:
        return False, None, [f"TOEFL{num}"]


def check_ielts_pass(row):
    """Check if IELTS scores meet the requirements."""
    L = safe_float(row["listening"])
    R = safe_float(row["reading"])
    W = safe_float(row["writing"])
    S = safe_float(row["speaking"])
    T = safe_float(row["total_band_score"])
    num = row["ielts_number"] or 1

    if all(v is not None for v in (L, R, W, S, T)):
        if min(L, R, W, S) >= IELTS_EACH_MIN and T >= IELTS_TOTAL_MIN:
            return True, f"IELTS{num}, score is above the minimum requirement (6.5 overall, 6.0 each)", []

    # Track failures
    failed_sections = []
    total_failed = False

    if all(v is not None for v in (R, W, L, S, T)):
        if R < IELTS_EACH_MIN:
            failed_sections.append("Reading")
        if W < IELTS_EACH_MIN:
            failed_sections.append("Writing")
        if L < IELTS_EACH_MIN:
            failed_sections.append("Listening")
        if S < IELTS_EACH_MIN:
            failed_sections.append("Speaking")
        if T < IELTS_TOTAL_MIN:
            total_failed = True

    if total_failed and failed_sections:
        return False, None, [f"IELTS{num} (Total)"]
    elif failed_sections:
        return False, None, [f"IELTS{num} ({', '.join(failed_sections)})"]
    elif total_failed:
        return False, None, [f"IELTS{num} (Total)"]
    else:
        return False, None, [f"IELTS{num}"]


def compute_english_status(user_code: str, not_required_rule=None):
    """
    Compute english_status/english_description/english for a single applicant,
    using the first test that meets the minimum requirements.

    Order: TOEFL -> IELTS -> MELAB -> PTE -> CAEL
    """
    status = None
    desc = None
    failed_tests = []

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            # Optional "Not Required" rule hook
            if callable(not_required_rule):
                nr_ok, nr_reason = not_required_rule(cur, user_code)
                if nr_ok:
                    status = "Not Required"
                    desc = nr_reason or "Exempt from English requirement"
                    cur.execute(
                        """
                        UPDATE application_info
                           SET english_status = %s,
                               english_description = %s,
                               english = TRUE
                         WHERE user_code = %s
                        """,
                        (status, desc, user_code),
                    )
                    conn.commit()
                    return

            # 1) TOEFL
            cur.execute(
                """
                SELECT toefl_number, listening, structure_written, reading, speaking,
                       total_score, mybest_listening, mybest_writing,
                       mybest_reading, mybest_speaking, mybest_total
                  FROM toefl
                 WHERE user_code = %s
                 ORDER BY toefl_number
                """,
                (user_code,),
            )
            for row in cur.fetchall():
                passed, description, failures = check_toefl_pass(row)
                if passed:
                    status = "Passed"
                    desc = description
                    break
                failed_tests.extend(failures)

            if status == "Passed":
                _update_english_passed(cur, user_code, status, desc)
                conn.commit()
                return

            # 2) IELTS
            cur.execute(
                """
                SELECT ielts_number, listening, reading, writing, speaking, total_band_score
                  FROM ielts
                 WHERE user_code = %s
                 ORDER BY ielts_number
                """,
                (user_code,),
            )
            for row in cur.fetchall():
                passed, description, failures = check_ielts_pass(row)
                if passed:
                    status = "Passed"
                    desc = description
                    break
                failed_tests.extend(failures)

            if status == "Passed":
                _update_english_passed(cur, user_code, status, desc)
                conn.commit()
                return

            # 3) MELAB
            cur.execute("SELECT total FROM melab WHERE user_code = %s", (user_code,))
            melab = cur.fetchone()
            if melab is not None:
                total = safe_int(melab["total"])
                if total is not None and total >= MELAB_TOTAL_MIN:
                    status = "Passed"
                    desc = "MELAB, score is above the minimum requirement (64)"
                else:
                    failed_tests.append("MELAB")

            if status == "Passed":
                _update_english_passed(cur, user_code, status, desc)
                conn.commit()
                return

            # 4) PTE
            cur.execute("SELECT total FROM pte WHERE user_code = %s", (user_code,))
            pte = cur.fetchone()
            if pte is not None:
                total = safe_int(pte["total"])
                if total is not None and total >= PTE_TOTAL_MIN:
                    status = "Passed"
                    desc = "PTE, score is above the minimum requirement (65)"
                else:
                    failed_tests.append("PTE")

            if status == "Passed":
                _update_english_passed(cur, user_code, status, desc)
                conn.commit()
                return

            # 5) CAEL
            cur.execute(
                "SELECT reading, listening, writing, speaking FROM cael WHERE user_code = %s",
                (user_code,),
            )
            cael = cur.fetchone()
            if cael is not None:
                R = safe_int(cael["reading"])
                L = safe_int(cael["listening"])
                W = safe_int(cael["writing"])
                S = safe_int(cael["speaking"])
                if all(v is not None for v in (R, L, W, S)) and min(R, L, W, S) >= CAEL_EACH_MIN:
                    status = "Passed"
                    desc = "CAEL, all sections >= 60"
                else:
                    failed_sections = []
                    if all(v is not None for v in (R, L, W, S)):
                        if R < CAEL_EACH_MIN:
                            failed_sections.append("Reading")
                        if L < CAEL_EACH_MIN:
                            failed_sections.append("Listening")
                        if W < CAEL_EACH_MIN:
                            failed_sections.append("Writing")
                        if S < CAEL_EACH_MIN:
                            failed_sections.append("Speaking")
                    if failed_sections:
                        failed_tests.append(f"CAEL ({', '.join(failed_sections)})")
                    else:
                        failed_tests.append("CAEL")

            # Finalize result
            if status == "Passed":
                _update_english_passed(cur, user_code, status, desc)
            else:
                if not failed_tests:
                    cur.execute(
                        """
                        UPDATE application_info
                           SET english_status = 'Not Met',
                               english_description = 'No English tests submitted',
                               english = FALSE
                         WHERE user_code = %s
                        """,
                        (user_code,),
                    )
                else:
                    if len(failed_tests) == 1:
                        desc_text = f"{failed_tests[0]} is below the minimum requirement"
                    else:
                        desc_text = f"{', '.join(failed_tests)} are below the minimum requirement"

                    cur.execute(
                        """
                        UPDATE application_info
                        SET english_status = 'Not Met',
                            english_description = %s,
                            english = FALSE
                        WHERE user_code = %s
                        """,
                        (desc_text, user_code),
                    )

        conn.commit()

    finally:
        try:
            conn.close()
        except Exception:
            pass


def _update_english_passed(cur, user_code, status, desc):
    """Helper to update application_info with passed English status."""
    cur.execute(
        """
        UPDATE application_info
           SET english_status = %s,
               english_description = %s,
               english = TRUE
         WHERE user_code = %s
        """,
        (status, desc, user_code),
    )


def compute_english_status_for_all(not_required_rule=None):
    """
    Recompute english_status for every row in application_info.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT user_code FROM application_info ORDER BY user_code")
            codes = [r["user_code"] for r in cur.fetchall()]
    finally:
        try:
            conn.close()
        except Exception:
            pass

    for code in codes:
        compute_english_status(code, not_required_rule=not_required_rule)
