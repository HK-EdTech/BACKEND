from typing import List
from prisma import Prisma


class ModuleService:
    """Service for module and permission aggregation logic"""

    def __init__(self, db: Prisma):
        self.db = db

    async def get_user_modules_with_permissions(self, user_id: str) -> List[dict]:
        """
        Get modules accessible to user with aggregated permissions.

        Permission Aggregation:
        - User can have multiple roles (via profile_roles table)
        - Returns UNION of permissions across all roles (most permissive)
        - Modules sorted by seq_no

        Args:
            user_id: UUID of authenticated user

        Returns:
            List of modules with permissions array per module
        """

        # Step 1: Get all role IDs for this user
        user_roles = await self.db.profile_roles.find_many(
            where={"profile_id": user_id},
            include={"roles": True}
        )

        if not user_roles:
            return []

        role_ids = [ur.role_id for ur in user_roles]

        # Step 2: Get all role_module_perm records for these roles
        role_module_perms = await self.db.role_module_perm.find_many(
            where={"role_id": {"in": role_ids}},
            include={"modules": True, "permissions": True}
        )

        # Step 3: Aggregate permissions by module_code (UNION logic)
        module_perms_map = {}

        for rmp in role_module_perms:
            module_code = rmp.module_code
            permission = rmp.permission_code

            if module_code not in module_perms_map:
                module_perms_map[module_code] = {
                    "module": rmp.modules,
                    "permissions": set()
                }

            module_perms_map[module_code]["permissions"].add(permission)

        # Step 4: Build result list with permissions array
        result = []
        for module_code, data in module_perms_map.items():
            module = data["module"]
            permissions = sorted(list(data["permissions"]))  # Alphabetical order

            result.append({
                "module_code": module.module_code,
                "module_eng_name": module.module_eng_name,
                "module_chi_name": module.module_chi_name,
                "seq_no": module.seq_no,
                "route": module.route,
                "description": module.description,
                "descriptive_message": module.descriptive_message,
                "parent_module_code": module.parent_module_code,
                "permissions": permissions,
                "created_at": module.created_at,
                "updated_at": module.updated_at
            })

        # Step 5: Sort by seq_no
        result.sort(key=lambda x: x["seq_no"])

        return result
