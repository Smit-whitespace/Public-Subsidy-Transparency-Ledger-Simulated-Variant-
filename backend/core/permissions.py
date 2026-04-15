class Permissions:
    # Public access (no login required)
    PUBLIC_VIEW = "public:view"
    PUBLIC_SEARCH = "public:search"
    PUBLIC_METRICS = "public:metrics"
    
    # Analytics & Reporting
    READ_ANALYTICS = "read:analytics"
    EXPORT_DATA = "export:data"
    GENERATE_REPORTS = "reports:generate"
    
    # Subsidy operations
    READ_SUBSIDIES = "read:subsidies"
    WRITE_SUBSIDIES = "write:subsidies"
    DELETE_SUBSIDIES = "delete:subsidies"
    
    # Project operations
    READ_PROJECTS = "read:projects"
    WRITE_PROJECTS = "write:projects"
    DELETE_PROJECTS = "delete:projects"
    
    # Disbursement operations
    READ_DISBURSEMENTS = "read:disbursements"
    WRITE_DISBURSEMENTS = "write:disbursements"
    APPROVE_DISBURSEMENTS = "disbursements:approve"
    
    # Audit & Investigation
    READ_AUDITS = "read:audits"
    INVESTIGATE = "investigate:anomalies"
    RISK_ANALYSIS = "risk:analysis"
    
    # Administration
    ADMIN_MANAGE_USERS = "admin:manage_users"
    ADMIN_ROLES = "admin:roles"
    ADMIN_SYSTEM = "admin:system"


class RoleNames:
    """Government role constants"""
    PUBLIC = "public"
    MEDIA = "media"
    AUDITOR = "auditor"
    GOVERNMENT_OFFICIAL = "government_official"
    ADMIN = "admin"


# Role hierarchy for quick reference
ROLE_HIERARCHY = {
    RoleNames.PUBLIC: 0,
    RoleNames.MEDIA: 1,
    RoleNames.AUDITOR: 2,
    RoleNames.GOVERNMENT_OFFICIAL: 3,
    RoleNames.ADMIN: 4,
}