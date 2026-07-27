class TestUserManagementService:
    async def test_assign_roles_updates_role_names_and_permissions(self, user_management_service, user_repo):
        user = await user_repo.create("target@example.com", "hashed", "Target")

        updated = await user_management_service.assign_roles(
            actor_id=user.id, target_user_id=user.id, role_names=("manager",)
        )

        assert updated.role_names == ("manager",)
        assert "audit:read" in updated.permission_codes

    async def test_assign_roles_logs_audit_event_with_actor_and_target(
        self, user_management_service, user_repo, audit_log_repo
    ):
        actor = await user_repo.create("actor@example.com", "hashed", "Actor")
        target = await user_repo.create("target2@example.com", "hashed", "Target")

        await user_management_service.assign_roles(actor.id, target.id, ("admin",))

        event = audit_log_repo.events[-1]
        assert event["event_type"] == "roles_assigned"
        assert event["user_id"] == actor.id
        assert event["metadata"]["target_user_id"] == str(target.id)

    async def test_deactivate_user_sets_is_active_false(self, user_management_service, user_repo):
        user = await user_repo.create("deactivate@example.com", "hashed", None)

        await user_management_service.deactivate_user(actor_id=user.id, target_user_id=user.id)

        deactivated = await user_repo.get_by_id(user.id)
        assert deactivated.is_active is False

    async def test_list_users_returns_created_users(self, user_management_service, user_repo):
        await user_repo.create("a@example.com", "hashed", None)
        await user_repo.create("b@example.com", "hashed", None)

        users = await user_management_service.list_users()

        assert {u.email for u in users} == {"a@example.com", "b@example.com"}

    async def test_list_audit_logs_returns_logged_events(self, user_management_service, audit_log_repo):
        await audit_log_repo.log_event("some_event", None, None, None)

        entries = await user_management_service.list_audit_logs()

        assert len(entries) == 1
        assert entries[0].event_type == "some_event"
