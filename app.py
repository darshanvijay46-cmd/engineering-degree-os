import os
from datetime import datetime, date
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# APP CONFIG & PATH SETUP
# ==========================================
st.set_page_state = "wide"
st.set_page_config(
    page_title="My Engineering Degree OS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Custom Styling for Professional Academic Dashboard
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-card h4 {
        margin: 0;
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-card p {
        margin: 0.35rem 0 0 0;
        font-size: 1.6rem;
        font-weight: 700;
        color: #0F172A;
    }
    .tag-completed {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .tag-progress {
        background-color: #FEF08A;
        color: #713F12;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .tag-notstarted {
        background-color: #F1F5F9;
        color: #475569;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# DATA HANDLERS & DEFAULTS
# ==========================================
DEFAULT_SCHEMAS = {
    "semesters.csv": [
        "semester",
        "academic_year",
        "year_of_study",
        "status",
        "total_credits",
        "remarks",
    ],
    "courses.csv": [
        "semester",
        "course_code",
        "course_title",
        "credits",
        "syllabus_topics",
        "status",
    ],
    "calendar.csv": [
        "event_id",
        "title",
        "event_type",
        "start_date",
        "end_date",
        "semester",
        "academic_year",
        "notes",
    ],
    "assessments.csv": [
        "assessment_id",
        "semester",
        "course_code",
        "assessment_type",
        "due_date",
        "max_marks",
        "weightage_percent",
        "status",
    ],
    "scores.csv": [
        "semester",
        "course_code",
        "course_title",
        "credits",
        "score_obtained",
        "max_score",
        "grade",
    ],
    "plan_checklist.csv": [
        "item_id",
        "category",
        "task",
        "target_date",
        "status",
        "notes",
    ],
    "university_syllabus.csv": [
        "programme_name",
        "regulation",
        "degree",
        "department",
        "total_credits_required",
        "syllabus_source_url",
        "overview",
    ],
}


def load_csv(filename: str) -> pd.DataFrame:
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=DEFAULT_SCHEMAS.get(filename, []))
    try:
        df = pd.read_csv(file_path)
        # Accept common alternate headers used by course CSVs and normalize
        # them for the rest of the app.
        if filename == "courses.csv":
            aliases = {
                "course_name": "course_title",
                "syllabus": "syllabus_topics",
            }
            rename = {
                old: new
                for old, new in aliases.items()
                if old in df.columns and new not in df.columns
            }
            df = df.rename(columns=rename)
        elif filename == "assessments.csv":
            # The supplied assessment file calls this column `date`; the
            # dashboard and assistant use the clearer canonical name.
            if "date" in df.columns and "due_date" not in df.columns:
                df = df.rename(columns={"date": "due_date"})
        elif filename == "scores.csv":
            aliases = {
                "score": "score_obtained",
                "max_marks": "max_score",
            }
            rename = {
                old: new
                for old, new in aliases.items()
                if old in df.columns and new not in df.columns
            }
            df = df.rename(columns=rename)
        return df
    except Exception as e:
        st.warning(f"Unable to parse `{filename}`: {e}")
        return pd.DataFrame(columns=DEFAULT_SCHEMAS.get(filename, []))


def save_csv(filename: str, df: pd.DataFrame) -> bool:
    file_path = os.path.join(DATA_DIR, filename)
    try:
        df.to_csv(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving `{filename}`: {e}")
        return False


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.markdown("### 🎓 Degree OS")
st.sidebar.caption("Engineering Degree Workspace")

menu_selection = st.sidebar.radio(
    "Go to",
    [
        "1. Dashboard",
        "2. Semesters 1-8",
        "3. Courses & Syllabus",
        "4. University Syllabus",
        "5. Academic / Leave Calendar",
        "6. Internal Assessments",
        "7. Status Tracker",
        "8. Scorecard",
        "9. Plan & Checklist",
        "10. Ask Degree AI",
        "11. Data Admin",
    ],
    index=0,
)

st.sidebar.divider()
st.sidebar.caption("System: Python + Streamlit + CSV")
st.sidebar.caption(f"Data Folder: `{DATA_DIR}`")


# ==========================================
# 1. DASHBOARD
# ==========================================
if menu_selection == "1. Dashboard":
    st.markdown(
        "<div class='main-header'>Student Academic Dashboard</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sub-header'>Executive overview of degree completion, milestones, and upcoming academic events.</div>",
        unsafe_allow_html=True,
    )

    sem_df = load_csv("semesters.csv")
    courses_df = load_csv("courses.csv")
    calendar_df = load_csv("calendar.csv")
    assessments_df = load_csv("assessments.csv")
    scores_df = load_csv("scores.csv")
    univ_df = load_csv("university_syllabus.csv")

    if (
        sem_df.empty
        or courses_df.empty
        or calendar_df.empty
        or assessments_df.empty
    ):
        st.warning(
            "Some data files are currently empty or missing. Visit **Data Admin** to verify CSV files."
        )

    # Determine current semester
    current_sem = "Semester 1"
    if not sem_df.empty and "status" in sem_df.columns:
        in_prog = sem_df[sem_df["status"].str.strip().str.lower() == "in progress"]
        if not in_prog.empty:
            current_sem = in_prog.iloc[0]["semester"]
        else:
            not_done = sem_df[
                sem_df["status"].str.strip().str.lower() != "completed"
            ]
            if not not_done.empty:
                current_sem = not_done.iloc[0]["semester"]
            elif len(sem_df) > 0:
                current_sem = sem_df.iloc[-1]["semester"]

    # Credits & completion
    total_req_credits = 160
    if not univ_df.empty and "total_credits_required" in univ_df.columns:
        try:
            total_req_credits = int(univ_df.iloc[0]["total_credits_required"])
        except (ValueError, TypeError):
            total_req_credits = 160

    completed_credits = 0
    if not courses_df.empty and "credits" in courses_df.columns:
        completed_courses = courses_df[
            courses_df["status"].str.strip().str.lower() == "completed"
        ]
        completed_credits = pd.to_numeric(
            completed_courses["credits"], errors="coerce"
        ).sum()

    deg_pct = (
        min(100.0, (completed_credits / total_req_credits) * 100)
        if total_req_credits > 0
        else 0.0
    )

    # Next Assessment
    next_asm_str = "None scheduled"
    if not assessments_df.empty and "due_date" in assessments_df.columns:
        today_str = date.today().strftime("%Y-%m-%d")
        upcoming_asm = assessments_df[
            (assessments_df["due_date"] >= today_str)
            & (assessments_df["status"].str.lower() != "completed")
        ].sort_values("due_date")
        if not upcoming_asm.empty:
            top_asm = upcoming_asm.iloc[0]
            next_asm_str = f"{top_asm['course_code']} ({top_asm['assessment_type']}) on {top_asm['due_date']}"

    # Next Holiday/Leave
    next_holiday_str = "None scheduled"
    if not calendar_df.empty and "start_date" in calendar_df.columns:
        today_str = date.today().strftime("%Y-%m-%d")
        upcoming_leaves = calendar_df[
            (
                calendar_df["event_type"].str.contains(
                    "Leave|Holiday", case=False, na=False
                )
            )
            & (calendar_df["start_date"] >= today_str)
        ].sort_values("start_date")
        if not upcoming_leaves.empty:
            top_h = upcoming_leaves.iloc[0]
            next_holiday_str = f"{top_h['title']} ({top_h['start_date']})"

    # Score summary
    score_summary_str = "N/A"
    if (
        not scores_df.empty
        and "score_obtained" in scores_df.columns
        and "max_score" in scores_df.columns
    ):
        obt = pd.to_numeric(scores_df["score_obtained"], errors="coerce").sum()
        mx = pd.to_numeric(scores_df["max_score"], errors="coerce").sum()
        if mx > 0:
            score_summary_str = f"{(obt / mx) * 100:.1f}% Avg"

    # Metrics Layout
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""<div class='metric-card'>
            <h4>Active Semester</h4>
            <p>{current_sem}</p>
        </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class='metric-card'>
            <h4>Degree Progress</h4>
            <p>{deg_pct:.1f}%</p>
        </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div class='metric-card'>
            <h4>Earned Credits</h4>
            <p>{int(completed_credits)} / {total_req_credits}</p>
        </div>""",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""<div class='metric-card'>
            <h4>Prototype Score</h4>
            <p>{score_summary_str}</p>
        </div>""",
            unsafe_allow_html=True,
        )

    st.write("")
    st.progress(deg_pct / 100.0)

    # Next items row
    c_left, c_right = st.columns(2)
    with c_left:
        st.info(f"📌 **Next Upcoming Assessment:** {next_asm_str}")
    with c_right:
        st.success(f"🌴 **Next Upcoming Holiday / Leave:** {next_holiday_str}")

    st.divider()

    # Active Semester Course Snapshot
    st.subheader(f"Current Semester Snapshot: {current_sem}")
    active_courses = courses_df[courses_df["semester"] == current_sem]
    if not active_courses.empty:
        st.dataframe(
            active_courses[
                ["course_code", "course_title", "credits", "status"]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption(f"No courses mapped for {current_sem} yet.")


# ==========================================
# 2. SEMESTERS 1-8
# ==========================================
elif menu_selection == "2. Semesters 1-8":
    st.markdown(
        "<div class='main-header'>Semester Progression (Sem 1 to 8)</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sub-header'>Eight-semester curriculum roadmap and structural overview.</div>",
        unsafe_allow_html=True,
    )

    sem_df = load_csv("semesters.csv")
    courses_df = load_csv("courses.csv")

    if sem_df.empty:
        st.warning("No semester data located in `data/semesters.csv`.")
    else:
        # Semester cards grid (2 rows of 4)
        for row_idx in range(2):
            cols = st.columns(4)
            for col_idx in range(4):
                sem_index = row_idx * 4 + col_idx
                if sem_index < len(sem_df):
                    row = sem_df.iloc[sem_index]
                    s_name = row.get("semester", f"Semester {sem_index+1}")
                    s_status = row.get("status", "Not Started")
                    s_year = row.get("year_of_study", "")
                    s_credits = row.get("total_credits", 20)

                    # Count courses in this semester
                    c_count = 0
                    if not courses_df.empty:
                        c_count = len(courses_df[courses_df["semester"] == s_name])

                    badge_class = (
                        "tag-completed"
                        if s_status == "Completed"
                        else "tag-progress"
                        if s_status == "In Progress"
                        else "tag-notstarted"
                    )

                    with cols[col_idx]:
                        st.markdown(
                            f"""
                            <div class='metric-card' style='margin-bottom: 1rem;'>
                                <h4>{s_year}</h4>
                                <h3 style='margin:0.2rem 0; font-size:1.15rem; color:#1E293B;'>{s_name}</h3>
                                <p style='font-size:0.85rem; color:#475569; margin: 0.2rem 0;'>Credits: {s_credits} | Courses: {c_count}</p>
                                <span class='{badge_class}'>{s_status}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

        st.divider()
        st.subheader("Filter Semester Specifics")
        selected_sem = st.selectbox(
            "Select Semester to Inspect", sem_df["semester"].tolist()
        )

        filtered_sem_info = sem_df[sem_df["semester"] == selected_sem].iloc[0]
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Academic Year", filtered_sem_info.get("academic_year", "-"))
        col_b.metric("Year of Study", filtered_sem_info.get("year_of_study", "-"))
        col_c.metric("Semester Status", filtered_sem_info.get("status", "-"))

        st.write("#### Courses in " + selected_sem)
        if not courses_df.empty:
            sc = courses_df[courses_df["semester"] == selected_sem]
            if not sc.empty:
                st.dataframe(
                    sc[
                        [
                            "course_code",
                            "course_title",
                            "credits",
                            "syllabus_topics",
                            "status",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(f"No courses assigned to {selected_sem}.")


# ==========================================
# 3. COURSES & SYLLABUS
# ==========================================
elif menu_selection == "3. Courses & Syllabus":
    st.markdown(
        "<div class='main-header'>Course Catalog & Syllabus Topics</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sub-header'>Detailed course list, unit topics, credit distribution, and status.</div>",
        unsafe_allow_html=True,
    )

    courses_df = load_csv("courses.csv")
    st.caption(f"Reading courses from `{os.path.join(DATA_DIR, 'courses.csv')}`")
    if courses_df.empty:
        st.warning(
            f"File `{os.path.join(DATA_DIR, 'courses.csv')}` is missing or empty. Please check Data Admin."
        )
    else:
        # Filters
        sem_list = ["All"] + sorted(courses_df["semester"].dropna().unique().tolist())
        status_list = ["All"] + sorted(
            courses_df["status"].dropna().unique().tolist()
        )

        f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
        with f_col1:
            filter_sem = st.selectbox("Semester", sem_list)
        with f_col2:
            filter_status = st.selectbox("Status", status_list)
        with f_col3:
            search_query = st.text_input(
                "Search Course Code / Title / Syllabus", ""
            )

        view_df = courses_df.copy()
        if filter_sem != "All":
            view_df = view_df[view_df["semester"] == filter_sem]
        if filter_status != "All":
            view_df = view_df[view_df["status"] == filter_status]
        if search_query.strip():
            q = search_query.lower()
            view_df = view_df[
                view_df["course_code"].astype(str).str.lower().str.contains(q)
                | view_df["course_title"]
                .astype(str)
                .str.lower()
                .str.contains(q)
                | view_df["syllabus_topics"]
                .astype(str)
                .str.lower()
                .str.contains(q)
            ]

        st.caption(f"Showing {len(view_df)} of {len(courses_df)} courses")
        st.dataframe(view_df, use_container_width=True, hide_index=True)


# ==========================================
# 4. UNIVERSITY SYLLABUS
# ==========================================
elif menu_selection == "4. University Syllabus":
    st.markdown(
        "<div class='main-header'>University Programme Syllabus</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sub-header'>Programme level regulation overview, department information, and source repository.</div>",
        unsafe_allow_html=True,
    )

    univ_df = load_csv("university_syllabus.csv")
    if univ_df.empty:
        st.warning("`data/university_syllabus.csv` is empty or not found.")
    else:
        info = univ_df.iloc[0]

        c1, c2, c3 = st.columns(3)
        c1.metric("Degree", info.get("degree", "B.Tech"))
        c2.metric("Department", info.get("department", "CSE"))
        c3.metric(
            "Regulation / System",
            info.get("regulation", "CBCS"),
        )

        st.write("")
        st.markdown("#### Programme Scope & Description")
        st.write(info.get("overview", "No overview provided."))

        st.write("")
        st.markdown("#### Official University Reference Source")
        url_link = info.get("syllabus_source_url", "")
        if url_link:
            st.code(url_link, language="text")
            st.markdown(
                f"🔗 [Open Official University Syllabus Document]({url_link})"
            )
        else:
            st.info("No external syllabus URL defined.")


# ==========================================
# 5. ACADEMIC / LEAVE CALENDAR
# ==========================================
elif menu_selection == "5. Academic / Leave Calendar":
    st.markdown(
        "<div class='main-header'>Academic & Leave Calendar</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sub-header'>Institutional schedule, internal exam dates, festival leaves, and term breaks.</div>",
        unsafe_allow_html=True,
    )

    cal_df = load_csv("calendar.csv")
    if cal_df.empty:
        st.warning("`data/calendar.csv` not found or empty.")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            ay_options = ["All"] + sorted(
                cal_df["academic_year"].dropna().unique().tolist()
            )
            sel_ay = st.selectbox("Academic Year", ay_options)
        with col_f2:
            sem_options = ["All"] + sorted(
                cal_df["semester"].dropna().unique().tolist()
            )
            sel_sem = st.selectbox("Semester", sem_options)
        with col_f3:
            type_options = ["All"] + sorted(
                cal_df["event_type"].dropna().unique().tolist()
            )
            sel_type = st.selectbox("Event Category", type_options)

        f_cal = cal_df.copy()
        if sel_ay != "All":
            f_cal = f_cal[f_cal["academic_year"] == sel_ay]
        if sel_sem != "All":
            f_cal = f_cal[f_cal["semester"] == sel_sem]
        if sel_type != "All":
            f_cal = f_cal[f_cal["event_type"] == sel_type]

        st.dataframe(f_cal, use_container_width=True, hide_index=True)


# ==========================================
# 6. INTERNAL ASSESSMENTS
# ==========================================
elif menu_selection == "6. Internal Assessments":
    st.markdown(
        "<div class='main-header'>Internal Assessments Tracker</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sub-header'>IA1, IA2, assignments, laboratory evaluations, project reviews, and examinations.</div>",
        unsafe_allow_html=True,
    )

    asm_df = load_csv("assessments.csv")
    if asm_df.empty:
        st.warning("No assessment records found in `data/assessments.csv`.")
    else:
        a_col1, a_col2 = st.columns(2)
        with a_col1:
            sem_filter = st.selectbox(
                "Filter Semester",
                ["All"] + sorted(asm_df["semester"].dropna().unique().tolist()),
            )
        with a_col2:
            type_filter = st.selectbox(
                "Assessment Type",
                ["All"]
                + sorted(asm_df["assessment_type"].dropna().unique().tolist()),
            )

        f_asm = asm_df.copy()
        if sem_filter != "All":
            f_asm = f_asm[f_asm["semester"] == sem_filter]
        if type_filter != "All":
            f_asm = f_asm[f_asm["assessment_type"] == type_filter]

        st.dataframe(f_asm, use_container_width=True, hide_index=True)


# ==========================================
# 7. STATUS TRACKER
# ==========================================
elif menu_selection == "7. Status Tracker":
    st.markdown(
        "<div class='main-header'>Degree Execution Status Tracker</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sub-header'>Not Started / In Progress / Completed states across the entire 8-semester scope.</div>",
        unsafe_allow_html=True,
    )

    courses_df = load_csv("courses.csv")
    checklist_df = load_csv("plan_checklist.csv")

    if courses_df.empty:
        st.warning("Course data unavailable.")
    else:
        # Standardize strings
        status_series = courses_df["status"].fillna("Not Started").str.strip()
        comp_count = (
            status_series.str.lower() == "completed"
        ).sum()
        inprog_count = (
            status_series.str.lower() == "in progress"
        ).sum()
        notstart_count = (
            status_series.str.lower() == "not started"
        ).sum()
        total_courses = len(courses_df)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Courses", total_courses)
        m2.metric("Completed", comp_count)
        m3.metric("In Progress", inprog_count)
        m4.metric("Not Started", notstart_count)

        st.write("")
        st.subheader("Courses by Workflow Status")
        status_choice = st.radio(
            "Select Status Bucket",
            ["All", "In Progress", "Not Started", "Completed"],
            horizontal=True,
        )

        filtered_c = courses_df.copy()
        if status_choice != "All":
            filtered_c = filtered_c[
                filtered_c["status"].str.strip().str.lower()
                == status_choice.lower()
            ]

        st.dataframe(
            filtered_c[
                [
                    "semester",
                    "course_code",
                    "course_title",
                    "credits",
                    "status",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


# ==========================================
# 8. SCORECARD
# ==========================================
elif menu_selection == "8. Scorecard":
    st.markdown(
        "<div class='main-header'>Academic Scorecard</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sub-header'>Course grades, raw score evaluations, and prototype average calculation.</div>",
        unsafe_allow_html=True,
    )

    scores_df = load_csv("scores.csv")
    st.caption(f"Reading scores from `{os.path.join(DATA_DIR, 'scores.csv')}`")
    if scores_df.empty:
        st.warning(
            f"No records found in `{os.path.join(DATA_DIR, 'scores.csv')}`."
        )
    else:
        # Disclaimer regarding CGPA
        st.info(
            "ℹ️ **Regulatory Notice on CGPA:** University CGPA formulas vary across institutions "
            "(e.g., relative standard deviation scales, 10-point weighted grade systems). "
            "The calculation shown here is explicitly a **Prototype Simple Average Percentage**."
        )

        sem_list = ["All"] + sorted(
            scores_df["semester"].dropna().unique().tolist()
        )
        selected_sem = st.selectbox("Filter Scorecard by Semester", sem_list)

        filtered_scores = scores_df.copy()
        if selected_sem != "All":
            filtered_scores = filtered_scores[
                filtered_scores["semester"] == selected_sem
            ]

        # Calculate metrics
        num_courses = len(filtered_scores)
        obt_total = pd.to_numeric(
            filtered_scores["score_obtained"], errors="coerce"
        ).sum()
        max_total = pd.to_numeric(
            filtered_scores["max_score"], errors="coerce"
        ).sum()
        pct = (obt_total / max_total * 100) if max_total > 0 else 0.0

        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Evaluated Courses", num_courses)
        sc2.metric("Total Marks Obtained", f"{obt_total:.0f} / {max_total:.0f}")
        sc3.metric("Prototype Simple Average Marks %", f"{pct:.2f}%")

        st.write("")
        st.dataframe(filtered_scores, use_container_width=True, hide_index=True)


# ==========================================
# 9. PLAN & CHECKLIST
# ==========================================
elif menu_selection == "9. Plan & Checklist":
    st.markdown(
        "<div class='main-header'>Plan & Checklist</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sub-header'>Personal action items, deliverables, and semester milestones stored in <code>data/plan_checklist.csv</code>.</div>",
        unsafe_allow_html=True,
    )

    checklist_df = load_csv("plan_checklist.csv")

    st.write("#### Add New Checklist Item")
    with st.form("add_checklist_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            new_cat = st.selectbox(
                "Category",
                ["Academic", "Project", "Internship", "Administrative", "Exam"],
            )
        with c2:
            new_task = st.text_input("Task / Milestone", "")
        with c3:
            new_date = st.date_input("Target Date", value=date.today())

        c4, c5 = st.columns([1, 3])
        with c4:
            new_status = st.selectbox(
                "Status", ["Not Started", "In Progress", "Completed"]
            )
        with c5:
            new_notes = st.text_input("Notes / Reference", "")

        submitted = st.form_submit_button("Add Task")
        if submitted:
            if not new_task.strip():
                st.error("Task description cannot be empty.")
            else:
                new_id = f"CHK-{len(checklist_df) + 1:02d}"
                new_row = pd.DataFrame(
                    [
                        {
                            "item_id": new_id,
                            "category": new_cat,
                            "task": new_task.strip(),
                            "target_date": new_date.strftime("%Y-%m-%d"),
                            "status": new_status,
                            "notes": new_notes.strip(),
                        }
                    ]
                )
                updated_df = pd.concat([checklist_df, new_row], ignore_index=True)
                if save_csv("plan_checklist.csv", updated_df):
                    st.success(f"Added task {new_id} successfully!")
                    st.rerun()

    st.divider()
    st.write("#### Manage Checklist Tasks")
    if not checklist_df.empty:
        edited_checklist = st.data_editor(
            checklist_df,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="checklist_editor",
        )
        if st.button("Save Changes to Checklist", type="primary"):
            if save_csv("plan_checklist.csv", edited_checklist):
                st.success("Checklist saved to `data/plan_checklist.csv`!")
                st.rerun()
    else:
        st.info("Checklist is empty. Add your first task using the form above.")


# ==========================================
# 10. ASK DEGREE AI
# ==========================================
elif menu_selection == "10. Ask Degree AI":
    st.markdown(
        "<div class='main-header'>Ask Degree AI Assistant</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sub-header'>Ask about your courses, calendar, assessments, scores, and plan.</div>",
        unsafe_allow_html=True,
    )
    system_instruction = (
        "You are Degree AI. Answer only from the supplied degree data. Do not invent university rules, dates, "
        "marks, formulas or syllabus content. If the requested information is missing, say: I cannot verify "
        "that from the current Degree OS data."
    )
    missing_answer = "I cannot verify that from the current Degree OS data."
    ai_data = {
        "Semesters": load_csv("semesters.csv"),
        "Courses": load_csv("courses.csv"),
        "Calendar": load_csv("academic_calendar.csv"),
        "Assessments": load_csv("assessments.csv"),
        "Scores": load_csv("scores.csv"),
        "Plan": load_csv("plan_checklist.csv"),
    }
    ai_sources = [
        ("Semesters", "semesters.csv"),
        ("Courses", "courses.csv"),
        ("Calendar", "academic_calendar.csv"),
        ("Assessments", "assessments.csv"),
        ("Scores", "scores.csv"),
        ("Plan", "plan_checklist.csv"),
    ]
    context_string = "\n\n".join(
        f"{area} ({filename}): {ai_data[area].fillna('').to_json(orient='records', force_ascii=False)}"
        for area, filename in ai_sources
    )

    def answer_locally(question):
        import re

        q = question.lower().strip()
        if "semester" in q and "status" in q:
            match = re.search(r"(?:semester|sem)\s*(\d+)", q)
            frame = ai_data["Semesters"]
            if match and not frame.empty and {"semester", "status"}.issubset(frame.columns):
                target = match.group(1)
                values = frame["semester"].astype(str).str.extract(r"(\d+)")[0]
                rows = frame[values == target]
                if not rows.empty:
                    return f"Semester {target} status: {rows.iloc[0]['status']}.", ["Semesters"]
            return missing_answer, ["Semesters"]

        if "incomplete course" in q or "incomplete courses" in q:
            frame = ai_data["Courses"]
            if not frame.empty and {"course_code", "status"}.issubset(frame.columns):
                rows = frame[frame["status"].fillna("").astype(str).str.lower() != "completed"]
                if not rows.empty:
                    labels = []
                    for _, row in rows.iterrows():
                        title = row.get("course_title", row.get("course_name", ""))
                        labels.append(f"{row['course_code']} {title} ({row['status']})".strip())
                    return "Incomplete courses: " + "; ".join(labels) + ".", ["Courses"]
            return missing_answer, ["Courses"]

        if "next assessment" in q:
            frame = ai_data["Assessments"]
            date_col = "due_date" if "due_date" in frame.columns else "date" if "date" in frame.columns else None
            if not frame.empty and date_col:
                dates = pd.to_datetime(frame[date_col], errors="coerce")
                mask = dates.notna() & (dates.dt.date >= date.today())
                rows = frame[mask].copy()
                rows["_sort_date"] = dates[mask]
                if "status" in rows.columns:
                    rows = rows[rows["status"].fillna("").astype(str).str.lower() != "completed"]
                rows = rows.sort_values("_sort_date")
                if not rows.empty:
                    row = rows.iloc[0]
                    return f"Your next assessment is {row.get('assessment_type', 'Assessment')} for {row.get('course_code', 'your course')} on {row[date_col]}.", ["Assessments"]
            return missing_answer, ["Assessments"]

        if "next holiday" in q:
            frame = ai_data["Calendar"]
            if not frame.empty and {"event_type", "start_date"}.issubset(frame.columns):
                dates = pd.to_datetime(frame["start_date"], errors="coerce")
                holidays = frame["event_type"].fillna("").astype(str).str.contains("holiday|leave|break", case=False)
                mask = holidays & dates.notna() & (dates.dt.date >= date.today())
                rows = frame[mask].copy()
                rows["_sort_date"] = dates[mask]
                rows = rows.sort_values("_sort_date")
                if not rows.empty:
                    row = rows.iloc[0]
                    return f"Your next holiday or leave is {row.get('title', 'listed event')} on {row['start_date']}.", ["Calendar"]
            return missing_answer, ["Calendar"]

        if "syllabus" in q or "topics" in q:
            frame = ai_data["Courses"]
            title_col = "course_title" if "course_title" in frame.columns else "course_name" if "course_name" in frame.columns else None
            topics_col = "syllabus_topics" if "syllabus_topics" in frame.columns else "syllabus" if "syllabus" in frame.columns else None
            if not frame.empty and topics_col:
                mask = pd.Series(False, index=frame.index)
                if "course_code" in frame.columns:
                    mask |= frame["course_code"].fillna("").astype(str).str.lower().map(lambda value: bool(value) and value in q)
                if title_col:
                    mask |= frame[title_col].fillna("").astype(str).str.lower().map(lambda value: bool(value) and value in q)
                rows = frame[mask]
                if not rows.empty and pd.notna(rows.iloc[0][topics_col]):
                    row = rows.iloc[0]
                    return f"Syllabus topics for {row.get('course_code', 'course')}: {row[topics_col]}.", ["Courses"]
            return missing_answer, ["Courses"]

        if "checklist" in q or "task status" in q:
            frame = ai_data["Plan"]
            if not frame.empty and "status" in frame.columns:
                if "task" in frame.columns:
                    mask = frame["task"].fillna("").astype(str).str.lower().map(lambda task: bool(task) and task in q)
                    rows = frame[mask]
                else:
                    rows = frame.iloc[0:0]
                if not rows.empty:
                    row = rows.iloc[0]
                    return f"Checklist status for {row.get('task', 'the task')}: {row['status']}.", ["Plan"]
                counts = frame["status"].fillna("Unknown").astype(str).value_counts()
                summary = ", ".join(f"{status}: {count}" for status, count in counts.items())
                return f"Checklist status: {summary}.", ["Plan"]
            return missing_answer, ["Plan"]

        return missing_answer, []

    def answer_with_gemini(question, key):
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)
        available = {
            model.name.rsplit("/", 1)[-1]
            for model in client.models.list()
            if getattr(model, "name", None)
        }
        candidates = ["gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]
        last_error = None
        for model_name in candidates:
            if model_name not in available:
                continue
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=f"{context_string}\n\nStudent question: {question}\nAnswer concisely and student-friendly.",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                        max_output_tokens=300,
                    ),
                )
                return response.text or missing_answer
            except Exception as error:
                last_error = error
                if "404" not in str(error):
                    raise
        if last_error:
            raise last_error
        raise RuntimeError("No free-tier Flash-Lite model is available to this API key.")

    api_key = ""
    try:
        api_key = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        pass

    user_query = st.text_input(
        "Ask a question about your degree data:",
        placeholder="Try: incomplete courses, next assessment, next holiday, syllabus topics for CS101, semester 3 status, or checklist status",
    )
    if st.button("Ask Degree AI", type="primary"):
        if not user_query.strip():
            st.warning("Please enter a question.")
        elif api_key:
            try:
                with st.spinner("Checking your Degree OS data..."):
                    answer = answer_with_gemini(user_query, api_key)
                st.markdown(answer)
                areas = [area for area, _ in ai_sources if not ai_data[area].empty]
                st.caption("Data areas used: " + (", ".join(areas) if areas else "None"))
            except Exception as error:
                st.error(f"Degree AI request failed: {error}")
        else:
            answer, areas = answer_locally(user_query)
            st.markdown(answer)
            st.caption("Data areas used: " + (", ".join(areas) if areas else "None"))


# ==========================================
# 11. DATA ADMIN
# ==========================================
elif menu_selection == "11. Data Admin":
    st.markdown(
        "<div class='main-header'>Data Admin & Editor</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='sub-header'>Directly edit, audit, and save core degree CSV datasets back to <code>/data</code>.</div>",
        unsafe_allow_html=True,
    )

    available_files = [
        "courses.csv",
        "semesters.csv",
        "calendar.csv",
        "assessments.csv",
        "scores.csv",
        "plan_checklist.csv",
        "university_syllabus.csv",
    ]

    selected_file = st.selectbox(
        "Select CSV Dataset to Edit",
        available_files,
    )

    st.caption(f"Target File: `{os.path.join('data', selected_file)}`")
    current_data = load_csv(selected_file)

    if current_data.empty:
        st.warning(
            f"`{selected_file}` is currently empty or does not exist on disk."
        )
        if st.button(f"Initialize Empty Schema for {selected_file}"):
            cols = DEFAULT_SCHEMAS.get(selected_file, ["id", "name"])
            blank_df = pd.DataFrame(columns=cols)
            save_csv(selected_file, blank_df)
            st.success(f"Initialized `{selected_file}` with schema.")
            st.rerun()

    # Editable Table
    edited_df = st.data_editor(
        current_data,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=f"editor_{selected_file}",
    )

    col_btn1 = st.columns([1])[0]
    with col_btn1:
        if st.button("Save Changes", type="primary"):
            if save_csv(selected_file, edited_df):
                st.success(f"Successfully saved updates to `data/{selected_file}`!")
                st.rerun()
