from bw_gui.contracts import Key, KeySpec
from bw_gui.laufkern import (
    LaufKernManifest,
    LaufKernRoute,
    build_manifest,
    evaluate_intent_routes,
)
from bw_gui.contracts.keybinding import KeyBindingDefinition, KeybindingRuntimeContext


def test_laufkern_bridge_manifest_and_reachability():
    manifest = build_manifest(
        manifest_id="blattwerk.test",
        repo_name="blattwerk",
        intents=("open",),
        keybindings=(
            KeyBindingDefinition(
                binding_id="global.open",
                keys=(KeySpec.parse("Ctrl+O"),),
                intent="open",
            ),
        ),
        routes=(
            LaufKernRoute(
                route_id="route.open.shortcut",
                intent="open",
                route_type="shortcut",
                binding_id="global.open",
            ),
        ),
    )

    assert isinstance(manifest, LaufKernManifest)

    result = evaluate_intent_routes(
        manifest=manifest,
        intent="open",
        context=KeybindingRuntimeContext(active_mode="global"),
    )

    assert result.reachable is True


def test_runtime_manifest_provider_reports_canonical_key_notation():
    """Der Manifest-Provider liest ``definition.keys`` (früher ``sequence`` -> AttributeError)."""
    from bw_gui.contracts.keybinding import KeybindingRegistry

    from app.ui.laufkern_manifest_provider import build_runtime_shortcut_manifest

    registry = KeybindingRegistry()
    registry.register(
        KeyBindingDefinition(
            binding_id="quiz.enter",
            keys=(KeySpec.parse("Enter (tolerate: Shift)"), KeySpec.char("n", ())),
            intent="quiz.enter",
        )
    )
    manifest = build_runtime_shortcut_manifest(registry)
    assert [route.metadata["keys"] for route in manifest.routes] == [("Enter (tolerate: Shift)", "N")]
