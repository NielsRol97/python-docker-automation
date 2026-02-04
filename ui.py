import streamlit as st
from pathlib import Path
from dataclasses import dataclass

from engine.laravel import list_laravel_projects
from engine.docker import mysql_volume_exists
from engine.fs import MountError
from engine.app import generate_docker_files
from engine.workflows import (
    start_environment,
    stop_environment,
    reset_database,
    WorkflowResult,
)
from engine.safety import SafetyContext, SafetyError


# -------------------------------------------------
# UI helpers
# -------------------------------------------------
def normalize_projects_path(path: Path) -> Path:
    parts = list(path.parts)
    if len(parts) >= 2 and parts[-1] == parts[-2]:
        return Path(*parts[:-1])
    return path


def render_workflow(result: WorkflowResult) -> None:
    for step in result.steps:
        st.info(step)

    if result.result:
        if result.result.stdout:
            st.code(result.result.stdout)
        if result.result.stderr:
            st.code(result.result.stderr, language="text")

    if result.ok:
        st.success("Workflow completed successfully 🚀")
    else:
        st.error(result.error or "Workflow failed")


# -------------------------------------------------
# UI state
# -------------------------------------------------
@dataclass(frozen=True)
class UiOptions:
    overwrite_compose: bool
    update_env: bool
    auto_migrate: bool
    confirm_destructive: bool


# -------------------------------------------------
# Page setup
# -------------------------------------------------
st.set_page_config(
    page_title="Laravel Docker Setup",
    page_icon="🐳",
    layout="wide",
)

st.title("🐳 Laravel Docker Setup Automator")
st.subheader("A safe, repeatable Docker environment for Laravel projects")
st.markdown("---")


# -------------------------------------------------
# Sidebar
# -------------------------------------------------
with st.sidebar:
    st.header("📁 Project discovery")

    projects_dir = st.text_input(
        "Projects root directory",
        value=str((Path.cwd() / "../").resolve()),
    )

    st.divider()
    st.header("⚙️ Setup options")

    options = UiOptions(
        overwrite_compose=st.checkbox(
            "Overwrite docker-compose.yml",
            value=True,
        ),
        update_env=st.checkbox(
            "Ensure .env defaults",
            value=True,
        ),
        auto_migrate=st.checkbox(
            "Run migrations after Docker up",
            value=True,
        ),
        confirm_destructive=st.checkbox(
            "I understand this may delete data",
            value=False,
        ),
    )


# -------------------------------------------------
# Project discovery
# -------------------------------------------------
root = normalize_projects_path(Path(projects_dir).expanduser().resolve())

if not root.exists():
    st.error(f"Folder does not exist: {root}")
    st.stop()

projects = list_laravel_projects(root)

if not projects:
    st.warning("No Laravel projects found.")
    st.stop()

project = st.selectbox(
    "Laravel project",
    projects,
    format_func=lambda p: p.name,
)

st.success(f"Using project: **{project.name}**")


# -------------------------------------------------
# Warnings
# -------------------------------------------------
if mysql_volume_exists(project):
    st.warning(
        "⚠️ Existing MySQL data detected.\n\n"
        "Destructive actions require confirmation."
    )


# -------------------------------------------------
# Main actions
# -------------------------------------------------
st.markdown("---")
col1, col2, col3, col4 = st.columns([1.2, 1, 1.2, 1.6])

safety = SafetyContext(
    project=project,
    confirmed=options.confirm_destructive,
)


# ---------- Generate files ----------
with col1:
    st.markdown("### 🧱 Files")
    if st.button("Generate Docker files", type="primary"):
        try:
            with st.status("Generating configuration files..."):
                actions = generate_docker_files(
                    project,
                    overwrite_compose=options.overwrite_compose,
                    update_env=options.update_env,
                )

            for action in actions:
                st.info(action)

            st.success("Docker configuration ready")

        except MountError as e:
            st.error("Filesystem validation failed")
            st.code(str(e))


# ---------- Stop ----------
with col2:
    st.markdown("### 🧨 Stop")
    if st.button("Docker down"):
        try:
            with st.status("Stopping environment..."):
                result = stop_environment(project, safety=safety)
            render_workflow(result)
        except SafetyError as e:
            st.error(str(e))


# ---------- Start ----------
with col3:
    st.markdown("### 🚀 Start")
    if st.button("Docker up"):
        with st.status("Starting environment...", expanded=True):
            result = start_environment(
                project,
                auto_migrate=options.auto_migrate,
            )
        render_workflow(result)


# ---------- Database ----------
with col4:
    st.markdown("### 🧬 Database tools")

    if st.button("Migrate fresh"):
        try:
            with st.status("Resetting database..."):
                result = reset_database(
                    project,
                    seed=False,
                    safety=safety,
                )
            render_workflow(result)
        except SafetyError as e:
            st.error(str(e))

    if st.button("Migrate fresh + seed"):
        try:
            with st.status("Resetting & seeding database..."):
                result = reset_database(
                    project,
                    seed=True,
                    safety=safety,
                )
            render_workflow(result)
        except SafetyError as e:
            st.error(str(e))


# -------------------------------------------------
# Footer
# -------------------------------------------------
st.markdown("---")
st.caption(
    "🔒 Destructive actions require explicit confirmation.\n\n"
    "UI declares intent only — workflows enforce safety."
)
