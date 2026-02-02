import streamlit as st
from pathlib import Path

from engine.laravel import list_laravel_projects, ensure_env_defaults
from engine.templates import (
    docker_compose_yml,
    nginx_default_conf,
    php_dockerfile,
    php_ini_overrides,
)
from engine.docker import (
    docker_compose_up,
    docker_compose_down,
    mysql_volume_exists,
    mark_mysql_initialized,
)
from engine.artisan import artisan
from engine.fs import ensure_file, ensure_directory, MountError, safe_backup


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def normalize_projects_path(path: Path) -> Path:
    """
    Prevent paths like /projects/projects by collapsing duplicates.
    """
    parts = list(path.parts)
    if len(parts) >= 2 and parts[-1] == parts[-2]:
        return Path(*parts[:-1])
    return path


# -------------------------------------------------
# UI setup
# -------------------------------------------------
st.set_page_config(page_title="Laravel Docker Setup", layout="wide")
st.title("🐳 Laravel Docker Setup Automator")
st.caption("Docker-powered Laravel dev environment")


# -------------------------------------------------
# Sidebar
# -------------------------------------------------
with st.sidebar:
    st.header("📁 Projects folder")

    projects_dir = st.text_input(
        "Path to your projects directory",
        value=str((Path.cwd() / "../").resolve()),
    )

    st.divider()
    st.header("⚙️ Options")

    overwrite_compose = st.checkbox("Overwrite docker-compose.yml", value=True)
    update_env = st.checkbox("Ensure .env defaults", value=True)
    auto_disable_compose_yaml = st.checkbox("Disable compose.yaml", value=True)
    auto_migrate = st.checkbox("Run migrations on startup", value=True)


# -------------------------------------------------
# Project discovery (SAFE)
# -------------------------------------------------
root = normalize_projects_path(
    Path(projects_dir).expanduser().resolve()
)

if not root.exists():
    st.error(f"Folder does not exist: {root}")
    st.stop()

projects = list_laravel_projects(root)

if not projects:
    st.warning("No Laravel projects found.")
    st.stop()

project = st.selectbox(
    "Select a Laravel project",
    projects,
    format_func=lambda p: p.name,
)

st.success(f"Selected project: {project.name}")


# -------------------------------------------------
# Paths
# -------------------------------------------------
compose_path = project / "docker-compose.yml"
compose_yaml = project / "compose.yaml"

docker_dir = project / "docker"
nginx_dir = docker_dir / "nginx"
php_dir = docker_dir / "php"

nginx_conf = nginx_dir / "default.conf"
php_dockerfile_path = php_dir / "Dockerfile"
php_ini_path = php_dir / "zz-overrides.ini"


# -------------------------------------------------
# Non-destructive warnings
# -------------------------------------------------
if mysql_volume_exists(project):
    st.warning(
        "⚠️ Existing MySQL data detected.\n\n"
        "If credentials changed, consider running:\n"
        "`docker compose down -v`"
    )

if compose_yaml.exists():
    st.warning(
        "⚠️ compose.yaml found — Docker prefers this over docker-compose.yml"
    )

    if auto_disable_compose_yaml:
        backup = compose_yaml.with_suffix(".yaml.bak")
        compose_yaml.rename(backup)
        st.info(f"Renamed compose.yaml → {backup.name}")


# -------------------------------------------------
# Actions (ALL side effects live here)
# -------------------------------------------------
col1, col2, col3, col4 = st.columns([1, 1, 1, 2])


# ---------- Generate files ----------
with col1:
    if st.button("🧱 Generate files", type="primary"):
        try:
            # Directories
            ensure_directory(docker_dir)
            ensure_directory(nginx_dir)
            ensure_directory(php_dir)

            # Files
            ensure_file(nginx_conf, nginx_default_conf())
            ensure_file(php_dockerfile_path, php_dockerfile())
            ensure_file(php_ini_path, php_ini_overrides())

            # docker-compose.yml
            if compose_path.exists() and overwrite_compose:
                backup = safe_backup(compose_path)
                st.info(f"Backed up docker-compose.yml → {backup.name}")

            compose_path.write_text(
                docker_compose_yml(project.name),
                encoding="utf-8",
            )

            # .env
            if update_env:
                ensure_env_defaults(project)

            st.success("Files generated successfully")

        except MountError as e:
            st.error("Filesystem validation failed")
            st.code(str(e))
            st.stop()


# ---------- Docker down ----------
with col2:
    if st.button("🧨 Docker down"):
        ok, out = docker_compose_down(project)
        st.code(out)
        st.success("Containers stopped" if ok else "Failed")


# ---------- Docker up ----------
with col3:
    if st.button("🚀 Docker up"):
        ok, out = docker_compose_up(project)
        st.code(out)

        if ok:
            mark_mysql_initialized(project)

            if auto_migrate:
                ok_m, out_m = artisan(project, ["migrate"])
                st.code(out_m)

            st.success("Environment ready 🚀")
        else:
            st.error("Docker failed — see output above")


# ---------- Database tools ----------
with col4:
    st.subheader("🧬 Database")

    if st.button("Run migrations"):
        ok, out = artisan(project, ["migrate"])
        st.code(out)
        st.success("Migrations complete" if ok else "Migration failed")

    if st.button("Migrate fresh"):
        ok, out = artisan(project, ["migrate:fresh"])
        st.code(out)

    if st.button("Seed database"):
        ok, out = artisan(project, ["db:seed"])
        st.code(out)


# -------------------------------------------------
# Footer
# -------------------------------------------------
st.divider()
st.caption(
    "Filesystem mounts are validated before Docker runs "
    "to prevent file/dir binding errors."
)
