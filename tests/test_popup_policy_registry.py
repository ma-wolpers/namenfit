from app.ui.popup_policy import POPUP_KIND_MODAL, PopupPolicy, PopupPolicyRegistry


def test_popup_policy_registry_stack_behavior() -> None:
    registry = PopupPolicyRegistry()
    registry.register_policy(PopupPolicy(policy_id="dialog.modal", kind=POPUP_KIND_MODAL))

    registry.open_popup("runtime-debug", "Runtime Debug", "dialog.modal")
    registry.open_popup("settings", "Settings", "dialog.modal")

    assert registry.has_active_popup() is True
    assert registry.active_popup() is not None
    assert registry.active_popup().popup_id == "settings"

    assert registry.close_popup("settings") is True
    assert registry.active_popup() is not None
    assert registry.active_popup().popup_id == "runtime-debug"

    registry.close_all()
    assert registry.active_popup() is None
