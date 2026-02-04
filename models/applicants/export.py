"""
Export Functions for Applicant Data

This module handles export operations for applicant data, including
selected applicant exports and complete database exports.
"""

from utils.db_helpers import db_connection


def get_selected_applicants_for_export(user_codes, sections=None):
    """
    Fetch aggregated data for a selected list of applicants with specific formatting.
    Matches the specific "Student#, Program Code..." report format.

    @param user_codes: List of user codes to export
    @param sections: Optional list of sections to include ('personal', 'application', 'institutions')
    @return: Tuple of (applicants_list, error_message)
    """
    if not user_codes:
        return [], None
    if not isinstance(user_codes, (list, tuple)):
        user_codes = [user_codes]

    try:
        with db_connection() as (conn, cursor):
            all_sections = sections is None or len(sections) == 0
            inc_personal = all_sections or 'personal' in sections
            inc_app = all_sections or 'application' in sections
            inc_edu = all_sections or 'institutions' in sections or 'education' in sections

            select_parts = []

            if inc_personal or inc_app:
                select_parts.append("ast.student_number as \"Student#\"")

            if inc_app:
                select_parts.extend([
                    "s.program_code as \"Program Code\"",
                    "s.session_abbrev as \"Session\"",
                    "TO_CHAR(ast.app_start, 'DD-MM-YYYY') as \"Application Start Date\"",
                    "TO_CHAR(ast.submit_date, 'DD-MM-YYYY') as \"Submitted Date\"",
                    "ast.status_code as \"Status Code\"",
                    "ast.status as \"Status\""
                ])

            if inc_personal:
                select_parts.extend([
                    "ai.gender_code as \"Gender CODE\"",
                    "ai.visa_type_code as \"Visa Type CODE\"",
                    "ai.age as \"Age\"",
                    """CASE
                        WHEN ai.age <18 THEN '18-'
                        WHEN ai.age BETWEEN 18 AND 25 THEN '18-24'
                        WHEN ai.age BETWEEN 25 AND 34 THEN '25-34'
                        WHEN ai.age BETWEEN 35 AND 44 THEN '35-44'
                        WHEN ai.age BETWEEN 45 AND 54 THEN '45-54'
                        WHEN ai.age >= 55 THEN '55+'
                        ELSE ''
                       END as "Age Range"
                    """,
                    "ai.country_citizenship as \"Country of Current Citizenship\"",
                    "ai.primary_spoken_lang as \"Primary Spoken Language\"",
                    "ai.country as \"Country of Current Residence\"",
                    "ai.city as \"City\"",
                    "ai.province_state_region as \"Province, State or Region\""
                ])

            # Admin / Offer Status (always included)
            select_parts.extend([
                "CASE WHEN COALESCE(app.sent, 'Not Reviewed') = 'Not Reviewed' THEN 'N' ELSE 'Y' END AS \"Admission Review\"",
                "CASE WHEN app.sent IN ('Send Offer to CoGS', 'Offer Sent to CoGS', 'Offer Sent to Student', 'Offer Accepted', 'Offer Declined') THEN 'Y' ELSE '' END AS \"Offer Sent\"",
                "CASE WHEN app.sent = 'Offer Accepted' THEN 'Accepted' WHEN app.sent = 'Offer Deferred' THEN 'Deferred' WHEN app.sent = 'Offer Declined' THEN 'Declined' ELSE '' END AS \"Offer Status\"",
                "CASE WHEN app.scholarship = 'Yes' THEN 'yes' ELSE '' END AS \"Scholarship Offered\""
            ])

            if inc_edu:
                select_parts.extend([
                    "COALESCE(CAST(ai.academic_history_code AS TEXT), '') as \"Academic History Source CODE\"",
                    "COALESCE(CAST((SELECT EXTRACT(YEAR FROM MAX(date_confer)) FROM institution_info WHERE user_code = ai.user_code) AS TEXT), '') as \"Year of Last Degree\"",
                    "COALESCE(CAST((EXTRACT(YEAR FROM CURRENT_DATE) - (SELECT EXTRACT(YEAR FROM MAX(date_confer)) FROM institution_info WHERE user_code = ai.user_code)) AS TEXT), '') as \"Years Since Degree\"",
                    """CASE
                        WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - (SELECT EXTRACT(YEAR FROM MAX(date_confer)) FROM institution_info WHERE user_code = ai.user_code)) <= 0 THEN '="0"'
                        WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - (SELECT EXTRACT(YEAR FROM MAX(date_confer)) FROM institution_info WHERE user_code = ai.user_code)) <= 2 THEN '="1-2"'
                        WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - (SELECT EXTRACT(YEAR FROM MAX(date_confer)) FROM institution_info WHERE user_code = ai.user_code)) <= 5 THEN '="3-5"'
                        WHEN (SELECT MAX(date_confer) FROM institution_info WHERE user_code = ai.user_code) IS NOT NULL THEN '="6+"'
                        ELSE ''
                    END as "Years Since Degree Grouped"
                    """,
                    """CASE
                        WHEN app.highest_degree ILIKE '%%Doc%%' OR app.highest_degree ILIKE '%%PhD%%' OR app.highest_degree = 'MD' THEN 'Doctorate'
                        WHEN app.highest_degree ILIKE '%%Mast%%' OR app.highest_degree ILIKE '%%MD/MS%%' THEN 'Master''s'
                        WHEN app.highest_degree ILIKE '%%Bach%%' THEN 'Bachelor''s'
                        WHEN app.highest_degree IS NOT NULL AND app.highest_degree != '' THEN 'Bachelor''s'
                        ELSE ''
                    END as "Level of Education"
                    """,
                    "COALESCE(CAST(app.degree_area AS TEXT), '') as \"Subject of Degree\"",
                    """CASE
                        WHEN app.degree_area ILIKE '%%comput%%' OR app.degree_area ILIKE '%%tech%%' OR app.degree_area ILIKE '%%software%%' THEN 'Computer Science / Engineering / Technology'
                        WHEN app.degree_area ILIKE '%%engineering%%' OR app.degree_area ILIKE '%%elect%%' OR app.degree_area ILIKE '%%mech%%' THEN 'Engineering (excluding computer engineering)'
                        WHEN app.degree_area ILIKE '%%stat%%' OR app.degree_area ILIKE '%%math%%' OR app.degree_area ILIKE '%%actuarial%%' THEN 'Stats / Math / Actuarial Sciences'
                        WHEN app.degree_area ILIKE '%%science%%' OR app.degree_area ILIKE '%%chem%%' OR app.degree_area ILIKE '%%physic%%' OR app.degree_area ILIKE '%%bio%%' THEN 'Sciences'
                        WHEN app.degree_area ILIKE '%%arts%%' OR app.degree_area ILIKE '%%psych%%' OR app.degree_area ILIKE '%%lang%%' THEN 'Arts'
                        WHEN app.degree_area ILIKE '%%financ%%' OR app.degree_area ILIKE '%%mba%%' OR app.degree_area ILIKE '%%bus%%' OR app.degree_area ILIKE '%%econ%%' THEN 'Finance / Business / Management / Economics'
                        WHEN app.degree_area IS NOT NULL AND app.degree_area != '' THEN 'Other'
                        ELSE ''
                       END as "Subject Grouped"
                    """
                ])

            if inc_personal or inc_app:
                select_parts.extend([
                    "COALESCE(CAST(ai.interest AS TEXT), '') as \"Source of Interest in UBC\"",
                    "CASE WHEN app.mds_v = 'Yes' THEN 'Y' ELSE '' END as \"Applied MDS-V\"",
                    "CASE WHEN app.mds_o = 'Yes' THEN 'Y' ELSE '' END as \"Applied MDS-O\"",
                    "CASE WHEN app.mds_cl = 'Yes' THEN 'Y' ELSE '' END as \"Applied MDS-CL\""
                ])

            if not select_parts:
                select_parts = ["ai.user_code as \"User Code\""]

            placeholders = ','.join(['%s'] * len(user_codes))

            query = f"""
                SELECT {', '.join(select_parts)}
                FROM applicant_info ai
                LEFT JOIN applicant_status ast ON ai.user_code = ast.user_code
                LEFT JOIN application_info app ON ai.user_code = app.user_code
                LEFT JOIN sessions s ON ai.session_id = s.id
                LEFT JOIN program_info pi ON ai.user_code = pi.user_code
                WHERE ai.user_code IN ({placeholders})
                ORDER BY ai.family_name, ai.given_name
            """

            cursor.execute(query, tuple(user_codes))
            return cursor.fetchall(), None

    except Exception as e:
        print(f"Error in get_selected_applicants_for_export: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, f"Database error: {str(e)}"


def get_all_applicants_complete_export():
    """
    Fetch every single piece of information for all applicants in the database.

    @return: Tuple of (applicants_list, error_message)
    """
    try:
        with db_connection() as (conn, cursor):
            query = """
                SELECT
                    -- Basic Identification
                    ai.user_code AS "User Code",
                    ast.student_number AS "Student Number",

                    -- Session & Program Info
                    s.id AS "Session ID",
                    s.program_code AS "Program Code",
                    s.program AS "Program",
                    s.session_abbrev AS "Session Abbreviation",
                    s.year AS "Session Year",
                    s.name AS "Session Name",
                    s.description AS "Session Description",
                    pi.program_code AS "Program Info Code",
                    pi.program AS "Program Info Name",
                    pi.session AS "Program Info Session",

                    -- Personal Information
                    ai.interest_code AS "Interest Code",
                    ai.interest AS "Source of Interest",
                    ai.title AS "Title",
                    ai.family_name AS "Family Name",
                    ai.given_name AS "Given Name",
                    ai.middle_name AS "Middle Name",
                    ai.preferred_name AS "Preferred Name",
                    ai.former_family_name AS "Former Family Name",
                    ai.gender_code AS "Gender Code",
                    ai.gender AS "Gender",
                    ai.country_birth_code AS "Country of Birth Code",
                    ai.country_birth AS "Country of Birth",
                    TO_CHAR(ai.date_birth, 'YYYY-MM-DD') AS "Date of Birth",
                    ai.age AS "Age",
                    CASE
                        WHEN ai.age < 18 THEN 'Under 18'
                        WHEN ai.age BETWEEN 18 AND 24 THEN '18-24'
                        WHEN ai.age BETWEEN 25 AND 34 THEN '25-34'
                        WHEN ai.age BETWEEN 35 AND 44 THEN '35-44'
                        WHEN ai.age BETWEEN 45 AND 54 THEN '45-54'
                        WHEN ai.age >= 55 THEN '55+'
                        ELSE NULL
                    END AS "Age Range",

                    -- Citizenship & Visa
                    ai.country_citizenship_code AS "Country of Citizenship Code",
                    ai.country_citizenship AS "Country of Citizenship",
                    ai.dual_citizenship_code AS "Dual Citizenship Code",
                    ai.dual_citizenship AS "Dual Citizenship",
                    ai.visa_type_code AS "Visa Type Code",
                    ai.visa_type AS "Visa Type",

                    -- Language
                    ai.primary_spoken_lang_code AS "Primary Language Code",
                    ai.primary_spoken_lang AS "Primary Spoken Language",
                    ai.other_spoken_lang_code AS "Other Language Code",
                    ai.other_spoken_lang AS "Other Spoken Language",

                    -- Contact Information
                    ai.country_code AS "Current Country Code",
                    ai.country AS "Current Country",
                    ai.address_line1 AS "Address Line 1",
                    ai.address_line2 AS "Address Line 2",
                    ai.city AS "City",
                    ai.province_state_region AS "Province/State/Region",
                    ai.postal_code AS "Postal Code",
                    ai.primary_telephone AS "Primary Telephone",
                    ai.secondary_telephone AS "Secondary Telephone",
                    ai.email AS "Email",

                    -- Diversity & Background
                    ai.aboriginal AS "Aboriginal",
                    ai.first_nation AS "First Nation",
                    ai.inuit AS "Inuit",
                    ai.metis AS "Metis",
                    ai.aboriginal_not_specified AS "Aboriginal Not Specified",
                    ai.aboriginal_info AS "Aboriginal Information",
                    ai.racialized AS "Racialized",
                    ai.academic_history_code AS "Academic History Code",
                    ai.academic_history AS "Academic History",
                    ai.ubc_academic_history AS "UBC Academic History",

                    -- Application Status
                    TO_CHAR(ast.app_start, 'DD-MM-YYYY') AS "Application Start Date",
                    TO_CHAR(ast.submit_date, 'DD-MM-YYYY') AS "Application Submit Date",
                    ast.status_code AS "Application Status Code",
                    ast.status AS "Application Status",
                    ast.detail_status AS "Application Detail Status",

                    -- Application Review Info
                    app.sent AS "Review Status",
                    app.full_name AS "Full Name",
                    app.canadian AS "Canadian",
                    app.english AS "English Proficiency Met",
                    app.english_status AS "English Status",
                    app.english_description AS "English Description",
                    app.english_comment AS "English Comment",

                    -- Prerequisites & Academics
                    app.cs AS "Computer Science Prerequisite",
                    app.stat AS "Statistics Prerequisite",
                    app.math AS "Mathematics Prerequisite",
                    app.additional_comments AS "Additional Comments",
                    app.gpa AS "GPA",
                    app.highest_degree AS "Highest Degree",
                    app.degree_area AS "Degree Area",

                    -- MDS Program Applications
                    app.mds_v AS "Applied MDS Vancouver",
                    app.mds_cl AS "Applied MDS Computational Linguistics",
                    app.mds_o AS "Applied MDS Okanagan",

                    -- Scholarship & Offers
                    app.scholarship AS "Scholarship Status",
                    CASE
                        WHEN app.sent IN ('Send Offer to CoGS', 'Offer Sent to CoGS', 'Offer Sent to Student', 'Offer Accepted', 'Offer Declined')
                        THEN 'Yes'
                        ELSE 'No'
                    END AS "Offer Sent",

                    -- TOEFL Scores (Aggregated as JSON)
                    COALESCE(
                        (SELECT JSON_AGG(
                            JSON_BUILD_OBJECT(
                                'registration_number', t.registration_num,
                                'date_written', TO_CHAR(t.date_written, 'YYYY-MM-DD'),
                                'total_score', t.total_score,
                                'listening', t.listening,
                                'structure_written', t.structure_written,
                                'reading', t.reading,
                                'speaking', t.speaking
                            ) ORDER BY t.date_written DESC
                        ) FROM toefl t WHERE t.user_code = ai.user_code),
                        '[]'::json
                    ) AS "TOEFL Scores",

                    -- IELTS Scores (Aggregated as JSON)
                    COALESCE(
                        (SELECT JSON_AGG(
                            JSON_BUILD_OBJECT(
                                'candidate_number', i.candidate_num,
                                'date_written', TO_CHAR(i.date_written, 'YYYY-MM-DD'),
                                'total_band_score', i.total_band_score,
                                'listening', i.listening,
                                'reading', i.reading,
                                'writing', i.writing,
                                'speaking', i.speaking
                            ) ORDER BY i.date_written DESC
                        ) FROM ielts i WHERE i.user_code = ai.user_code),
                        '[]'::json
                    ) AS "IELTS Scores",

                    -- Other Test Scores
                    melab.total AS "MELAB Total Score",
                    pte.total AS "PTE Total Score",
                    duolingo.score AS "Duolingo Score",
                    gre.verbal AS "GRE Verbal",
                    gre.quantitative AS "GRE Quantitative",
                    gmat.total AS "GMAT Total Score",

                    -- Institution History (Aggregated as JSON)
                    COALESCE(
                        (SELECT JSON_AGG(
                            JSON_BUILD_OBJECT(
                                'institution_name', inst.full_name,
                                'country', inst.country,
                                'program_of_study', inst.program_study,
                                'degree_conferred', inst.degree_confer,
                                'date_conferred', TO_CHAR(inst.date_confer, 'YYYY-MM-DD'),
                                'credential_received', inst.credential_receive,
                                'gpa', inst.gpa
                            ) ORDER BY inst.institution_number
                        ) FROM institution_info inst WHERE inst.user_code = ai.user_code),
                        '[]'::json
                    ) AS "Institution History",

                    -- Ratings & Comments (Aggregated as JSON)
                    COALESCE(
                        (SELECT JSON_AGG(
                            JSON_BUILD_OBJECT(
                                'rating', r.rating,
                                'comment', r.user_comment,
                                'reviewer_name', u.first_name || ' ' || u.last_name
                            ) ORDER BY r.created_at DESC
                        ) FROM ratings r
                        JOIN "user" u ON r.user_id = u.id
                        WHERE r.user_code = ai.user_code),
                        '[]'::json
                    ) AS "Ratings and Comments",

                    -- Average Rating
                    (SELECT ROUND(AVG(r.rating), 2)
                     FROM ratings r
                     WHERE r.user_code = ai.user_code AND r.rating IS NOT NULL) AS "Average Rating",

                    -- Timestamps
                    TO_CHAR(ai.created_at, 'YYYY-MM-DD HH24:MI:SS') AS "Created At",
                    TO_CHAR(ai.updated_at, 'YYYY-MM-DD HH24:MI:SS') AS "Updated At"

                FROM applicant_info ai
                LEFT JOIN applicant_status ast ON ai.user_code = ast.user_code
                LEFT JOIN application_info app ON ai.user_code = app.user_code
                LEFT JOIN sessions s ON ai.session_id = s.id
                LEFT JOIN program_info pi ON ai.user_code = pi.user_code
                LEFT JOIN melab ON ai.user_code = melab.user_code
                LEFT JOIN pte ON ai.user_code = pte.user_code
                LEFT JOIN gre ON ai.user_code = gre.user_code
                LEFT JOIN gmat ON ai.user_code = gmat.user_code
                LEFT JOIN duolingo ON ai.user_code = duolingo.user_code
                ORDER BY ai.family_name, ai.given_name
            """

            cursor.execute(query)
            return cursor.fetchall(), None

    except Exception as e:
        print(f"Error in get_all_applicants_complete_export: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, f"Database error: {str(e)}"
