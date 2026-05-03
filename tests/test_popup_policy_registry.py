from bw_libs.ui_contract.popup import POPUP_KIND_MODAL, POPUP_KIND_NON_MODAL, PopupPolicy, PopupPolicyRegistry


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


def test_mode_blocking_popup_respects_policy_flag() -> None:
    registry = PopupPolicyRegistry()
    registry.register_policy(PopupPolicy(policy_id="dialog.modal", kind=POPUP_KIND_MODAL))
    registry.register_policy(
        PopupPolicy(
            policy_id="dialog.non_blocking",
            kind=POPUP_KIND_NON_MODAL,
            affects_mode=False,
            trap_focus=False,
        )
    )

    registry.open_popup("runtime", "Runtime", "dialog.non_blocking")
    assert registry.has_active_popup() is True
    assert registry.has_mode_blocking_popup() is False

    registry.open_popup("modal", "Modal", "dialog.modal")
    assert registry.has_mode_blocking_popup() is True
