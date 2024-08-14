from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from apps.users.domain.constants import USER_ROLE_PERMISSIONS, UserRoles
from typing import List


class Command(BaseCommand):
    """
    Create user groups and assign permissions.
    """

    help = "Create user groups and assign permissions"

    def _define_group(self, name: str) -> Group:
        """
        Define a group with the given name.
        """

        group, created = Group.objects.get_or_create(name=name)

        if created:
            self.stdout.write(
                msg=f"{self.style.MIGRATE_LABEL(text='Creating group')}: {name}"
            )
        else:
            self.stdout.write(
                msg=self.style.WARNING(text=f'Group "{name}" already exists:')
            )

        return group

    def _assign_permissions(self, permissions: List[str], group: Group) -> None:
        """
        Assign permissions to the given group.
        """

        for perm_codename in permissions:
            try:
                perm = Permission.objects.get(codename=perm_codename)
                group.permissions.add(perm)

                self.stdout.write(
                    msg=f"  Added {self.style.MIGRATE_LABEL(text=perm_codename)} permission... "
                    + self.style.SUCCESS(text="OK")
                )
            except Permission.DoesNotExist:
                self.stdout.write(
                    msg=f"  Permission {self.style.MIGRATE_LABEL(text=perm_codename)} not found... "
                    + self.style.ERROR(text="FAILED")
                )

    def handle(self, *args, **kwargs):
        """
        Handle the command, create groups and assign permissions.
        """

        user_roles = [UserRoles.SEARCHER.value]

        self.stdout.write(
            msg=self.style.MIGRATE_HEADING(
                text="The following user groups will be created:"
            )
            + self.style.MIGRATE_LABEL(
                text="".join([f"\n  - {role}" for role in user_roles])
            )
        )

        for role in user_roles:
            group = self._define_group(name=role)
            self._assign_permissions(
                permissions=USER_ROLE_PERMISSIONS[role]["perm_codename_list"],
                group=group,
            )

            self.stdout.write(
                msg=self.style.SUCCESS(
                    text="Permissions successfully assigned to the group."
                )
            )
