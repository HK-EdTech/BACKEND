from typing import List
from prisma import Prisma


class ModuleService:
    """Service for module and permission aggregation logic"""

    def __init__(self, db: Prisma):
        self.db = db

    async def get_user_modules_with_permissions(self, user_id: str) -> List[dict]:
        """
        Get modules accessible to user with aggregated permissions
        using a single DB query via nested includes.

        Fetches profile_roles → roles → role_module_perms → modules + permissions
        in one Prisma call, then aggregates permissions per module (UNION across roles).

        Returns list of modules with permissions array, sorted by seq_no.
        """

        # Single query: profile_roles → roles → role_module_perms → modules + permissions
        user_roles = await self.db.profile_roles.find_many(
            where={"profile_id": user_id},
            include={
                "roles": {
                    "include": {
                        "role_module_perms": {
                            "include": {
                                "modules": True,
                                "permissions": True
                            }
                        }
                    }
                }
            }
        )

        if not user_roles:
            return []

        # Aggregate permissions by module_code (UNION across all roles)
        module_perms_map = {}

        for pr in user_roles:
            for rmp in pr.roles.role_module_perms:
                module_code = rmp.module_code

                if module_code not in module_perms_map:
                    module_perms_map[module_code] = {
                        "module": rmp.modules,
                        "permissions": set()
                    }

                module_perms_map[module_code]["permissions"].add(rmp.permission_code)

        # Build result list sorted by seq_no
        result = []
        for module_code, data in module_perms_map.items():
            module = data["module"]
            result.append({
                "module_code": module.module_code,
                "module_eng_name": module.module_eng_name,
                "module_chi_name": module.module_chi_name,
                "seq_no": module.seq_no,
                "route": module.route,
                "description": module.description,
                "descriptive_message": module.descriptive_message,
                "parent_module_code": module.parent_module_code,
                "permissions": sorted(data["permissions"]),
                "created_at": module.created_at,
                "updated_at": module.updated_at
            })

        result.sort(key=lambda x: x["seq_no"])
        return result
