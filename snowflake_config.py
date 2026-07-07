import os

# --------------------------------------------------------------------------
# Snowflake config lookup.
#
# This checks three things against config tables in Snowflake:
#   1. Is this error pattern on the "ignore list" for this app/service?
#   2. What severity does this error map to (High/Medium/Low)?
#   3. What routing rule applies (which team/queue should this go to)?
#
# STUBBED MODE: if SNOWFLAKE_ACCOUNT env var isn't set, this returns safe
# defaults instead of failing, so the pipeline still runs end-to-end while
# real Snowflake credentials aren't wired up yet. Once connected, only
# _query_snowflake() needs a real implementation — nothing else changes.
# --------------------------------------------------------------------------

SNOWFLAKE_ENABLED = bool(os.environ.get("SNOWFLAKE_ACCOUNT"))

DEFAULT_SEVERITY = "Medium"
DEFAULT_ROUTING = "general-errors-queue"


def get_error_rules(application: str, error_message: str) -> dict:
    """
    Returns a dict:
      {
        "ignored": bool,
        "severity": "High" | "Medium" | "Low",
        "routing": str,
      }
    """
    if not SNOWFLAKE_ENABLED:
        return _stub_rules(error_message)

    return _query_snowflake(application, error_message)


def _stub_rules(error_message: str) -> dict:
    """Safe local fallback used until Snowflake is connected."""
    msg = error_message.lower()

    if "timeout" in msg:
        return {"ignored": False, "severity": "High", "routing": "infra-team-queue"}
    if "nullreference" in msg or "exception" in msg:
        return {"ignored": False, "severity": "High", "routing": "backend-team-queue"}
    if "500" in msg:
        return {"ignored": False, "severity": "Medium", "routing": "api-team-queue"}

    return {"ignored": False, "severity": DEFAULT_SEVERITY, "routing": DEFAULT_ROUTING}


def _query_snowflake(application: str, error_message: str) -> dict:
    """
    Real implementation goes here once Snowflake is connected.
    Expected tables:
      - APP_ERROR_RULES(application, pattern, ignored, severity, routing)

    Example (fill in once credentials exist):

    import snowflake.connector
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
    )
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ignored, severity, routing FROM APP_ERROR_RULES "
        "WHERE application = %s AND %s ILIKE '%' || pattern || '%' "
        "ORDER BY priority ASC LIMIT 1",
        (application, error_message),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"ignored": row[0], "severity": row[1], "routing": row[2]}
    return _stub_rules(error_message)
    """
    return _stub_rules(error_message)
