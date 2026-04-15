from sqlalchemy.orm import Session
import json

from backend.models.role import Role
from backend.core.permissions import Permissions, RoleNames


def seed_roles(db: Session):
    roles_config = [
        # Government Role System
        {
            "name": RoleNames.PUBLIC,
            "display_name": "Public Citizen",
            "description": "Public access to transparency portal - view subsidies, search funding, access metrics",
            "permissions": [
                Permissions.PUBLIC_VIEW,
                Permissions.PUBLIC_SEARCH,
                Permissions.PUBLIC_METRICS,
                Permissions.READ_SUBSIDIES,
                Permissions.READ_PROJECTS,
            ],
        },
        {
            "name": RoleNames.MEDIA,
            "display_name": "Media & Press",
            "description": "Journalist access - analytics dashboards, dataset downloads, report generation",
            "permissions": [
                Permissions.PUBLIC_VIEW,
                Permissions.PUBLIC_SEARCH,
                Permissions.READ_ANALYTICS,
                Permissions.EXPORT_DATA,
                Permissions.GENERATE_REPORTS,
                Permissions.READ_SUBSIDIES,
                Permissions.READ_PROJECTS,
                Permissions.READ_DISBURSEMENTS,
                Permissions.READ_AUDITS,
            ],
        },
        {
            "name": RoleNames.AUDITOR,
            "display_name": "Financial Auditor",
            "description": "Audit access - view audit logs, investigate anomalies, risk analysis tools",
            "permissions": [
                Permissions.READ_ANALYTICS,
                Permissions.READ_SUBSIDIES,
                Permissions.READ_PROJECTS,
                Permissions.READ_DISBURSEMENTS,
                Permissions.READ_AUDITS,
                Permissions.INVESTIGATE,
                Permissions.RISK_ANALYSIS,
            ],
        },
        {
            "name": RoleNames.GOVERNMENT_OFFICIAL,
            "display_name": "Government Official",
            "description": "Government operations - create subsidies, manage projects, record disbursements",
            "permissions": [
                Permissions.PUBLIC_VIEW,
                Permissions.READ_ANALYTICS,
                Permissions.READ_SUBSIDIES,
                Permissions.WRITE_SUBSIDIES,
                Permissions.READ_PROJECTS,
                Permissions.WRITE_PROJECTS,
                Permissions.READ_DISBURSEMENTS,
                Permissions.WRITE_DISBURSEMENTS,
                Permissions.APPROVE_DISBURSEMENTS,
                Permissions.READ_AUDITS,
            ],
        },
        {
            "name": RoleNames.ADMIN,
            "display_name": "Administrator",
            "description": "Full system access - all operations including user and role management",
            "permissions": [
                Permissions.PUBLIC_VIEW,
                Permissions.PUBLIC_SEARCH,
                Permissions.PUBLIC_METRICS,
                Permissions.READ_ANALYTICS,
                Permissions.EXPORT_DATA,
                Permissions.GENERATE_REPORTS,
                Permissions.READ_SUBSIDIES,
                Permissions.WRITE_SUBSIDIES,
                Permissions.DELETE_SUBSIDIES,
                Permissions.READ_PROJECTS,
                Permissions.WRITE_PROJECTS,
                Permissions.DELETE_PROJECTS,
                Permissions.READ_DISBURSEMENTS,
                Permissions.WRITE_DISBURSEMENTS,
                Permissions.APPROVE_DISBURSEMENTS,
                Permissions.READ_AUDITS,
                Permissions.INVESTIGATE,
                Permissions.RISK_ANALYSIS,
                Permissions.ADMIN_MANAGE_USERS,
                Permissions.ADMIN_ROLES,
                Permissions.ADMIN_SYSTEM,
            ],
        },
    ]

    for role_data in roles_config:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()

        if not existing:
            db.add(
                Role(
                    name=role_data["name"],
                    display_name=role_data["display_name"],
                    description=role_data["description"],
                    permissions=json.dumps(role_data["permissions"]),
                )
            )

    db.commit()