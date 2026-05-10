"""GUI-Komponenten des Namens-Trainers."""

import math
import random
import struct
import wave
from io import BytesIO
from bw_libs.shared_gui_core import ensure_bw_gui_on_path

ensure_bw_gui_on_path()
from bw_gui.runtime import ui, widgets

try:
    from bw_gui.menu import CustomMenuBar as SharedCustomMenuBar
    from bw_gui.menu import MenuDefinition as SharedMenuDefinition
    from bw_gui.menu import MenuItem as SharedMenuItem
except ModuleNotFoundError:
    SharedCustomMenuBar = None
    SharedMenuDefinition = None
    SharedMenuItem = None

try:
    from bw_gui.dialogs import SettingsDialogSpec as SharedSettingsDialogSpec
    from bw_gui.dialogs import SettingsFieldSpec as SharedSettingsFieldSpec
    from bw_gui.dialogs import SettingsSectionSpec as SharedSettingsSectionSpec
    from bw_gui.dialogs import open_tabbed_settings_dialog as open_shared_tabbed_settings_dialog
except ModuleNotFoundError:
    SharedSettingsDialogSpec = None
    SharedSettingsFieldSpec = None
    SharedSettingsSectionSpec = None
    open_shared_tabbed_settings_dialog = None

try:
    from bw_gui.shortcuts import compose_hover_text as compose_shared_hover_text
    from bw_gui.widgets import HoverTooltip as SharedHoverTooltip
except ModuleNotFoundError:
    compose_shared_hover_text = None
    SharedHoverTooltip = None

from time import perf_counter
from PIL import Image, ImageTk

try:
    import winsound
except ImportError:
    winsound = None

from .level_dialog import ask_level
from .phase_ui import apply_phase_ui
from ..core.models import (
    LEVEL_1,
    LEVEL_2,
    MODE_CSV,
    MODE_PHOTO,
    MODE_COMBINED,
    normalize_text,
)
from ..core.quiz_texts import PHASE_DONE, PHASE_GROUP, PHASE_NAME, PHASE_NEIGHBORS
from ..core.feedback import pick_feedback_line
from ..core.solve_logic import (
    build_combined_level2_result_text,
    build_csv_level2_result_text,
    combined_level2_task_score,
    csv_level2_task_score,
    evaluate_group_guess,
    evaluate_neighbors,
)
from ..core.stats_format import (
    format_percent,
    stats_text_level1,
    stats_text_level2,
)
from .learning_menu import populate_learning_menu
from bw_libs.ui_contract.keybinding import (
    UI_MODE_DIALOG,
    UI_MODE_EDITOR,
    UI_MODE_GLOBAL,
    UI_MODE_OFFLINE,
    KeyBindingDefinition,
    KeybindingRegistry,
    KeybindingRuntimeContext,
)
from bw_libs.ui_contract.hsm import (
    ESCAPE_CLOSE_POPUP,
    ESCAPE_EXIT_INLINE_EDITOR,
    build_ui_hsm_contract,
)
from bw_libs.ui_contract.popup import POPUP_KIND_MODAL, POPUP_KIND_NON_MODAL, PopupPolicy, PopupPolicyRegistry
from .ui_intents import UiIntent
from ..core.learning_profiles import (
    CUSTOM_PROFILE,
    FEEDBACK_STYLE_OPTIONS,
    LEARNING_PROFILE_ORDER,
    LEARNING_PROFILES,
    MIN_RETRIEVAL_OPTIONS,
    SLOW_CORRECT_THRESHOLD_OPTIONS,
)
from ..core.review_scheduler import REVIEW_PROFILES
from ..app_info import APP_INFO
from bw_libs.app_shell import AppShellConfig, TkinterAppShell
from .ui_theme import (
    DEFAULT_THEME,
    THEMES,
    THEME_ORDER,
    BG_MAIN,
    FG_MUTED,
    FG_PRIMARY,
    apply_window_theme,
    get_theme,
    normalize_theme_key,
    populate_theme_menu,
    style_entry,
    style_primary_button,
    style_secondary_button,
)


def _known_ui_intents() -> tuple[str, ...]:
    """Return all declared UiIntent string values."""

    values = []
    for key, value in UiIntent.__dict__.items():
        if key.startswith("_"):
            continue
        if isinstance(value, str):
            values.append(value)
    return tuple(sorted(set(values)))


class QuizApp:
    """Hauptfenster des Quiz mit levelabhängiger Auswertung und Statistik."""

    def __init__(
        self,
        root,
        people,
        grid,
        level,
        progress_store,
        mode=MODE_CSV,
        photo_map=None,
        ask_group_question=True,
        initial_theme_key=None,
        on_theme_changed=None,
        on_learning_settings_changed=None,
        debug_options=None,
        on_debug_options_changed=None,
        prompt_limit=None,
        sound_options=None,
        on_sound_options_changed=None,
        level2_require_group_before_neighbors=False,
        on_level2_setting_changed=None,
        shell_config: AppShellConfig | None = None,
    ):
        self.root = root
        resolved_shell_config = shell_config or AppShellConfig(
            title=APP_INFO.window_title,
            geometry="980x860",
            min_width=760,
            min_height=620,
        )
        self.app_shell = TkinterAppShell(self.root, resolved_shell_config, on_close=self._on_shell_close)
        self.progress_store = progress_store
        self.on_theme_changed_callback = on_theme_changed
        self.on_learning_settings_changed_callback = on_learning_settings_changed
        self.on_debug_options_changed_callback = on_debug_options_changed
        self.on_sound_options_changed_callback = on_sound_options_changed
        self.on_level2_setting_changed_callback = on_level2_setting_changed
        self.theme_key = normalize_theme_key(initial_theme_key or self.progress_store.get_theme_key())
        apply_window_theme(self.root, self.theme_key)
        self.people = people
        self.grid = grid
        self.level = level
        self.mode = mode
        self.photo_map = photo_map or {}
        self.ask_group_question = bool(ask_group_question)
        self.debug_options = dict(debug_options or {})
        provided_sound = sound_options if isinstance(sound_options, dict) else {}
        self.sound_enabled = bool(provided_sound.get("enabled", True))
        try:
            self.sound_volume = max(0, min(100, int(provided_sound.get("volume", 70))))
        except (TypeError, ValueError):
            self.sound_volume = 70
        self.prompt_limit = int(prompt_limit) if isinstance(prompt_limit, int) and prompt_limit > 0 else None
        self.level2_require_group_before_neighbors = bool(level2_require_group_before_neighbors)

        self.names = list(people.keys())
        self.session_intro_queue_by_level = {}
        self.introduced_names_by_level = {}
        self.current_name = None
        self.last_name = None
        self.awaiting_solution = True
        self.question_started_at = perf_counter()
        self.last_response_seconds = 0.0
        self.name_typo_available = False
        self.name_typo_field = None
        self.name_typo_phase = None
        self.pending_name_submission = None
        self.pending_level1_submission = None
        self.round_finished = False
        self.completed_prompts = 0
        self.current_prompt_completed = False
        self.current_prompt_success = False
        self.current_prompt_confused_with = None
        self.session_seen_names = set()
        self.session_prompt_results = {}
        self.session_confusions = {}
        self._runtime_shortcuts = KeybindingRegistry()
        self._hsm_contract = build_ui_hsm_contract(intents=_known_ui_intents())
        self._popup_registry = PopupPolicyRegistry()
        self._popup_registry.register_policy(PopupPolicy(policy_id="dialog.modal", kind=POPUP_KIND_MODAL))
        self._popup_registry.register_policy(
            PopupPolicy(
                policy_id="dialog.non_blocking",
                kind=POPUP_KIND_NON_MODAL,
                trap_focus=False,
                affects_mode=False,
            )
        )
        self._tracked_popup_ids = set()
        self._shortcut_debug_offline = False
        self._shortcut_runtime_debug_window = None
        self._shortcut_runtime_debug_table = None
        self._shortcut_runtime_debug_context_var = None
        self._shortcut_runtime_debug_summary_var = None
        self._shortcut_runtime_debug_offline_var = None
        self._shared_menu_bar = None
        self._hover_tooltips = []

        # Sequentielle Phasen-Logik
        self.current_phase = PHASE_GROUP
        self.phase_start_time = perf_counter()
        self.phase_times = {}  # {phase: seconds}
        self.phase_results = {}  # {phase: {field: ok}}

        # Bild-Referenz (muss gehalten werden für Tkinter)
        self.current_photo_image = None

        self._build_widgets()
        self._build_menu()
        self._apply_theme()
        self._bind_shortcuts()
        self._apply_level_widgets()
        self.next_person()

    def _on_shell_close(self) -> bool:
        """Close auxiliary windows before shutting down the root shell."""

        try:
            if hasattr(self, "_close_shortcut_runtime_debug_dialog"):
                self._close_shortcut_runtime_debug_dialog()
        except Exception:
            pass
        return True

    def _build_menu(self):
        """Erstellt die Menüleiste inkl. Theme-Auswahl."""

        self.theme_var = ui.StringVar(value=self.theme_key)
        self.review_profile_var = ui.StringVar(value=self.progress_store.get_review_profile())
        self.learning_profile_var = ui.StringVar(value=self.progress_store.get_learning_profile_key())
        self.allow_immediate_repeat_var = ui.BooleanVar(value=self.progress_store.get_allow_immediate_repeat())
        self.prioritize_urgent_var = ui.BooleanVar(value=self.progress_store.get_prioritize_urgent_repeats())
        self.mix_new_cards_var = ui.BooleanVar(value=self.progress_store.get_mix_new_cards())
        self.min_retrieval_seconds_var = ui.IntVar(value=self.progress_store.get_min_retrieval_seconds())
        self.revisit_slow_correct_var = ui.BooleanVar(value=self.progress_store.get_revisit_slow_correct())
        self.slow_correct_threshold_var = ui.IntVar(value=self.progress_store.get_slow_correct_threshold_seconds())
        self.feedback_style_var = ui.StringVar(value=self.progress_store.get_feedback_style())
        self.debug_show_panel_var = ui.BooleanVar(value=bool(self.debug_options.get("show_debug_panel", False)))
        self.debug_show_paths_var = ui.BooleanVar(value=bool(self.debug_options.get("show_paths", False)))
        self.sound_enabled_var = ui.BooleanVar(value=self.sound_enabled)
        self.sound_volume_var = ui.IntVar(value=self.sound_volume)
        self.level2_group_gate_var = ui.BooleanVar(value=self.level2_require_group_before_neighbors)

        if SharedCustomMenuBar is None or SharedMenuDefinition is None or SharedMenuItem is None:
            self._build_native_menu()
            return

        if self._shared_menu_bar is not None:
            self._shared_menu_bar.destroy()

        definitions = (
            SharedMenuDefinition(key="ansicht", label="Ansicht", alt="a", items_provider=self._menu_items_view),
            SharedMenuDefinition(key="lernen", label="Lernen", alt="l", items_provider=self._menu_items_learning),
            SharedMenuDefinition(key="debug", label="Debug", alt="d", items_provider=self._menu_items_debug),
            SharedMenuDefinition(key="ton", label="Ton", alt="t", items_provider=self._menu_items_sound),
            SharedMenuDefinition(key="sitzplan", label="Sitzplan", alt="s", items_provider=self._menu_items_seat),
        )

        self._shared_menu_bar = SharedCustomMenuBar(
            self.root,
            definitions,
            theme_key=self.theme_var.get(),
        )
        self._shared_menu_bar.build()
        self.root.config(menu="")

    def _set_menu_var(self, tk_var, value, callback=None):
        """Set a menu-backed Tk variable and run callback if configured."""

        if tk_var.get() != value:
            tk_var.set(value)
        if callable(callback):
            callback()

    def _toggle_menu_bool(self, tk_var, callback=None):
        """Toggle a bool variable from shared menu rows."""

        tk_var.set(not bool(tk_var.get()))
        if callable(callback):
            callback()

    def _set_theme_from_menu(self, theme_key):
        """Apply one theme selected from shared menu radio rows."""

        self.theme_var.set(theme_key)
        self._on_theme_changed()

    def _attach_hover_help(self, widget, *, label, shortcut=None):
        """Attach shared tooltip text for action buttons and shortcuts."""

        if SharedHoverTooltip is None:
            return

        shortcut_text = (shortcut or "").strip()
        if compose_shared_hover_text is not None:
            text = compose_shared_hover_text(label, shortcut_text)
        elif shortcut_text:
            text = f"{label}\nShortcut: {shortcut_text}"
        else:
            text = label

        tooltip = SharedHoverTooltip(widget, text, theme_key=self.theme_key)
        self._hover_tooltips.append(tooltip)

    def _menu_items_view(self):
        theme_items = tuple(
            SharedMenuItem(
                type="radio",
                label=THEMES[theme_key].get("label", theme_key),
                checked=(self.theme_var.get() == theme_key),
                command=lambda key=theme_key: self._set_theme_from_menu(key),
            )
            for theme_key in THEME_ORDER
        )
        return (
            SharedMenuItem(type="command", label="Einstellungen...", command=self._open_settings_dialog),
            SharedMenuItem(type="separator"),
            SharedMenuItem(type="submenu", label="Theme", items=theme_items),
        )

    def _menu_items_learning(self):
        items: list[SharedMenuItem] = []

        preset_items: list[SharedMenuItem] = []
        for profile_key in LEARNING_PROFILE_ORDER:
            profile = LEARNING_PROFILES.get(profile_key)
            if not profile:
                continue
            preset_items.append(
                SharedMenuItem(
                    type="radio",
                    label=str(profile.get("label", profile_key)),
                    checked=(self.learning_profile_var.get() == profile_key),
                    command=lambda key=profile_key: self._set_menu_var(
                        self.learning_profile_var,
                        key,
                        self._on_learning_profile_changed,
                    ),
                )
            )
        preset_items.append(SharedMenuItem(type="separator"))
        preset_items.append(
            SharedMenuItem(
                type="radio",
                label="Individuell (manuell)",
                checked=(self.learning_profile_var.get() == CUSTOM_PROFILE),
                command=lambda: self._set_menu_var(
                    self.learning_profile_var,
                    CUSTOM_PROFILE,
                    self._on_learning_profile_changed,
                ),
            )
        )
        items.append(SharedMenuItem(type="submenu", label="Lernprofil", items=tuple(preset_items)))
        items.append(SharedMenuItem(type="separator"))

        for profile_key in ("leicht", "mittel", "stark"):
            profile = REVIEW_PROFILES.get(profile_key)
            if not profile:
                continue
            items.append(
                SharedMenuItem(
                    type="radio",
                    label=f"Wiederholungsprofil: {profile['label']}",
                    checked=(self.review_profile_var.get() == profile_key),
                    command=lambda key=profile_key: self._set_menu_var(
                        self.review_profile_var,
                        key,
                        self._on_review_profile_changed,
                    ),
                )
            )

        items.append(SharedMenuItem(type="separator"))
        items.append(
            SharedMenuItem(
                type="radio",
                label="Gleicher Name darf direkt wiederkommen",
                checked=bool(self.allow_immediate_repeat_var.get()),
                command=lambda: self._toggle_menu_bool(self.allow_immediate_repeat_var, self._on_learning_toggles_changed),
            )
        )
        items.append(
            SharedMenuItem(
                type="radio",
                label="Fehler-Relearn priorisieren",
                checked=bool(self.prioritize_urgent_var.get()),
                command=lambda: self._toggle_menu_bool(self.prioritize_urgent_var, self._on_learning_toggles_changed),
            )
        )
        items.append(
            SharedMenuItem(
                type="radio",
                label="Neue Fotos trotz faelliger Wiederholungen beimischen",
                checked=bool(self.mix_new_cards_var.get()),
                command=lambda: self._toggle_menu_bool(self.mix_new_cards_var, self._on_learning_toggles_changed),
            )
        )

        items.append(SharedMenuItem(type="separator"))

        min_delay_items = tuple(
            SharedMenuItem(
                type="radio",
                label=("Mindest-Denkzeit: aus" if seconds == 0 else f"Mindest-Denkzeit: {seconds}s"),
                checked=(int(self.min_retrieval_seconds_var.get()) == int(seconds)),
                command=lambda secs=seconds: self._set_menu_var(
                    self.min_retrieval_seconds_var,
                    int(secs),
                    self._on_min_retrieval_changed,
                ),
            )
            for seconds in MIN_RETRIEVAL_OPTIONS
        )
        items.append(SharedMenuItem(type="submenu", label="Abrufaufwand", items=min_delay_items))

        items.append(
            SharedMenuItem(
                type="radio",
                label="Langsame richtige Antworten frueher wiederholen (laengenfair)",
                checked=bool(self.revisit_slow_correct_var.get()),
                command=lambda: self._toggle_menu_bool(self.revisit_slow_correct_var, self._on_learning_toggles_changed),
            )
        )

        slow_threshold_items = tuple(
            SharedMenuItem(
                type="radio",
                label=f"Basis-Schwelle (ca. 6 Buchstaben): >= {seconds}s",
                checked=(int(self.slow_correct_threshold_var.get()) == int(seconds)),
                command=lambda secs=seconds: self._set_menu_var(
                    self.slow_correct_threshold_var,
                    int(secs),
                    self._on_slow_correct_threshold_changed,
                ),
            )
            for seconds in SLOW_CORRECT_THRESHOLD_OPTIONS
        )
        items.append(SharedMenuItem(type="submenu", label="Langsam-richtig-Schwelle (Basis)", items=slow_threshold_items))

        feedback_items: list[SharedMenuItem] = []
        for style_key in FEEDBACK_STYLE_OPTIONS:
            label = {
                "sarkastisch": "Feedback: Sarkastisch",
                "ermutigend": "Feedback: Ermutigend",
                "neutral": "Feedback: Neutral",
            }.get(style_key, style_key)
            feedback_items.append(
                SharedMenuItem(
                    type="radio",
                    label=label,
                    checked=(self.feedback_style_var.get() == style_key),
                    command=lambda key=style_key: self._set_menu_var(
                        self.feedback_style_var,
                        key,
                        self._on_feedback_style_changed,
                    ),
                )
            )
        items.append(SharedMenuItem(type="submenu", label="Feedbackstil", items=tuple(feedback_items)))

        return tuple(items)

    def _menu_items_debug(self):
        return (
            SharedMenuItem(
                type="radio",
                label="Debug-Panel anzeigen",
                checked=bool(self.debug_show_panel_var.get()),
                command=lambda: self._toggle_menu_bool(self.debug_show_panel_var, self._on_debug_options_changed),
            ),
            SharedMenuItem(
                type="radio",
                label="Dateipfade im Debug-Panel",
                checked=bool(self.debug_show_paths_var.get()),
                command=lambda: self._toggle_menu_bool(self.debug_show_paths_var, self._on_debug_options_changed),
            ),
            SharedMenuItem(type="separator"),
            SharedMenuItem(
                type="command",
                label="Shortcut-Runtime-Debug anzeigen (Strg+Shift+D)",
                command=self._open_shortcut_runtime_debug_dialog,
            ),
            SharedMenuItem(
                type="command",
                label="Offline simulieren umschalten (Strg+Shift+O)",
                command=self._toggle_shortcut_runtime_offline,
            ),
        )

    def _menu_items_sound(self):
        volume_items = tuple(
            SharedMenuItem(
                type="radio",
                label=f"Lautstaerke {label}",
                checked=(int(self.sound_volume_var.get()) == int(value)),
                command=lambda level=value: self._set_menu_var(self.sound_volume_var, int(level), self._on_sound_volume_changed),
            )
            for value, label in ((0, "0%"), (25, "25%"), (50, "50%"), (75, "75%"), (100, "100%"))
        )
        return (
            SharedMenuItem(
                type="radio",
                label="Sound aktiv",
                checked=bool(self.sound_enabled_var.get()),
                command=lambda: self._toggle_menu_bool(self.sound_enabled_var, self._on_sound_enabled_changed),
            ),
            SharedMenuItem(type="separator"),
            SharedMenuItem(type="submenu", label="Lautstaerke", items=volume_items),
        )

    def _menu_items_seat(self):
        return (
            SharedMenuItem(
                type="radio",
                label="Level 2: Nachbarfragen nur bei korrekter Tischgruppe",
                checked=bool(self.level2_group_gate_var.get()),
                command=lambda: self._toggle_menu_bool(self.level2_group_gate_var, self._on_level2_group_gate_changed),
            ),
        )

    def _build_settings_dialog_spec(self):
        """Build shared tabbed settings schema for Namenfit runtime options."""

        if SharedSettingsDialogSpec is None or SharedSettingsSectionSpec is None or SharedSettingsFieldSpec is None:
            return None

        review_values = tuple(key for key in ("leicht", "mittel", "stark") if key in REVIEW_PROFILES) or ("mittel",)
        learning_profile_values = tuple(dict.fromkeys([*LEARNING_PROFILE_ORDER, CUSTOM_PROFILE]))
        min_retrieval_values = tuple(int(value) for value in MIN_RETRIEVAL_OPTIONS)
        slow_threshold_values = tuple(int(value) for value in SLOW_CORRECT_THRESHOLD_OPTIONS)

        return SharedSettingsDialogSpec(
            sections=(
                SharedSettingsSectionSpec(
                    key="ansicht",
                    label="Ansicht",
                    fields=(
                        SharedSettingsFieldSpec(
                            key="theme_key",
                            label="Theme",
                            field_type="enum",
                            enum_values=tuple(THEME_ORDER),
                            default=self.theme_var.get(),
                        ),
                    ),
                ),
                SharedSettingsSectionSpec(
                    key="lernen",
                    label="Lernen",
                    fields=(
                        SharedSettingsFieldSpec(
                            key="learning_profile",
                            label="Lernprofil",
                            field_type="enum",
                            enum_values=learning_profile_values,
                            default=self.learning_profile_var.get(),
                        ),
                        SharedSettingsFieldSpec(
                            key="review_profile",
                            label="Wiederholungsprofil",
                            field_type="enum",
                            enum_values=review_values,
                            default=self.review_profile_var.get(),
                        ),
                        SharedSettingsFieldSpec(
                            key="allow_immediate_repeat",
                            label="Gleicher Name darf direkt wiederkommen",
                            field_type="bool",
                            default=bool(self.allow_immediate_repeat_var.get()),
                        ),
                        SharedSettingsFieldSpec(
                            key="prioritize_urgent",
                            label="Fehler-Relearn priorisieren",
                            field_type="bool",
                            default=bool(self.prioritize_urgent_var.get()),
                        ),
                        SharedSettingsFieldSpec(
                            key="mix_new_cards",
                            label="Neue Fotos trotz faelliger Wiederholungen beimischen",
                            field_type="bool",
                            default=bool(self.mix_new_cards_var.get()),
                        ),
                        SharedSettingsFieldSpec(
                            key="min_retrieval_seconds",
                            label="Mindest-Denkzeit (Sekunden)",
                            field_type="int",
                            default=int(self.min_retrieval_seconds_var.get()),
                            min_value=min(min_retrieval_values),
                            max_value=max(min_retrieval_values),
                        ),
                        SharedSettingsFieldSpec(
                            key="revisit_slow_correct",
                            label="Langsame richtige Antworten frueher wiederholen (laengenfair)",
                            field_type="bool",
                            default=bool(self.revisit_slow_correct_var.get()),
                        ),
                        SharedSettingsFieldSpec(
                            key="slow_correct_threshold_seconds",
                            label="Langsam-richtig-Schwelle (Sekunden)",
                            field_type="int",
                            default=int(self.slow_correct_threshold_var.get()),
                            min_value=min(slow_threshold_values),
                            max_value=max(slow_threshold_values),
                        ),
                        SharedSettingsFieldSpec(
                            key="feedback_style",
                            label="Feedbackstil",
                            field_type="enum",
                            enum_values=tuple(FEEDBACK_STYLE_OPTIONS),
                            default=self.feedback_style_var.get(),
                        ),
                    ),
                ),
                SharedSettingsSectionSpec(
                    key="debug",
                    label="Debug",
                    fields=(
                        SharedSettingsFieldSpec(
                            key="debug_show_panel",
                            label="Debug-Panel anzeigen",
                            field_type="bool",
                            default=bool(self.debug_show_panel_var.get()),
                        ),
                        SharedSettingsFieldSpec(
                            key="debug_show_paths",
                            label="Dateipfade im Debug-Panel",
                            field_type="bool",
                            default=bool(self.debug_show_paths_var.get()),
                        ),
                    ),
                ),
                SharedSettingsSectionSpec(
                    key="ton",
                    label="Ton",
                    fields=(
                        SharedSettingsFieldSpec(
                            key="sound_enabled",
                            label="Sound aktiv",
                            field_type="bool",
                            default=bool(self.sound_enabled_var.get()),
                        ),
                        SharedSettingsFieldSpec(
                            key="sound_volume",
                            label="Lautstaerke (Prozent)",
                            field_type="int",
                            default=int(self.sound_volume_var.get()),
                            min_value=0,
                            max_value=100,
                        ),
                    ),
                ),
                SharedSettingsSectionSpec(
                    key="sitzplan",
                    label="Sitzplan",
                    fields=(
                        SharedSettingsFieldSpec(
                            key="level2_group_gate",
                            label="Level 2: Nachbarfragen nur bei korrekter Tischgruppe",
                            field_type="bool",
                            default=bool(self.level2_group_gate_var.get()),
                        ),
                    ),
                ),
            )
        )

    def _build_settings_dialog_values(self):
        """Return current runtime settings as shared-dialog payload."""

        return {
            "theme_key": self.theme_var.get(),
            "learning_profile": self.learning_profile_var.get(),
            "review_profile": self.review_profile_var.get(),
            "allow_immediate_repeat": bool(self.allow_immediate_repeat_var.get()),
            "prioritize_urgent": bool(self.prioritize_urgent_var.get()),
            "mix_new_cards": bool(self.mix_new_cards_var.get()),
            "min_retrieval_seconds": int(self.min_retrieval_seconds_var.get()),
            "revisit_slow_correct": bool(self.revisit_slow_correct_var.get()),
            "slow_correct_threshold_seconds": int(self.slow_correct_threshold_var.get()),
            "feedback_style": self.feedback_style_var.get(),
            "debug_show_panel": bool(self.debug_show_panel_var.get()),
            "debug_show_paths": bool(self.debug_show_paths_var.get()),
            "sound_enabled": bool(self.sound_enabled_var.get()),
            "sound_volume": int(self.sound_volume_var.get()),
            "level2_group_gate": bool(self.level2_group_gate_var.get()),
        }

    def _apply_settings_dialog_payload(self, payload):
        """Apply committed shared-dialog values back into runtime vars/controllers."""

        if not isinstance(payload, dict):
            return

        theme_key = normalize_theme_key(str(payload.get("theme_key", self.theme_var.get())))
        self.theme_var.set(theme_key)
        self._on_theme_changed()

        learning_profile = str(payload.get("learning_profile", self.learning_profile_var.get()) or CUSTOM_PROFILE)
        self.learning_profile_var.set(learning_profile)
        if learning_profile != CUSTOM_PROFILE:
            self._on_learning_profile_changed()

        review_profile = str(payload.get("review_profile", self.review_profile_var.get()) or self.review_profile_var.get())
        self.review_profile_var.set(review_profile)
        self._on_review_profile_changed()

        self.allow_immediate_repeat_var.set(bool(payload.get("allow_immediate_repeat", self.allow_immediate_repeat_var.get())))
        self.prioritize_urgent_var.set(bool(payload.get("prioritize_urgent", self.prioritize_urgent_var.get())))
        self.mix_new_cards_var.set(bool(payload.get("mix_new_cards", self.mix_new_cards_var.get())))
        self.revisit_slow_correct_var.set(bool(payload.get("revisit_slow_correct", self.revisit_slow_correct_var.get())))
        self._on_learning_toggles_changed()

        self.min_retrieval_seconds_var.set(int(payload.get("min_retrieval_seconds", self.min_retrieval_seconds_var.get())))
        self._on_min_retrieval_changed()

        self.slow_correct_threshold_var.set(
            int(payload.get("slow_correct_threshold_seconds", self.slow_correct_threshold_var.get()))
        )
        self._on_slow_correct_threshold_changed()

        self.feedback_style_var.set(str(payload.get("feedback_style", self.feedback_style_var.get()) or self.feedback_style_var.get()))
        self._on_feedback_style_changed()

        self.debug_show_panel_var.set(bool(payload.get("debug_show_panel", self.debug_show_panel_var.get())))
        self.debug_show_paths_var.set(bool(payload.get("debug_show_paths", self.debug_show_paths_var.get())))
        self._on_debug_options_changed()

        self.sound_enabled_var.set(bool(payload.get("sound_enabled", self.sound_enabled_var.get())))
        self._on_sound_enabled_changed()
        self.sound_volume_var.set(max(0, min(100, int(payload.get("sound_volume", self.sound_volume_var.get())))))
        self._on_sound_volume_changed()

        self.level2_group_gate_var.set(bool(payload.get("level2_group_gate", self.level2_group_gate_var.get())))
        self._on_level2_group_gate_changed()

    def _open_settings_dialog(self):
        """Open the shared tabbed settings dialog for runtime learning/debug/theme options."""

        if open_shared_tabbed_settings_dialog is None:
            return

        spec = self._build_settings_dialog_spec()
        if spec is None:
            return

        open_shared_tabbed_settings_dialog(
            self.root,
            title="Einstellungen",
            theme_key=self.theme_var.get(),
            spec=spec,
            initial_values=self._build_settings_dialog_values(),
            on_commit=self._apply_settings_dialog_payload,
        )

    def _build_native_menu(self):
        """Fallback-Menü für Umgebungen ohne Shared CustomMenuBar."""

        menu_bar = ui.Menu(self.root)
        view_menu = ui.Menu(menu_bar, tearoff=0)
        learning_menu = ui.Menu(menu_bar, tearoff=0)
        debug_menu = ui.Menu(menu_bar, tearoff=0)
        sound_menu = ui.Menu(menu_bar, tearoff=0)
        seat_menu = ui.Menu(menu_bar, tearoff=0)

        populate_theme_menu(view_menu, self.theme_var, self._on_theme_changed)
        view_menu.add_separator()
        view_menu.add_command(label="Einstellungen...", command=self._open_settings_dialog)

        populate_learning_menu(
            learning_menu,
            review_profile_var=self.review_profile_var,
            allow_immediate_repeat_var=self.allow_immediate_repeat_var,
            prioritize_urgent_var=self.prioritize_urgent_var,
            mix_new_cards_var=self.mix_new_cards_var,
            min_retrieval_seconds_var=self.min_retrieval_seconds_var,
            revisit_slow_correct_var=self.revisit_slow_correct_var,
            slow_correct_threshold_var=self.slow_correct_threshold_var,
            feedback_style_var=self.feedback_style_var,
            on_review_profile_changed=self._on_review_profile_changed,
            on_learning_toggles_changed=self._on_learning_toggles_changed,
            on_min_retrieval_changed=self._on_min_retrieval_changed,
            on_slow_correct_threshold_changed=self._on_slow_correct_threshold_changed,
            on_feedback_style_changed=self._on_feedback_style_changed,
            learning_profile_var=self.learning_profile_var,
            on_learning_profile_changed=self._on_learning_profile_changed,
        )

        debug_menu.add_checkbutton(
            label="Debug-Panel anzeigen",
            variable=self.debug_show_panel_var,
            command=self._on_debug_options_changed,
        )
        debug_menu.add_checkbutton(
            label="Dateipfade im Debug-Panel",
            variable=self.debug_show_paths_var,
            command=self._on_debug_options_changed,
        )
        debug_menu.add_separator()
        debug_menu.add_command(
            label="Shortcut-Runtime-Debug anzeigen",
            accelerator="Strg+Shift+D",
            command=self._open_shortcut_runtime_debug_dialog,
        )
        debug_menu.add_command(
            label="Offline simulieren umschalten",
            accelerator="Strg+Shift+O",
            command=self._toggle_shortcut_runtime_offline,
        )

        sound_menu.add_checkbutton(
            label="Sound aktiv",
            variable=self.sound_enabled_var,
            command=self._on_sound_enabled_changed,
        )
        sound_menu.add_separator()
        for value, label in ((0, "0%"), (25, "25%"), (50, "50%"), (75, "75%"), (100, "100%")):
            sound_menu.add_radiobutton(
                label=f"Lautstärke {label}",
                variable=self.sound_volume_var,
                value=value,
                command=self._on_sound_volume_changed,
            )

        seat_menu.add_checkbutton(
            label="Level 2: Nachbarfragen nur bei korrekter Tischgruppe",
            variable=self.level2_group_gate_var,
            command=self._on_level2_group_gate_changed,
        )

        menu_bar.add_cascade(label="Ansicht", menu=view_menu, underline=0)
        menu_bar.add_cascade(label="Lernen", menu=learning_menu, underline=0)
        menu_bar.add_cascade(label="Debug", menu=debug_menu, underline=0)
        menu_bar.add_cascade(label="Ton", menu=sound_menu, underline=0)
        menu_bar.add_cascade(label="Sitzplan", menu=seat_menu, underline=0)
        self.root.config(menu=menu_bar)

    def _on_theme_changed(self):
        self.theme_key = normalize_theme_key(self.theme_var.get())
        self.progress_store.set_theme_key(self.theme_key)
        if callable(self.on_theme_changed_callback):
            self.on_theme_changed_callback(self.theme_key)
        if self._shared_menu_bar is not None:
            self._shared_menu_bar.refresh_theme(self.theme_key)
        for tooltip in self._hover_tooltips:
            try:
                setattr(tooltip, "theme_key", self.theme_key)
            except Exception:
                continue
        self._apply_theme()

    def _on_review_profile_changed(self):
        profile_key = self.review_profile_var.get()
        self.progress_store.set_review_profile(profile_key)
        self.learning_profile_var.set(self.progress_store.get_learning_profile_key())
        self._notify_learning_settings_changed()

    def _on_learning_profile_changed(self):
        profile_key = self.learning_profile_var.get()
        if profile_key == CUSTOM_PROFILE:
            return

        self.progress_store.apply_learning_profile(profile_key)
        self._sync_learning_menu_vars()
        self._notify_learning_settings_changed()

    def _sync_learning_menu_vars(self):
        self.learning_profile_var.set(self.progress_store.get_learning_profile_key())
        self.review_profile_var.set(self.progress_store.get_review_profile())
        self.allow_immediate_repeat_var.set(self.progress_store.get_allow_immediate_repeat())
        self.prioritize_urgent_var.set(self.progress_store.get_prioritize_urgent_repeats())
        self.mix_new_cards_var.set(self.progress_store.get_mix_new_cards())
        self.min_retrieval_seconds_var.set(self.progress_store.get_min_retrieval_seconds())
        self.revisit_slow_correct_var.set(self.progress_store.get_revisit_slow_correct())
        self.slow_correct_threshold_var.set(self.progress_store.get_slow_correct_threshold_seconds())
        self.feedback_style_var.set(self.progress_store.get_feedback_style())

    def _on_learning_toggles_changed(self):
        self.progress_store.set_allow_immediate_repeat(self.allow_immediate_repeat_var.get())
        self.progress_store.set_prioritize_urgent_repeats(self.prioritize_urgent_var.get())
        self.progress_store.set_mix_new_cards(self.mix_new_cards_var.get())
        self.progress_store.set_revisit_slow_correct(self.revisit_slow_correct_var.get())
        self.learning_profile_var.set(self.progress_store.get_learning_profile_key())
        self._notify_learning_settings_changed()

    def _on_min_retrieval_changed(self):
        self.progress_store.set_min_retrieval_seconds(self.min_retrieval_seconds_var.get())
        self.learning_profile_var.set(self.progress_store.get_learning_profile_key())
        self._notify_learning_settings_changed()

    def _on_slow_correct_threshold_changed(self):
        self.progress_store.set_slow_correct_threshold_seconds(self.slow_correct_threshold_var.get())
        self.learning_profile_var.set(self.progress_store.get_learning_profile_key())
        self._notify_learning_settings_changed()

    def _on_feedback_style_changed(self):
        self.progress_store.set_feedback_style(self.feedback_style_var.get())
        self.learning_profile_var.set(self.progress_store.get_learning_profile_key())
        self._notify_learning_settings_changed()

    def _notify_learning_settings_changed(self):
        if callable(self.on_learning_settings_changed_callback):
            self.on_learning_settings_changed_callback(self.progress_store.get_learning_settings())

    def _on_debug_options_changed(self):
        self.debug_options["show_debug_panel"] = bool(self.debug_show_panel_var.get())
        self.debug_options["show_paths"] = bool(self.debug_show_paths_var.get())
        if callable(self.on_debug_options_changed_callback):
            self.on_debug_options_changed_callback(dict(self.debug_options))
        self._refresh_debug_panel()

    def _notify_sound_options_changed(self):
        if callable(self.on_sound_options_changed_callback):
            self.on_sound_options_changed_callback(
                {
                    "enabled": bool(self.sound_enabled),
                    "volume": int(self.sound_volume),
                }
            )

    def _on_sound_enabled_changed(self):
        self.sound_enabled = bool(self.sound_enabled_var.get())
        self._notify_sound_options_changed()

    def _on_sound_volume_changed(self):
        self.sound_volume = max(0, min(100, int(self.sound_volume_var.get())))
        self._notify_sound_options_changed()

    def _on_level2_group_gate_changed(self):
        self.level2_require_group_before_neighbors = bool(self.level2_group_gate_var.get())
        if callable(self.on_level2_setting_changed_callback):
            self.on_level2_setting_changed_callback(self.level2_require_group_before_neighbors)

    def _refresh_debug_panel(self):
        if not self.debug_options.get("show_debug_panel", False):
            self.debug_label.config(text="")
            return

        parts = [
            f"Mode: {self.mode}",
            f"Level: {self.level}",
            f"Lernprofil: {self.progress_store.get_learning_profile_key()}",
            f"Prompt: {int(self.progress_store.data.get('prompt_counter', 0))}",
        ]
        if self.debug_options.get("show_paths", False):
            parts.append(f"Log: {self.progress_store.log_path}")
        self.debug_label.config(text=" | ".join(parts))

    def _require_min_retrieval_delay(self):
        """Sichert einen minimalen Abrufaufwand vor Auflösung (desirable difficulty)."""

        minimum = int(self.progress_store.get_min_retrieval_seconds())
        if minimum <= 0:
            return True

        elapsed = perf_counter() - self.phase_start_time
        if elapsed >= float(minimum):
            return True

        remaining = max(0.0, float(minimum) - float(elapsed))
        self.result_label.config(text=f"⏳ Erst erinnern, dann auflösen ({remaining:.1f}s verbleiben).")
        return False

    def _apply_theme(self):
        """Wendet das aktuell gewählte Theme auf alle Widgets an."""

        theme = get_theme(self.theme_key)
        apply_window_theme(self.root, self.theme_key)

        self.photo_label.configure(bg=theme["bg_main"])
        self.prompt_label.configure(bg=theme["bg_main"], fg=theme["fg_primary"])
        self.result_label.configure(bg=theme["bg_main"], fg=theme["fg_primary"])

        self.name_label.configure(bg=theme["bg_main"], fg=theme["fg_primary"])
        self.group_label.configure(bg=theme["bg_main"], fg=theme["fg_primary"])
        self.level2_frame.configure(bg=theme["bg_main"])
        self.behind_label.configure(bg=theme["bg_main"], fg=theme["fg_primary"])
        self.opposite_label.configure(bg=theme["bg_main"], fg=theme["fg_primary"])
        self.front_label.configure(bg=theme["bg_main"], fg=theme["fg_primary"])

        self.stats_label.configure(bg=theme["bg_main"], fg=theme["fg_muted"])
        self.aggregate_stats_label.configure(bg=theme["bg_main"], fg=theme["fg_muted"])
        self.feedback_label.configure(bg=theme["bg_main"], fg=theme["fg_primary"])
        self.debug_label.configure(bg=theme["bg_main"], fg=theme["fg_muted"])

        style_entry(self.name_entry, self.theme_key)
        style_entry(self.group_entry, self.theme_key)
        style_entry(self.behind_entry, self.theme_key)
        style_entry(self.opposite_entry, self.theme_key)
        style_entry(self.front_entry, self.theme_key)

        style_primary_button(self.solve_button, self.theme_key)
        style_primary_button(self.next_button, self.theme_key)
        style_secondary_button(self.typo_button, self.theme_key)
        style_secondary_button(self.switch_level_button, self.theme_key)

    def _build_widgets(self):
        """Erstellt das UI in logisch getrennten Blöcken."""

        # Foto-Anzeige (für Foto-Modi)
        self.photo_label = ui.Label(self.root, bg=BG_MAIN)
        # Initial nicht gepackt, wird in _apply_level_widgets gezeigt

        self.prompt_label = ui.Label(self.root, text="", font=("Arial", 18), bg=BG_MAIN, fg=FG_PRIMARY)
        self.prompt_label.pack(pady=10)

        self.result_label = ui.Label(self.root, text="", font=("Arial", 12), bg=BG_MAIN, fg=FG_PRIMARY)
        self.result_label.pack(pady=(0, 8))

        # Name-Eingabe (für Foto-Modi)
        self.name_label = ui.Label(self.root, text="Name:", font=("Arial", 12), bg=BG_MAIN, fg=FG_PRIMARY)
        self.name_entry = ui.Entry(self.root, font=("Arial", 14))
        style_entry(self.name_entry, self.theme_key)

        self.group_label = ui.Label(
            self.root,
            text=f"{self._group_term()}:",
            font=("Arial", 12),
            bg=BG_MAIN,
            fg=FG_PRIMARY,
        )
        self.group_label.pack()
        self.group_entry = ui.Entry(self.root, font=("Arial", 14))
        style_entry(self.group_entry, self.theme_key)
        self.group_entry.pack(pady=(0, 8))

        self.level2_frame = ui.Frame(self.root, bg=BG_MAIN)
        self.level2_frame.pack(pady=(0, 8))

        self.behind_label = ui.Label(self.level2_frame, text="Dahinter:", font=("Arial", 12), bg=BG_MAIN, fg=FG_PRIMARY)
        self.behind_entry = ui.Entry(self.level2_frame, font=("Arial", 14))
        style_entry(self.behind_entry, self.theme_key)
        self.opposite_label = ui.Label(self.level2_frame, text="Gegenüber:", font=("Arial", 12), bg=BG_MAIN, fg=FG_PRIMARY)
        self.opposite_entry = ui.Entry(self.level2_frame, font=("Arial", 14))
        style_entry(self.opposite_entry, self.theme_key)
        self.front_label = ui.Label(self.level2_frame, text="Davor:", font=("Arial", 12), bg=BG_MAIN, fg=FG_PRIMARY)
        self.front_entry = ui.Entry(self.level2_frame, font=("Arial", 14))
        style_entry(self.front_entry, self.theme_key)

        self.solve_button = ui.Button(self.root, text="Auflösen", command=self.solve)
        style_primary_button(self.solve_button, self.theme_key)
        self.solve_button.pack(pady=(2, 2))
        self._attach_hover_help(self.solve_button, label="Aktuelle Aufgabe aufloesen", shortcut="Enter")

        self.typo_button = ui.Button(
            self.root,
            text="Ups, vertippt",
            command=self.mark_name_typo,
        )
        style_secondary_button(self.typo_button, self.theme_key)
        self.typo_button.pack(pady=(0, 4))
        self.typo_button.pack_forget()
        self._attach_hover_help(self.typo_button, label="Vertipper markieren", shortcut="Backspace")

        self.next_button = ui.Button(self.root, text="Weiter", command=self.next_person)
        style_primary_button(self.next_button, self.theme_key)
        self.next_button.pack(pady=5)
        self.next_button.pack_forget()
        self._attach_hover_help(self.next_button, label="Naechste Person laden", shortcut="Enter")

        self.switch_level_button = ui.Button(
            self.root,
            text="Level wechseln",
            command=self.switch_level,
        )
        style_secondary_button(self.switch_level_button, self.theme_key)
        self.switch_level_button.pack(pady=(2, 6))
        self._attach_hover_help(self.switch_level_button, label="Trainingslevel wechseln", shortcut=None)

        self.stats_label = ui.Label(self.root, text="", font=("Arial", 10), fg=FG_MUTED, bg=BG_MAIN)
        self.stats_label.pack(pady=(0, 8))

        self.aggregate_stats_label = ui.Label(self.root, text="", font=("Arial", 9), fg=FG_MUTED, bg=BG_MAIN)
        self.aggregate_stats_label.pack(pady=(0, 8))

        self.feedback_label = ui.Label(self.root, text="", font=("Arial", 9, "bold"), fg=FG_PRIMARY, bg=BG_MAIN)
        self.feedback_label.pack(pady=(6, 8))

        self.debug_label = ui.Label(self.root, text="", font=("Arial", 8), fg=FG_MUTED, bg=BG_MAIN)
        self.debug_label.pack(pady=(0, 6))

    def _bind_shortcuts(self):
        """Bindet Enter/Leertaste an die jeweils passende Aktion."""

        self._bind_runtime_shortcut(
            "<Return>",
            self._on_enter,
            binding_id="global.enter",
            intent=UiIntent.QUIZ_ENTER,
            modes=(UI_MODE_GLOBAL, UI_MODE_DIALOG),
            allow_when_text_input=True,
        )
        self._bind_runtime_shortcut(
            "<KP_Enter>",
            self._on_enter,
            binding_id="global.enter.numpad",
            intent=UiIntent.QUIZ_ENTER_NUMPAD,
            modes=(UI_MODE_GLOBAL, UI_MODE_DIALOG),
            allow_when_text_input=True,
        )
        self._bind_runtime_shortcut(
            "<space>",
            self._on_space,
            binding_id="global.space",
            intent=UiIntent.QUIZ_SPACE,
            modes=(UI_MODE_GLOBAL, UI_MODE_DIALOG),
            allow_when_text_input=False,
        )
        self._bind_runtime_shortcut(
            "<BackSpace>",
            self._on_backspace,
            binding_id="global.backspace",
            intent=UiIntent.QUIZ_TYPO,
            modes=(UI_MODE_GLOBAL, UI_MODE_DIALOG),
            allow_when_text_input=True,
        )
        self._bind_runtime_shortcut(
            "<Alt-s>",
            self._on_alt_s,
            binding_id="global.alt-s",
            intent=UiIntent.SETTINGS_TOGGLE_GROUP_GATE,
            modes=(UI_MODE_GLOBAL, UI_MODE_DIALOG),
            allow_when_text_input=True,
        )
        self._bind_runtime_shortcut(
            "<Alt-S>",
            self._on_alt_s,
            binding_id="global.alt-s.upper",
            intent=UiIntent.SETTINGS_TOGGLE_GROUP_GATE_UPPER,
            modes=(UI_MODE_GLOBAL, UI_MODE_DIALOG),
            allow_when_text_input=True,
        )
        self._bind_runtime_shortcut(
            "<Control-Shift-d>",
            lambda _event: self._open_shortcut_runtime_debug_dialog(),
            binding_id="debug.runtime-overlay",
            intent=UiIntent.DEBUG_RUNTIME_OVERLAY,
            modes=(UI_MODE_GLOBAL, UI_MODE_DIALOG),
            allow_when_text_input=True,
        )
        self._bind_runtime_shortcut(
            "<Control-Shift-o>",
            lambda _event: self._toggle_shortcut_runtime_offline(),
            binding_id="debug.runtime-offline",
            intent=UiIntent.DEBUG_RUNTIME_OFFLINE,
            modes=(UI_MODE_GLOBAL, UI_MODE_DIALOG),
            allow_when_text_input=True,
        )
        self._bind_runtime_shortcut(
            "<Escape>",
            self._on_escape_runtime,
            binding_id="global.escape",
            intent=UiIntent.GLOBAL_ESCAPE,
            modes=(UI_MODE_GLOBAL, UI_MODE_DIALOG),
            allow_when_text_input=True,
        )

    @staticmethod
    def _is_editable_widget(widget):
        if widget is None:
            return False
        return isinstance(widget, (ui.Entry, ui.Text, ui.Spinbox, widgets.Entry, widgets.Combobox))

    def _track_popup_window(self, window, *, policy_id="dialog.modal"):
        popup_id = str(window)
        if popup_id in self._tracked_popup_ids:
            return
        self._popup_registry.open_popup(popup_id=popup_id, title=str(window.title() or ""), policy_id=policy_id)
        self._tracked_popup_ids.add(popup_id)

    def _sync_popup_sessions_from_windows(self):
        visible_popup_ids = set()
        for child in self.root.winfo_children():
            if not isinstance(child, ui.Toplevel):
                continue
            try:
                if not int(child.winfo_exists()):
                    continue
                if str(child.state()).lower() == "withdrawn":
                    continue
            except Exception:
                continue

            popup_id = str(child)
            visible_popup_ids.add(popup_id)
            if popup_id in self._tracked_popup_ids:
                continue
            self._popup_registry.open_popup(popup_id=popup_id, title=str(child.title() or ""), policy_id="dialog.modal")
            self._tracked_popup_ids.add(popup_id)

        stale_ids = self._tracked_popup_ids - visible_popup_ids
        for popup_id in tuple(stale_ids):
            self._popup_registry.close_popup(popup_id)
            self._tracked_popup_ids.discard(popup_id)

    def _build_runtime_context(self, event=None):
        self._sync_popup_sessions_from_windows()
        focused_widget = getattr(event, "widget", None) or self.root.focus_get()
        text_input_focused = self._is_editable_widget(focused_widget)
        dialog_open = self._popup_registry.has_mode_blocking_popup()
        offline = bool(self._shortcut_debug_offline)

        if offline:
            active_mode = UI_MODE_OFFLINE
        elif dialog_open:
            active_mode = UI_MODE_DIALOG
        elif text_input_focused:
            active_mode = UI_MODE_EDITOR
        else:
            active_mode = UI_MODE_GLOBAL

        return KeybindingRuntimeContext(
            active_mode=active_mode,
            offline=offline,
            text_input_focused=text_input_focused,
            dialog_open=dialog_open,
        )

    def _register_runtime_shortcut(
        self,
        *,
        binding_id,
        sequence,
        intent,
        modes,
        allow_when_text_input,
        allow_when_offline=True,
    ):
        intent_ok, _intent_reason = self._hsm_contract.validate_intent(intent)
        if not intent_ok:
            raise ValueError(f"Unknown runtime shortcut intent: {intent}")

        definition = KeyBindingDefinition(
            binding_id=binding_id,
            sequence=sequence,
            intent=intent,
            modes=modes,
            allow_when_text_input=allow_when_text_input,
            allow_when_offline=allow_when_offline,
        )
        self._runtime_shortcuts.register(definition)
        return definition

    def _bind_runtime_shortcut(
        self,
        sequence,
        handler,
        *,
        binding_id,
        intent,
        modes,
        allow_when_text_input=False,
        allow_when_offline=True,
    ):
        definition = self._register_runtime_shortcut(
            binding_id=binding_id,
            sequence=sequence,
            intent=intent,
            modes=modes,
            allow_when_text_input=allow_when_text_input,
            allow_when_offline=allow_when_offline,
        )

        def _wrapped(event):
            context = self._build_runtime_context(event)
            can_execute, _reason = self._runtime_shortcuts.evaluate_runtime(definition, context)
            if not can_execute:
                return None
            return handler(event)

        self.root.bind(sequence, _wrapped)

    def _close_active_popup_on_escape(self):
        self._sync_popup_sessions_from_windows()
        active_popup = self._popup_registry.active_popup()
        if active_popup is None:
            return False
        popup_id = active_popup.popup_id
        for child in self.root.winfo_children():
            if not isinstance(child, ui.Toplevel):
                continue
            if str(child) != popup_id:
                continue
            try:
                child.destroy()
            except Exception:
                pass
            break
        self._popup_registry.close_popup(popup_id)
        self._tracked_popup_ids.discard(popup_id)
        return True

    def _on_escape_runtime(self, _event=None):
        focused = self.root.focus_get()
        action = self._hsm_contract.resolve_escape_action(
            has_popup=self._popup_registry.has_active_popup(),
            has_inline_editor=self._is_editable_widget(focused),
            has_parent_state=False,
        )
        if action == ESCAPE_CLOSE_POPUP and self._close_active_popup_on_escape():
            return "break"
        if action == ESCAPE_EXIT_INLINE_EDITOR:
            self.root.focus_set()
            return "break"
        return "break"

    def _toggle_shortcut_runtime_offline(self):
        self._shortcut_debug_offline = not bool(self._shortcut_debug_offline)
        if self._shortcut_runtime_debug_offline_var is not None:
            self._shortcut_runtime_debug_offline_var.set(bool(self._shortcut_debug_offline))
        self._refresh_shortcut_runtime_debug_dialog()

    def _on_shortcut_runtime_offline_var_changed(self):
        if self._shortcut_runtime_debug_offline_var is not None:
            self._shortcut_debug_offline = bool(self._shortcut_runtime_debug_offline_var.get())
        self._refresh_shortcut_runtime_debug_dialog()

    def _open_shortcut_runtime_debug_dialog(self):
        existing = self._shortcut_runtime_debug_window
        if existing is not None and int(existing.winfo_exists()):
            self._refresh_shortcut_runtime_debug_dialog()
            existing.deiconify()
            existing.lift()
            existing.focus_force()
            return

        window = ui.Toplevel(self.root)
        window.title("Shortcut Runtime Debug")
        window.geometry("980x520")
        window.minsize(820, 420)
        self._track_popup_window(window, policy_id="dialog.non_blocking")

        self._shortcut_runtime_debug_context_var = ui.StringVar(master=window, value="")
        self._shortcut_runtime_debug_summary_var = ui.StringVar(master=window, value="")
        self._shortcut_runtime_debug_offline_var = ui.BooleanVar(master=window, value=bool(self._shortcut_debug_offline))

        toolbar = widgets.Frame(window, padding=(10, 8))
        toolbar.pack(fill="x")
        widgets.Label(toolbar, textvariable=self._shortcut_runtime_debug_context_var).pack(side="left", fill="x", expand=True)
        widgets.Checkbutton(
            toolbar,
            text="Offline simulieren",
            variable=self._shortcut_runtime_debug_offline_var,
            command=self._on_shortcut_runtime_offline_var_changed,
        ).pack(side="left", padx=(12, 0))
        widgets.Button(toolbar, text="Aktualisieren", command=self._refresh_shortcut_runtime_debug_dialog).pack(side="left", padx=(8, 0))

        body = widgets.Frame(window, padding=(10, 0, 10, 8))
        body.pack(fill="both", expand=True)
        columns = ("mode", "key", "binding", "status", "reason")
        table = widgets.Treeview(body, columns=columns, show="headings")
        table.heading("mode", text="Mode")
        table.heading("key", text="Key")
        table.heading("binding", text="Binding")
        table.heading("status", text="Status")
        table.heading("reason", text="Reason")
        table.column("mode", width=100, anchor="center", stretch=False)
        table.column("key", width=130, anchor="center", stretch=False)
        table.column("binding", width=300, anchor="w", stretch=True)
        table.column("status", width=90, anchor="center", stretch=False)
        table.column("reason", width=180, anchor="w", stretch=True)
        table.pack(side="left", fill="both", expand=True)
        y_scroll = widgets.Scrollbar(body, orient="vertical", command=table.yview)
        y_scroll.pack(side="right", fill="y")
        table.configure(yscrollcommand=y_scroll.set)

        widgets.Label(window, textvariable=self._shortcut_runtime_debug_summary_var).pack(fill="x", padx=10, pady=(0, 8))

        self._shortcut_runtime_debug_window = window
        self._shortcut_runtime_debug_table = table
        window.protocol("WM_DELETE_WINDOW", self._close_shortcut_runtime_debug_dialog)
        self._refresh_shortcut_runtime_debug_dialog()

    def _close_shortcut_runtime_debug_dialog(self):
        if self._shortcut_runtime_debug_window is not None and int(self._shortcut_runtime_debug_window.winfo_exists()):
            popup_id = str(self._shortcut_runtime_debug_window)
            self._popup_registry.close_popup(popup_id)
            self._tracked_popup_ids.discard(popup_id)
            self._shortcut_runtime_debug_window.destroy()
        self._shortcut_runtime_debug_window = None
        self._shortcut_runtime_debug_table = None
        self._shortcut_runtime_debug_context_var = None
        self._shortcut_runtime_debug_summary_var = None
        self._shortcut_runtime_debug_offline_var = None

    def _refresh_shortcut_runtime_debug_dialog(self):
        table = self._shortcut_runtime_debug_table
        if table is None:
            return

        context = self._build_runtime_context()
        if self._shortcut_runtime_debug_context_var is not None:
            self._shortcut_runtime_debug_context_var.set(
                f"mode={context.active_mode} | offline={context.offline} | dialog={context.dialog_open} | text-focus={context.text_input_focused}"
            )

        for item_id in table.get_children(""):
            table.delete(item_id)

        active_count = 0
        disabled_count = 0
        for mode in (UI_MODE_GLOBAL, UI_MODE_EDITOR, UI_MODE_DIALOG, UI_MODE_OFFLINE):
            for definition in self._runtime_shortcuts.all():
                if mode not in definition.modes and UI_MODE_GLOBAL not in definition.modes:
                    continue
                can_execute, reason = self._runtime_shortcuts.evaluate_runtime(
                    definition,
                    context,
                    active_mode_override=mode,
                )
                status = "active" if can_execute else "disabled"
                if can_execute:
                    active_count += 1
                else:
                    disabled_count += 1
                table.insert(
                    "",
                    "end",
                    values=(mode, definition.sequence, definition.binding_id, status, "" if can_execute else reason),
                )

        total = active_count + disabled_count
        if self._shortcut_runtime_debug_summary_var is not None:
            self._shortcut_runtime_debug_summary_var.set(
                f"Bindings: {total} total | {active_count} active | {disabled_count} disabled"
            )

    def _on_alt_s(self, _event):
        self.level2_group_gate_var.set(not self.level2_group_gate_var.get())
        self._on_level2_group_gate_changed()
        return "break"

    def _apply_level_widgets(self):
        """Zeigt/versteckt Widgets passend zum aktuellen Level und Modus."""

        # Foto-spezifische Widgets
        has_photos = self.mode in (MODE_PHOTO, MODE_COMBINED)

        if has_photos:
            if not self.photo_label.winfo_manager():
                self.photo_label.pack(before=self.prompt_label, pady=10)
            if not self.name_label.winfo_manager():
                self.name_label.pack(before=self.group_label)
            if not self.name_entry.winfo_manager():
                self.name_entry.pack(before=self.group_label, pady=(0, 8))
        else:
            self.photo_label.pack_forget()
            self.name_label.pack_forget()
            self.name_entry.pack_forget()

        # Lerngruppen-Widget in allen Modi sichtbar
        has_csv = self.mode in (MODE_CSV, MODE_COMBINED)
        has_group = self.ask_group_question

        if has_group:
            if not self.group_label.winfo_manager():
                self.group_label.pack()
            if not self.group_entry.winfo_manager():
                self.group_entry.pack(pady=(0, 8))
        else:
            self.group_label.pack_forget()
            self.group_entry.pack_forget()

        # Level-Wechsel-Button nur bei CSV-Modi
        if has_csv:
            if not self.switch_level_button.winfo_manager():
                self.switch_level_button.pack(pady=(2, 6))
        else:
            self.switch_level_button.pack_forget()

        # Level-2-Felder
        if has_csv and self.level == LEVEL_2:
            if not self.behind_label.winfo_manager():
                self.behind_label.pack()
            if not self.behind_entry.winfo_manager():
                self.behind_entry.pack(pady=(0, 6))
            if not self.opposite_label.winfo_manager():
                self.opposite_label.pack()
            if not self.opposite_entry.winfo_manager():
                self.opposite_entry.pack(pady=(0, 6))
            if not self.front_label.winfo_manager():
                self.front_label.pack()
            if not self.front_entry.winfo_manager():
                self.front_entry.pack(pady=(0, 8))
            return

        self.behind_label.pack_forget()
        self.behind_entry.pack_forget()
        self.front_label.pack_forget()
        self.front_entry.pack_forget()
        self.opposite_label.pack_forget()
        self.opposite_entry.pack_forget()

    def _show_action_button(self):
        """Zeigt genau einen Aktionsbutton gemäß aktuellem UI-Zustand."""

        if self.round_finished:
            self.typo_button.pack_forget()
            self.solve_button.pack_forget()
            self.next_button.config(text="Zurück zum Startdialog")
            self.next_button.pack(pady=5)
            return

        if self.name_typo_available:
            if self.name_typo_field == "group":
                self.typo_button.config(text=f"Ups, {self._group_term()} vertippt")
            elif self.name_typo_field == "behind":
                self.typo_button.config(text="Ups, Dahinter vertippt")
            elif self.name_typo_field == "opposite":
                self.typo_button.config(text="Ups, Gegenüber vertippt")
            elif self.name_typo_field == "front":
                self.typo_button.config(text="Ups, Davor vertippt")
            else:
                self.typo_button.config(text="Ups, Name vertippt")
            self.typo_button.pack(pady=(0, 4))
        else:
            self.typo_button.pack_forget()

        if self.awaiting_solution:
            self.next_button.pack_forget()
            self.next_button.config(text="Weiter")
            self.solve_button.pack(pady=(2, 2))
            return

        self.solve_button.pack_forget()
        self.next_button.config(text="Weiter")
        self.next_button.pack(pady=5)

    def _on_enter(self, _event):
        """Enter löst die aktuelle Aufgabe auf (nur im Lösungsmodus)."""

        if self.round_finished:
            self._close_round_and_return_to_start()
            return "break"

        if self.awaiting_solution:
            self.solve()
            return "break"
        return None

    def _on_space(self, _event):
        """Leertaste springt weiter (nur nach Auflösung)."""

        if self.round_finished:
            self._close_round_and_return_to_start()
            return "break"

        if not self.awaiting_solution:
            self.next_person()
            return "break"
        return None

    def _on_backspace(self, _event):
        """Backspace triggert die Vertipper-Korrektur als schnellen Reset."""

        if self.name_typo_available:
            self.mark_name_typo()
            return "break"
        return None

    def _set_typo_option(self, phase, field):
        self.name_typo_available = True
        self.name_typo_phase = phase
        self.name_typo_field = field

    def _clear_typo_option(self):
        self.name_typo_available = False
        self.name_typo_phase = None
        self.name_typo_field = None

    def _record_prompt_completion(self, success, confused_with=None):
        self.current_prompt_completed = True
        self.current_prompt_success = bool(success)
        self.current_prompt_confused_with = confused_with if confused_with else None

    def _play_feedback_sound(self, success):
        if not self.sound_enabled or winsound is None or self.sound_volume <= 0:
            return

        amplitude = int(32767 * (self.sound_volume / 100.0))
        sample_rate = 22050
        duration_ms = 160
        total_samples = int(sample_rate * (duration_ms / 1000.0))
        frequencies = (920, 1240) if success else (340, 220)

        buffer = BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for idx in range(total_samples):
                t = idx / sample_rate
                freq = frequencies[0] if idx < total_samples // 2 else frequencies[1]
                sample = int(amplitude * math.sin(2 * math.pi * freq * t))
                wav_file.writeframes(struct.pack("<h", sample))

        try:
            winsound.PlaySound(buffer.getvalue(), winsound.SND_MEMORY | winsound.SND_ASYNC)
        except RuntimeError:
            pass

    def _set_result_neutral_style(self):
        theme = get_theme(self.theme_key)
        self.result_label.config(fg=theme["fg_primary"])

    def _show_verdict(self, success):
        theme = get_theme(self.theme_key)
        if success:
            self.result_label.config(fg=theme.get("success", "#1F8F3A"))
        else:
            self.result_label.config(fg=theme.get("error", theme.get("danger", "#B00020")))
        self._play_feedback_sound(success)

    def _consume_completed_prompt(self):
        if not self.current_prompt_completed or not self.current_name:
            return

        person_key = self.current_name
        stats = self.session_prompt_results.setdefault(person_key, {"shown": 0, "correct": 0, "wrong": 0})
        stats["shown"] += 1
        if self.current_prompt_success:
            stats["correct"] += 1
        else:
            stats["wrong"] += 1

        self.session_seen_names.add(person_key)
        if self.current_prompt_confused_with:
            confused_with = self.current_prompt_confused_with
            self.session_confusions[confused_with] = int(self.session_confusions.get(confused_with, 0)) + 1

        self.completed_prompts += 1
        self.current_prompt_completed = False
        self.current_prompt_success = False
        self.current_prompt_confused_with = None

    def _round_progress_prefix(self):
        if self.prompt_limit is None:
            return f"Runde: {self.completed_prompts} / ∞"

        remaining = max(0, self.prompt_limit - self.completed_prompts)
        return f"Runde: {self.completed_prompts}/{self.prompt_limit} · Rest: {remaining}"

    def _is_round_limit_reached(self):
        if self.prompt_limit is None:
            return False
        return self.completed_prompts >= self.prompt_limit

    def _person_label_for_key(self, key):
        info = self.people.get(key)
        if info and getattr(info, "name", None):
            return info.name
        return key

    def _top_session_persons(self, *, metric, limit=3):
        rows = []
        for key, values in self.session_prompt_results.items():
            shown = int(values.get("shown", 0))
            if shown <= 0:
                continue
            correct = int(values.get("correct", 0))
            wrong = int(values.get("wrong", 0))
            counter = correct if metric == "correct" else wrong
            if counter <= 0:
                continue
            rows.append((counter, shown, self._person_label_for_key(key), correct, wrong))

        rows.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
        return rows[:limit]

    def _build_round_summary_text(self):
        total = self.completed_prompts
        correct = sum(int(v.get("correct", 0)) for v in self.session_prompt_results.values())
        wrong = total - correct
        unique_count = len(self.session_seen_names)

        lines = [
            f"Prompts gespielt: {total}",
            f"Richtig/Falsch: {correct}/{wrong}",
            f"Verschiedene Personen gesehen: {unique_count}",
        ]

        best_rows = self._top_session_persons(metric="correct", limit=3)
        if best_rows:
            best_text = ", ".join(f"{name} ({ok}/{shown})" for _, shown, name, ok, _ in best_rows)
            lines.append(f"Besonders sicher: {best_text}")

        weak_rows = self._top_session_persons(metric="wrong", limit=3)
        if weak_rows:
            weak_text = ", ".join(f"{name} ({wrong}/{shown})" for _, shown, name, _, wrong in weak_rows)
            lines.append(f"Besonders unsicher: {weak_text}")

        if self.session_confusions:
            confusions = sorted(self.session_confusions.items(), key=lambda item: item[1], reverse=True)[:3]
            confusion_text = ", ".join(f"{name} ({count}×)" for name, count in confusions)
            lines.append(f"Am meisten verwechselt mit: {confusion_text}")

        return "\n".join(lines)

    def _show_round_summary_screen(self):
        self.round_finished = True
        self.awaiting_solution = False

        self.photo_label.config(image="", text="")
        self.photo_label.pack_forget()
        self.name_label.pack_forget()
        self.name_entry.pack_forget()
        self.group_label.pack_forget()
        self.group_entry.pack_forget()
        self.level2_frame.pack_forget()
        self.switch_level_button.pack_forget()
        self.stats_label.pack_forget()
        self.aggregate_stats_label.pack_forget()
        self.debug_label.pack_forget()

        self.name_entry.configure(state="disabled")
        self.group_entry.configure(state="disabled")
        self.behind_entry.configure(state="disabled")
        self.front_entry.configure(state="disabled")
        self.opposite_entry.configure(state="disabled")

        self.prompt_label.config(text="🏁 Runde beendet")
        self.result_label.config(text=self._build_round_summary_text())
        self._set_result_neutral_style()
        self.feedback_label.config(text="Leertaste/Enter: zurück zum Startdialog")
        self._clear_typo_option()
        self._show_action_button()

    def _close_round_and_return_to_start(self):
        try:
            self.root.quit()
        finally:
            self.root.destroy()

    def _focus_entry_for_phase(self, phase):
        if phase == PHASE_NAME:
            self.name_entry.focus_set()
            return
        if phase == PHASE_GROUP:
            self.group_entry.focus_set()
            return
        if phase == PHASE_NEIGHBORS:
            self.behind_entry.focus_set()

    def _entry_for_field(self, field):
        if field == "name":
            return self.name_entry
        if field == "group":
            return self.group_entry
        if field == "behind":
            return self.behind_entry
        if field == "front":
            return self.front_entry
        if field == "opposite":
            return self.opposite_entry
        return None

    def _first_wrong_neighbor_field(self, behind_ok, front_ok, opposite_ok):
        if not behind_ok:
            return "behind"
        if not opposite_ok:
            return "opposite"
        if not front_ok:
            return "front"
        return None

    def _preview_name_confusion(self, guessed_name):
        confused_key = self._find_confused_person_key(guessed_name)
        if not confused_key:
            return None
        return self._display_name_for_key(confused_key)

    def _apply_name_confusion_penalty_if_needed(self, level):
        name_result = self.phase_results.get(PHASE_NAME, {})
        if bool(name_result.get("name", False)):
            return
        if bool(name_result.get("confusion_penalized", False)):
            return

        guessed_name = str(name_result.get("guess_name", "")).strip()
        if guessed_name:
            confused_with = self._apply_name_confusion_penalty(guessed_name, level)
            if confused_with and not name_result.get("confused_with"):
                name_result["confused_with"] = confused_with

        name_result["confusion_penalized"] = True

    def switch_level(self):
        """Erlaubt den Wechsel der Schwierigkeit während des Spiels."""

        selected = ask_level(self.root, current_level=self.level)
        if selected not in (LEVEL_1, LEVEL_2) or selected == self.level:
            return

        self.level = selected

        # Titel entsprechend Modus aktualisieren
        title_parts = []
        if self.mode == MODE_COMBINED:
            title_parts.append("Kombi-Modus")
        elif self.mode == MODE_CSV:
            title_parts.append("CSV-Modus")
        title_parts.append(f"Level {selected}")
        self.root.title(f"Namens-Trainer ({' · '.join(title_parts)})")

        self._apply_level_widgets()

        self.awaiting_solution = True
        self.result_label.config(text=f"Level gewechselt zu {selected}.")
        self.feedback_label.config(text="")
        self.next_person()

    def _pick_next_name(self):
        """Wählt die nächste Person (Session-Intro zuerst, dann Scheduler)."""

        introduced = self._introduced_names_for_level(self.level)
        intro_queue = self._intro_queue_for_level(self.level)
        if intro_queue and self._should_pause_intro(introduced):
            pool = introduced if introduced else self.names
            return self.progress_store.choose_next_name(pool, self.level, last_name=self.last_name)

        if intro_queue:
            if (
                self.last_name
                and not self.progress_store.get_allow_immediate_repeat()
                and len(intro_queue) > 1
                and intro_queue[0] == self.last_name
            ):
                intro_queue[0], intro_queue[1] = intro_queue[1], intro_queue[0]
            return intro_queue.pop(0)

        return self.progress_store.choose_next_name(self.names, self.level, last_name=self.last_name)

    def _introduced_names_for_level(self, level):
        introduced = self.introduced_names_by_level.get(level)
        if introduced is None:
            introduced = []
            self.introduced_names_by_level[level] = introduced
        return introduced

    def _mark_person_introduced(self, level, person_key):
        """Nimmt eine Person in den aktiven Session-Scope auf."""

        introduced = self._introduced_names_for_level(level)
        if person_key not in introduced:
            introduced.append(person_key)

        intro_queue = self._intro_queue_for_level(level)
        if person_key in intro_queue:
            intro_queue[:] = [name for name in intro_queue if name != person_key]

    def _is_stable_enough_for_new_intro(self, name, level):
        stats = self.progress_store.level_stats_for_display(name, level)
        streak = int(stats.get("streak", 0))
        relearn_steps = int(stats.get("relearn_steps", 0))
        stability = float(stats.get("stability", 0.0))
        return streak >= 4 and relearn_steps <= 0 and stability >= 0.72

    def _should_pause_intro(self, introduced):
        if not introduced:
            return False

        intro_queue = self._intro_queue_for_level(self.level)

        # Verhindert Start-Hänger auf nur einer Person:
        # Solange erst 1 Name eingeführt wurde und noch Intro-Namen offen sind,
        # immer mindestens den 2. Namen zulassen.
        if len(introduced) == 1 and intro_queue:
            return False

        # Wenn neue Karten aktiv beigemischt/priorisiert werden sollen,
        # Intro nicht durch Stabilitäts-Checks ausbremsen.
        # Nur bei explizit aktivierter Relearn-Priorisierung darf ein fälliger
        # Relearn weiterhin die Intro-Queue unterbrechen.
        if self.progress_store.get_mix_new_cards():
            if (
                self.progress_store.get_prioritize_urgent_repeats()
                and self.progress_store.has_pending_relearn_due(
                    introduced,
                    self.level,
                    last_name=self.last_name,
                )
            ):
                return True
            return False

        if self.progress_store.has_pending_relearn_due(introduced, self.level, last_name=self.last_name):
            return True

        unstable = [name for name in introduced if not self._is_stable_enough_for_new_intro(name, self.level)]
        if not unstable:
            return False

        # Wenn direkter Repeat aus ist und erst ein Name eingeführt wurde,
        # darf ein zweiter Name dazukommen, um Ping-Pong zu vermeiden.
        if (
            len(introduced) == 1
            and intro_queue
            and not self.progress_store.get_allow_immediate_repeat()
        ):
            return False

        return True

    def _intro_queue_for_level(self, level):
        """Liefert die zufällige Intro-Reihenfolge für ein Level in dieser Session."""

        queue = self.session_intro_queue_by_level.get(level)
        if queue is None:
            queue = list(self.names)
            random.shuffle(queue)
            self.session_intro_queue_by_level[level] = queue
        return queue

    def _current_display_name(self):
        info = self.people.get(self.current_name)
        if info and getattr(info, "name", None):
            return info.name
        return self.current_name

    def _expected_name_length(self):
        display_name = self._current_display_name() or ""
        letters = [char for char in display_name if char.isalpha()]
        return max(3, len(letters))

    def _find_confused_person_key(self, guessed_name):
        normalized_guess = normalize_text(guessed_name)
        if not normalized_guess:
            return None

        candidates = []
        for key, info in self.people.items():
            if key == self.current_name:
                continue
            display_name = getattr(info, "name", None) or key
            if normalize_text(display_name) == normalized_guess:
                candidates.append(key)

        if len(candidates) == 1:
            return candidates[0]
        return None

    def _display_name_for_key(self, person_key):
        info = self.people.get(person_key)
        if info and getattr(info, "name", None):
            return info.name
        if isinstance(person_key, str) and "::" in person_key:
            return person_key.split("::", 1)[1]
        return person_key

    def _apply_name_confusion_penalty(self, guessed_name, level):
        confused_key = self._find_confused_person_key(guessed_name)
        if confused_key:
            self.progress_store.register_confusion_wrong(confused_key, level)
            self._mark_person_introduced(level, confused_key)
            return self._display_name_for_key(confused_key)
        return None

    def _stats_text_level1(self, stats):
        return stats_text_level1(stats)

    def _stats_text_level2(self, stats):
        return stats_text_level2(stats)

    def update_stats_label(self):
        """Aktualisiert die Statistikanzeige je nach aktuellem Level."""

        stats = self.progress_store.level_stats_for_display(self.current_name, self.level)
        text = self._stats_text_level1(stats) if self.level == LEVEL_1 else self._stats_text_level2(stats)
        self.stats_label.config(text=text)

    def update_aggregate_stats_label(self):
        """Zeigt aggregierte Lernstände für aktuelle Auswahl und gesamte Lerngruppe."""

        all_names = list(self.people.keys())

        class_stats = self.progress_store.aggregate_stats_for_names(all_names, self.level)

        current_time_text = f"{self.last_response_seconds:.1f}s"
        avg_time_text = f"{class_stats['avg_time_sec']:.1f}s" if class_stats["time_count"] > 0 else "–"
        class_total = class_stats["correct"] + class_stats["wrong"]

        text = (
            f"{self._round_progress_prefix()} · "
            f"Fortschritt aktuelle Auswahl · "
            f"Lerngruppe gesamt: {format_percent(class_stats['ratio'])} "
            f"({class_stats['correct']}/{class_total}) · "
            f"Antwortzeit: {current_time_text} (Ø {avg_time_text})"
        )
        self.aggregate_stats_label.config(text=text)

    def _clear_inputs(self):
        """Leert alle relevanten Eingabefelder für die nächste Aufgabe."""

        entries = (
            self.name_entry,
            self.group_entry,
            self.behind_entry,
            self.front_entry,
            self.opposite_entry,
        )
        for entry in entries:
            entry.configure(state="normal")
            entry.delete(0, ui.END)

    def _pick_feedback_line(self, task_score, component_results):
        """Erzeugt eine Rückmeldung gemäß gewähltem Feedback-Stil."""

        stats = self.progress_store.level_stats_for_display(self.current_name, self.level)
        shown = stats.get("shown", 0)
        correct = stats.get("correct", 0)
        wrong = stats.get("wrong", 0)
        streak = stats.get("streak", 0)
        weight = self.progress_store.person_weight(self.current_name, self.level)

        class_stats = self.progress_store.aggregate_stats_for_names(list(self.people.keys()), self.level)
        class_ratio_percent = round(class_stats.get("ratio", 0.0) * 100)
        class_avg_time_sec = float(class_stats.get("avg_time_sec", 0.0))

        return pick_feedback_line(
            style=self.progress_store.get_feedback_style(),
            task_score=task_score,
            component_results=component_results,
            shown=shown,
            correct=correct,
            wrong=wrong,
            streak=streak,
            person_weight=weight,
            class_ratio_percent=class_ratio_percent,
            class_avg_time_sec=class_avg_time_sec,
            response_seconds=self.last_response_seconds,
        )

    def next_person(self):
        """Wählt die nächste Person und aktualisiert Prompt/Anzeige."""

        if self.round_finished:
            self._close_round_and_return_to_start()
            return

        if self.pending_name_submission:
            self._commit_pending_name_submission()
        if self.pending_level1_submission:
            self._commit_pending_level1_submission()
        self._consume_completed_prompt()

        if self._is_round_limit_reached():
            self._show_round_summary_screen()
            return

        self.current_name = self._pick_next_name()
        self._mark_person_introduced(self.level, self.current_name)
        self.last_name = self.current_name
        self.progress_store.mark_prompt_shown(self.current_name, self.level)
        self.awaiting_solution = True
        self.question_started_at = perf_counter()
        self.last_response_seconds = 0.0
        self.current_prompt_completed = False
        self.current_prompt_success = False
        self.current_prompt_confused_with = None

        # Phasen zurücksetzen
        self.phase_times = {}
        self.phase_results = {}
        self._init_phase()

        # Bild laden falls vorhanden
        self._load_current_photo()

        # Prompt setzen
        if self.mode == MODE_PHOTO:
            self.prompt_label.config(text="Wer ist das?")
        elif self.mode == MODE_COMBINED:
            self.prompt_label.config(text="Wer ist das?")
        else:
            if self.ask_group_question:
                self.prompt_label.config(text=f"Zu welcher {self._group_term()} gehört: {self._current_display_name()}?")
            elif self.level == LEVEL_2:
                self.prompt_label.config(text=f"Wer sitzt um {self._current_display_name()}?")
            else:
                self.prompt_label.config(text=f"{self._current_display_name()}")

        self._clear_inputs()
        self.result_label.config(text="")
        self._set_result_neutral_style()
        self.feedback_label.config(text="")
        self._clear_typo_option()
        self._apply_phase_ui()
        if self.mode == MODE_CSV and self.level == LEVEL_2 and not self.ask_group_question:
            self.solve_button.config(text="Nachbarn auflösen")
        else:
            self.solve_button.config(text="Auflösen")
        self.update_stats_label()
        self.update_aggregate_stats_label()
        self._refresh_debug_panel()
        self._show_action_button()

    def _init_phase(self):
        """Initialisiert die erste Phase basierend auf Modus und Level."""
        if self.mode in (MODE_PHOTO, MODE_COMBINED):
            self.current_phase = PHASE_NAME
        elif self.level == LEVEL_2:
            self.current_phase = PHASE_NEIGHBORS if not self.ask_group_question else PHASE_GROUP
        else:
            self.current_phase = PHASE_GROUP
        self.phase_start_time = perf_counter()

    def _load_current_photo(self):
        """Lädt und zeigt das Bild der aktuellen Person."""
        if self.mode not in (MODE_PHOTO, MODE_COMBINED):
            self.photo_label.config(image="")
            self.current_photo_image = None
            return

        photo_path = self.photo_map.get(self.current_name)
        if not photo_path:
            self.photo_label.config(image="", text="[Kein Bild]")
            self.current_photo_image = None
            return

        try:
            img = Image.open(photo_path)
            # Skalieren auf max 300px Höhe
            max_height = 300
            if img.height > max_height:
                ratio = max_height / img.height
                new_size = (int(img.width * ratio), max_height)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            self.current_photo_image = ImageTk.PhotoImage(img)
            self.photo_label.config(image=self.current_photo_image, text="")
        except Exception as e:
            self.photo_label.config(image="", text=f"[Fehler: {e}]")
            self.current_photo_image = None

    def _apply_phase_ui(self):
        """Aktiviert/Deaktiviert Eingabefelder basierend auf der aktuellen Phase."""
        apply_phase_ui(self)

    def _solve_level1(self):
        response_seconds = perf_counter() - self.question_started_at
        self.last_response_seconds = response_seconds

        correct_group = self.people[self.current_name].table
        if self.ask_group_question:
            guess_group = self.group_entry.get().strip()
            group_ok = evaluate_group_guess(guess_group, correct_group)
        else:
            group_ok = True

        if self.ask_group_question:
            if group_ok:
                result_text = f"✅ {self._group_term()} richtig!"
            else:
                result_text = f"❌ {self._group_term()} falsch.\nRichtig: {correct_group}"
        else:
            result_text = f"ℹ {self._group_term()} eindeutig ({correct_group})"

        self.progress_store.update_level1(self.current_name, group_ok, response_seconds=response_seconds)
        self.update_stats_label()
        self.update_aggregate_stats_label()
        self.result_label.config(text=result_text)
        self.feedback_label.config(
            text=self._pick_feedback_line(
                task_score=1.0 if group_ok else 0.0,
                component_results={"LG": group_ok},
            )
        )
        self._show_verdict(group_ok)
        self._record_prompt_completion(group_ok)
        self.awaiting_solution = False
        self._show_action_button()

    def _solve_level2(self):
        response_seconds = perf_counter() - self.question_started_at
        self.last_response_seconds = response_seconds

        guess_group = self.group_entry.get().strip()
        guess_behind = self.behind_entry.get().strip()
        guess_front = self.front_entry.get().strip()
        guess_opposite = self.opposite_entry.get().strip()

        correct_group = self.people[self.current_name].table
        group_ok = evaluate_group_guess(guess_group, correct_group)
        neighbor_eval = evaluate_neighbors(
            self.current_name,
            self.people,
            self.grid,
            guess_behind,
            guess_front,
            guess_opposite,
        )

        behind_ok = neighbor_eval["behind_ok"]
        front_ok = neighbor_eval["front_ok"]
        opposite_ok = neighbor_eval["opposite_ok"]

        result_text = build_csv_level2_result_text(
            correct_group,
            group_ok,
            behind_ok,
            neighbor_eval["behind_text"],
            opposite_ok,
            neighbor_eval["opposite_text"],
            front_ok,
            neighbor_eval["front_text"],
        )

        self.progress_store.update_level2(
            self.current_name,
            group_ok=group_ok,
            behind_ok=behind_ok,
            front_ok=front_ok,
            opposite_ok=opposite_ok,
            response_seconds=response_seconds,
        )

        task_score = csv_level2_task_score(group_ok, behind_ok, front_ok, opposite_ok)

        self.update_stats_label()
        self.update_aggregate_stats_label()
        self.result_label.config(text=result_text)
        self.feedback_label.config(
            text=self._pick_feedback_line(
                task_score=task_score,
                component_results={
                    "LG": group_ok,
                    "Dahinter": behind_ok,
                    "Gegenüber": opposite_ok,
                    "Davor": front_ok,
                },
            )
        )
        self._show_verdict(group_ok and behind_ok and front_ok and opposite_ok)
        self._record_prompt_completion(group_ok and behind_ok and front_ok and opposite_ok)
        self.awaiting_solution = False
        self._show_action_button()

    def solve(self):
        """Delegiert an die phasen- und modus-spezifische Auswertung."""

        if not self._require_min_retrieval_delay():
            return

        # Reiner CSV-Modus Level 1: wie bisher
        if self.mode == MODE_CSV and self.level == LEVEL_1:
            self._solve_level1()
            return

        # Reiner CSV-Modus Level 2: sequentiell
        if self.mode == MODE_CSV and self.level == LEVEL_2:
            self._solve_csv_level2_phase()
            return

        # Foto-Modus: nur Name
        if self.mode == MODE_PHOTO:
            self._solve_photo_phase()
            return

        # Kombinierter Modus: Name -> TG -> Nachbarn
        if self.mode == MODE_COMBINED:
            self._solve_combined_phase()
            return

    def _solve_csv_level2_phase(self):
        """Löst die aktuelle Phase im CSV Level 2 auf."""
        phase_time = perf_counter() - self.phase_start_time

        if self.current_phase == PHASE_GROUP:
            if not self.ask_group_question:
                self.phase_times[PHASE_GROUP] = 0.0
                self.phase_results[PHASE_GROUP] = {"group": True}
                self.current_phase = PHASE_NEIGHBORS
                self.phase_start_time = perf_counter()
                self._apply_phase_ui()
                self.solve_button.config(text="Nachbarn auflösen")
                return

            # Tischgruppe auswerten
            guess_group = self.group_entry.get().strip()
            correct_group = self.people[self.current_name].table
            group_ok = evaluate_group_guess(guess_group, correct_group)

            self.phase_times[PHASE_GROUP] = phase_time
            self.phase_results[PHASE_GROUP] = {"group": group_ok}

            if group_ok:
                result_text = f"✅ {self._group_term()}: {correct_group}"
            else:
                result_text = f"❌ {self._group_term()} falsch. Richtig: {correct_group}"

            self.result_label.config(text=result_text)
            self._show_verdict(group_ok)

            if self.level2_require_group_before_neighbors and not group_ok:
                neighbor_eval = evaluate_neighbors(
                    self.current_name,
                    self.people,
                    self.grid,
                    "",
                    "",
                    "",
                )
                behind_ok = neighbor_eval["behind_ok"]
                front_ok = neighbor_eval["front_ok"]
                opposite_ok = neighbor_eval["opposite_ok"]

                self.phase_times[PHASE_NEIGHBORS] = 0.0
                self.phase_results[PHASE_NEIGHBORS] = {
                    "behind": behind_ok,
                    "front": front_ok,
                    "opposite": opposite_ok,
                }

                result_text = build_csv_level2_result_text(
                    correct_group,
                    group_ok,
                    behind_ok,
                    neighbor_eval["behind_text"],
                    opposite_ok,
                    neighbor_eval["opposite_text"],
                    front_ok,
                    neighbor_eval["front_text"],
                )
                result_text += f"\n\n⏱ {self._group_abbr()}: {phase_time:.1f}s · Nachbarn: übersprungen"
                self.result_label.config(text=result_text)

                self.last_response_seconds = phase_time
                self.progress_store.update_level2(
                    self.current_name,
                    group_ok=group_ok,
                    behind_ok=behind_ok,
                    front_ok=front_ok,
                    opposite_ok=opposite_ok,
                    response_seconds=self.last_response_seconds,
                )

                task_score = csv_level2_task_score(group_ok, behind_ok, front_ok, opposite_ok)
                self.update_stats_label()
                self.update_aggregate_stats_label()
                self.feedback_label.config(
                    text=self._pick_feedback_line(
                        task_score=task_score,
                        component_results={
                            "LG": group_ok,
                            "Dahinter": behind_ok,
                            "Gegenüber": opposite_ok,
                            "Davor": front_ok,
                        },
                    )
                )
                self._show_verdict(group_ok and behind_ok and front_ok and opposite_ok)

                self.current_phase = PHASE_DONE
                self._record_prompt_completion(False)
                self.awaiting_solution = False
                self._apply_phase_ui()
                self.solve_button.config(text="Auflösen")
                self._clear_typo_option()
                self._show_action_button()
                return

            # Zur nächsten Phase
            self.current_phase = PHASE_NEIGHBORS
            self.phase_start_time = perf_counter()
            self._apply_phase_ui()
            self.solve_button.config(text="Nachbarn auflösen")
            return

        if self.current_phase == PHASE_NEIGHBORS:
            # Nachbarn auswerten
            guess_behind = self.behind_entry.get().strip()
            guess_front = self.front_entry.get().strip()
            guess_opposite = self.opposite_entry.get().strip()

            neighbor_eval = evaluate_neighbors(
                self.current_name,
                self.people,
                self.grid,
                guess_behind,
                guess_front,
                guess_opposite,
            )
            behind_ok = neighbor_eval["behind_ok"]
            front_ok = neighbor_eval["front_ok"]
            opposite_ok = neighbor_eval["opposite_ok"]

            self.phase_times[PHASE_NEIGHBORS] = phase_time
            self.phase_results[PHASE_NEIGHBORS] = {
                "behind": behind_ok,
                "front": front_ok,
                "opposite": opposite_ok,
            }

            wrong_neighbor_field = self._first_wrong_neighbor_field(behind_ok, front_ok, opposite_ok)
            if wrong_neighbor_field:
                self._set_typo_option(PHASE_NEIGHBORS, wrong_neighbor_field)
            else:
                self._clear_typo_option()

            # Gesamtergebnis aktualisieren
            correct_group = self.people[self.current_name].table
            group_ok = self.phase_results.get(PHASE_GROUP, {}).get("group", False)

            result_text = build_csv_level2_result_text(
                correct_group,
                group_ok,
                behind_ok,
                neighbor_eval["behind_text"],
                opposite_ok,
                neighbor_eval["opposite_text"],
                front_ok,
                neighbor_eval["front_text"],
            )

            # Zeiten anzeigen
            group_time = self.phase_times.get(PHASE_GROUP, 0)
            neighbor_time = self.phase_times.get(PHASE_NEIGHBORS, 0)
            result_text += f"\n\n⏱ {self._group_abbr()}: {group_time:.1f}s · Nachbarn: {neighbor_time:.1f}s"

            self.result_label.config(text=result_text)

            # Gesamtzeit für Statistik
            self.last_response_seconds = group_time + neighbor_time

            # Progress aktualisieren
            self.progress_store.update_level2(
                self.current_name,
                group_ok=group_ok,
                behind_ok=behind_ok,
                front_ok=front_ok,
                opposite_ok=opposite_ok,
                response_seconds=self.last_response_seconds,
            )

            task_score = csv_level2_task_score(group_ok, behind_ok, front_ok, opposite_ok)

            self.update_stats_label()
            self.update_aggregate_stats_label()
            self.feedback_label.config(
                text=self._pick_feedback_line(
                    task_score=task_score,
                    component_results={
                        "LG": group_ok,
                        "Dahinter": behind_ok,
                        "Gegenüber": opposite_ok,
                        "Davor": front_ok,
                    },
                )
            )
            self._show_verdict(group_ok and behind_ok and front_ok and opposite_ok)

            self.current_phase = PHASE_DONE
            self._record_prompt_completion(group_ok and behind_ok and front_ok and opposite_ok)
            self.awaiting_solution = False
            self._apply_phase_ui()
            self.solve_button.config(text="Auflösen")
            self._show_action_button()

    def _group_term(self):
        """Liefert den passenden Begriff für die Gruppenfrage je Modus."""

        if self.mode == MODE_CSV:
            return "Tischgruppe"
        return "Lerngruppe"

    def _group_abbr(self):
        """Liefert die Kurzform für Zeit-/Statistiktexte je Modus."""

        if self.mode == MODE_CSV:
            return "TG"
        return "LG"

    def _solve_photo_phase(self):
        """Löst im reinen Foto-Modus auf."""
        phase_time = perf_counter() - self.phase_start_time

        if self.current_phase == PHASE_NAME:
            guess_name = self.name_entry.get().strip()
            display_name = self._current_display_name()
            name_ok = normalize_text(guess_name) == normalize_text(display_name)
            confused_with = None
            if not name_ok:
                confused_with = self._preview_name_confusion(guess_name)

            self.phase_times[PHASE_NAME] = phase_time
            self.phase_results[PHASE_NAME] = {
                "name": name_ok,
                "guess_name": guess_name,
                "confused_with": confused_with,
                "confusion_penalized": False,
            }
            if name_ok:
                self._clear_typo_option()
            else:
                if confused_with:
                    self._clear_typo_option()
                else:
                    self._set_typo_option(PHASE_NAME, "name")
            if name_ok:
                result_text = f"✅ Richtig: {display_name}"
            else:
                result_text = f"❌ Falsch. Richtig: {display_name}"
                if confused_with:
                    result_text += f"\n↺ Verwechslung mit: {confused_with}"

            result_text += f"\n⏱ Zeit: {phase_time:.1f}s"
            self.result_label.config(text=result_text)
            self._show_verdict(name_ok)

            if not self.ask_group_question:
                self.current_phase = PHASE_DONE
                self._record_prompt_completion(name_ok, confused_with=confused_with)
                self.awaiting_solution = False
                self._apply_phase_ui()
                self.solve_button.config(text="Auflösen")
                self.pending_name_submission = {
                    "phase_time": phase_time,
                    "name_ok": bool(name_ok),
                }
                if name_ok or confused_with:
                    self._commit_pending_name_submission()
                self._show_action_button()
                return

            self.prompt_label.config(text=f"Zu welcher Lerngruppe gehört {display_name}?")
            self.current_phase = PHASE_GROUP
            self.phase_start_time = perf_counter()
            self._apply_phase_ui()
            self.solve_button.config(text="Lerngruppe auflösen")
            self._show_action_button()
            return

        if self.current_phase == PHASE_GROUP:
            guess_group = self.group_entry.get().strip()
            correct_group = self.people[self.current_name].table
            group_ok = evaluate_group_guess(guess_group, correct_group)

            self.phase_times[PHASE_GROUP] = phase_time
            self.phase_results[PHASE_GROUP] = {"group": group_ok}
            if group_ok:
                if self.name_typo_phase == PHASE_GROUP:
                    self._clear_typo_option()
            else:
                self._set_typo_option(PHASE_GROUP, "group")

            name_ok = self.phase_results.get(PHASE_NAME, {}).get("name", False)
            confused_with = self.phase_results.get(PHASE_NAME, {}).get("confused_with")
            name_time = self.phase_times.get(PHASE_NAME, 0)
            group_time = self.phase_times.get(PHASE_GROUP, 0)
            display_name = self._current_display_name()

            result_text = f"{'✅' if name_ok else '❌'} Name: {display_name}\n"
            if group_ok:
                result_text += f"✅ Lerngruppe: {correct_group}"
            else:
                result_text += f"❌ Lerngruppe falsch. Richtig: {correct_group}"
            if confused_with:
                result_text += f"\n↺ Verwechslung mit: {confused_with}"
            result_text += f"\n\n⏱ Name: {name_time:.1f}s · LG: {group_time:.1f}s"
            self.result_label.config(text=result_text)

            all_ok = name_ok and group_ok
            self.last_response_seconds = name_time + group_time
            has_name_confusion = bool(confused_with)

            if all_ok or has_name_confusion:
                self.progress_store.update_level1(
                    self.current_name,
                    all_ok,
                    response_seconds=self.last_response_seconds,
                    expected_name_length=self._expected_name_length(),
                )
                if has_name_confusion:
                    self._apply_name_confusion_penalty_if_needed(LEVEL_1)
                self.pending_level1_submission = None
            else:
                self.pending_level1_submission = {
                    "response_seconds": self.last_response_seconds,
                    "confusion_level": LEVEL_1,
                }

            if all_ok or has_name_confusion:
                self.update_stats_label()
                self.update_aggregate_stats_label()
            self.feedback_label.config(
                text=self._pick_feedback_line(
                    task_score=1.0 if all_ok else (0.5 if (name_ok or group_ok) else 0.0),
                    component_results={"Name": name_ok, "LG": group_ok},
                )
            )
            self._show_verdict(all_ok)

            self.current_phase = PHASE_DONE
            self._record_prompt_completion(all_ok, confused_with=confused_with)
            self.awaiting_solution = False
            self._apply_phase_ui()
            self.solve_button.config(text="Auflösen")
            if name_ok and group_ok:
                self._clear_typo_option()
            self._show_action_button()

    def _solve_combined_phase(self):
        """Löst die aktuelle Phase im kombinierten Modus auf."""
        phase_time = perf_counter() - self.phase_start_time

        if self.current_phase == PHASE_NAME:
            guess_name = self.name_entry.get().strip()
            display_name = self._current_display_name()
            name_ok = normalize_text(guess_name) == normalize_text(display_name)
            confused_with = None

            if not name_ok:
                confused_with = self._preview_name_confusion(guess_name)

            self.phase_times[PHASE_NAME] = phase_time
            self.phase_results[PHASE_NAME] = {
                "name": name_ok,
                "guess_name": guess_name,
                "confused_with": confused_with,
                "confusion_penalized": False,
            }
            if name_ok:
                self._clear_typo_option()
            else:
                if confused_with:
                    self._clear_typo_option()
                else:
                    self._set_typo_option(PHASE_NAME, "name")

            if name_ok:
                result_text = f"✅ Name: {display_name}"
            else:
                result_text = f"❌ Name falsch. Richtig: {display_name}"
                if confused_with:
                    result_text += f"\n↺ Verwechslung mit: {confused_with}"

            self.result_label.config(text=result_text)
            self._show_verdict(name_ok)
            self.prompt_label.config(text=f"Zu welcher Lerngruppe gehört {display_name}?")

            # Zur nächsten Phase
            self.current_phase = PHASE_GROUP
            self.phase_start_time = perf_counter()
            self._apply_phase_ui()
            self.solve_button.config(text="Lerngruppe auflösen")
            self._show_action_button()
            return

        if self.current_phase == PHASE_GROUP:
            guess_group = self.group_entry.get().strip()
            correct_group = self.people[self.current_name].table
            group_ok = evaluate_group_guess(guess_group, correct_group)

            self.phase_times[PHASE_GROUP] = phase_time
            self.phase_results[PHASE_GROUP] = {"group": group_ok}
            if group_ok:
                if self.name_typo_phase == PHASE_GROUP:
                    self._clear_typo_option()
            else:
                self._set_typo_option(PHASE_GROUP, "group")

            name_ok = self.phase_results.get(PHASE_NAME, {}).get("name", False)
            name_time = self.phase_times.get(PHASE_NAME, 0)
            display_name = self._current_display_name()

            result_text = f"{'✅' if name_ok else '❌'} Name: {display_name}\n"
            if group_ok:
                result_text += f"✅ Lerngruppe: {correct_group}"
            else:
                result_text += f"❌ Lerngruppe falsch. Richtig: {correct_group}"

            self.result_label.config(text=result_text)

            # Bei Level 1: fertig nach TG
            if self.level == LEVEL_1:
                group_time = self.phase_times.get(PHASE_GROUP, 0)
                self.last_response_seconds = name_time + group_time
                has_name_confusion = bool(self.phase_results.get(PHASE_NAME, {}).get("confused_with"))

                result_text += f"\n\n⏱ Name: {name_time:.1f}s · LG: {group_time:.1f}s"
                self.result_label.config(text=result_text)

                all_ok = name_ok and group_ok
                if all_ok or has_name_confusion:
                    self.progress_store.update_level1(
                        self.current_name,
                        all_ok,
                        response_seconds=self.last_response_seconds,
                        expected_name_length=self._expected_name_length(),
                    )
                    if has_name_confusion:
                        self._apply_name_confusion_penalty_if_needed(self.level)
                    self.pending_level1_submission = None
                else:
                    self.pending_level1_submission = {
                        "response_seconds": self.last_response_seconds,
                        "confusion_level": self.level,
                    }

                if all_ok or has_name_confusion:
                    self.update_stats_label()
                    self.update_aggregate_stats_label()
                self.feedback_label.config(
                    text=self._pick_feedback_line(
                        task_score=1.0 if all_ok else (0.5 if (name_ok or group_ok) else 0.0),
                        component_results={"Name": name_ok, "LG": group_ok},
                    )
                )
                self._show_verdict(all_ok)

                self.current_phase = PHASE_DONE
                self._record_prompt_completion(
                    all_ok,
                    confused_with=self.phase_results.get(PHASE_NAME, {}).get("confused_with"),
                )
                self.awaiting_solution = False
                self._apply_phase_ui()
                self.solve_button.config(text="Auflösen")
                if name_ok and group_ok:
                    self._clear_typo_option()
                self._show_action_button()
                return

            # Bei Level 2: weiter zu Nachbarn
            self.current_phase = PHASE_NEIGHBORS
            self.phase_start_time = perf_counter()
            self._apply_phase_ui()
            self.solve_button.config(text="Nachbarn auflösen")
            self._show_action_button()
            return

        if self.current_phase == PHASE_NEIGHBORS:
            guess_behind = self.behind_entry.get().strip()
            guess_front = self.front_entry.get().strip()
            guess_opposite = self.opposite_entry.get().strip()

            neighbor_eval = evaluate_neighbors(
                self.current_name,
                self.people,
                self.grid,
                guess_behind,
                guess_front,
                guess_opposite,
            )
            behind_ok = neighbor_eval["behind_ok"]
            front_ok = neighbor_eval["front_ok"]
            opposite_ok = neighbor_eval["opposite_ok"]

            self.phase_times[PHASE_NEIGHBORS] = phase_time
            self.phase_results[PHASE_NEIGHBORS] = {
                "behind": behind_ok,
                "front": front_ok,
                "opposite": opposite_ok,
            }

            wrong_neighbor_field = self._first_wrong_neighbor_field(behind_ok, front_ok, opposite_ok)
            if wrong_neighbor_field:
                self._set_typo_option(PHASE_NEIGHBORS, wrong_neighbor_field)
            else:
                self._clear_typo_option()

            name_ok = self.phase_results.get(PHASE_NAME, {}).get("name", False)
            group_ok = self.phase_results.get(PHASE_GROUP, {}).get("group", False)
            correct_group = self.people[self.current_name].table
            display_name = self._current_display_name()

            result_text = build_combined_level2_result_text(
                display_name,
                name_ok,
                correct_group,
                group_ok,
                behind_ok,
                neighbor_eval["behind_text"],
                opposite_ok,
                neighbor_eval["opposite_text"],
                front_ok,
                neighbor_eval["front_text"],
            )

            # Zeiten anzeigen
            name_time = self.phase_times.get(PHASE_NAME, 0)
            group_time = self.phase_times.get(PHASE_GROUP, 0)
            neighbor_time = self.phase_times.get(PHASE_NEIGHBORS, 0)
            result_text += f"\n\n⏱ Name: {name_time:.1f}s · LG: {group_time:.1f}s · Nachbarn: {neighbor_time:.1f}s"

            self.result_label.config(text=result_text)

            # Gesamtzeit
            self.last_response_seconds = name_time + group_time + neighbor_time

            if not name_ok:
                self._apply_name_confusion_penalty_if_needed(self.level)

            # Progress aktualisieren
            self.progress_store.update_level2(
                self.current_name,
                group_ok=group_ok,
                behind_ok=behind_ok,
                front_ok=front_ok,
                opposite_ok=opposite_ok,
                name_ok=name_ok,
                response_seconds=self.last_response_seconds,
                expected_name_length=self._expected_name_length(),
            )

            task_score = combined_level2_task_score(name_ok, group_ok, behind_ok, front_ok, opposite_ok)

            self.update_stats_label()
            self.update_aggregate_stats_label()
            self.feedback_label.config(
                text=self._pick_feedback_line(
                    task_score=task_score,
                    component_results={
                        "Name": name_ok,
                        "LG": group_ok,
                        "Dahinter": behind_ok,
                        "Gegenüber": opposite_ok,
                        "Davor": front_ok,
                    },
                )
            )
            self._show_verdict(name_ok and group_ok and behind_ok and front_ok and opposite_ok)

            self.current_phase = PHASE_DONE
            self._record_prompt_completion(
                name_ok and group_ok and behind_ok and front_ok and opposite_ok,
                confused_with=self.phase_results.get(PHASE_NAME, {}).get("confused_with"),
            )
            self.awaiting_solution = False
            self._apply_phase_ui()
            self.solve_button.config(text="Auflösen")
            self._show_action_button()

    def _commit_pending_name_submission(self):
        """Schreibt eine ausstehende Name-only-Auswertung in den Fortschritt."""

        pending = self.pending_name_submission
        if not pending:
            return

        name_ok = bool(self.phase_results.get(PHASE_NAME, {}).get("name", pending.get("name_ok", False)))
        phase_time = float(pending.get("phase_time", 0.0))
        self.last_response_seconds = phase_time

        if not name_ok:
            self._apply_name_confusion_penalty_if_needed(LEVEL_1)

        self.progress_store.update_level1(
            self.current_name,
            name_ok,
            response_seconds=self.last_response_seconds,
            expected_name_length=self._expected_name_length(),
        )

        self.update_stats_label()
        self.update_aggregate_stats_label()
        self.feedback_label.config(
            text=self._pick_feedback_line(
                task_score=1.0 if name_ok else 0.0,
                component_results={"Name": name_ok},
            )
        )

        self.pending_name_submission = None

    def _commit_pending_level1_submission(self):
        """Schreibt eine ausstehende Kombi-Level-1-Auswertung in den Fortschritt."""

        pending = self.pending_level1_submission
        if not pending:
            return

        name_ok = bool(self.phase_results.get(PHASE_NAME, {}).get("name", False))
        group_ok = bool(self.phase_results.get(PHASE_GROUP, {}).get("group", False))
        all_ok = name_ok and group_ok
        response_seconds = float(pending.get("response_seconds", 0.0))
        confusion_level = int(pending.get("confusion_level", self.level))

        if not name_ok:
            self._apply_name_confusion_penalty_if_needed(confusion_level)

        self.progress_store.update_level1(
            self.current_name,
            all_ok,
            response_seconds=response_seconds,
            expected_name_length=self._expected_name_length(),
        )

        self.update_stats_label()
        self.update_aggregate_stats_label()

        self.pending_level1_submission = None

    def mark_name_typo(self):
        """Setzt die letzte Antwort zurück und ermöglicht Neueingabe."""

        if not self.name_typo_available:
            return

        target_phase = self.name_typo_phase or PHASE_NAME
        target_field = self.name_typo_field or "name"
        target_result = self.phase_results.get(target_phase)
        if not target_result:
            return

        target_result[target_field] = False
        self._clear_typo_option()

        entry = self._entry_for_field(target_field)
        if entry:
            entry.configure(state="normal")
            entry.delete(0, ui.END)

        self.result_label.config(text="↩️ Eingabe zurückgesetzt – bitte neu eingeben.")
        self._set_result_neutral_style()
        self.feedback_label.config(text="")
        self.current_prompt_completed = False
        self.current_prompt_success = False
        self.current_prompt_confused_with = None

        can_reset_from_done = (
            self.current_phase == PHASE_DONE
            and (
                self.pending_level1_submission is not None
                or self.pending_name_submission is not None
                or (
                    self.level == LEVEL_2
                    and self.mode in (MODE_CSV, MODE_COMBINED)
                    and target_phase in (PHASE_GROUP, PHASE_NEIGHBORS)
                )
            )
        )

        if self.pending_name_submission and target_field == "name":
            self.pending_name_submission = None

        if (self.current_phase != PHASE_DONE or can_reset_from_done) and target_phase in (
            PHASE_NAME,
            PHASE_GROUP,
            PHASE_NEIGHBORS,
        ):
            self.current_phase = target_phase
            self.awaiting_solution = True
            self.phase_start_time = perf_counter()
            self._apply_phase_ui()
            self._focus_entry_for_phase(target_phase)
            if target_phase == PHASE_NEIGHBORS:
                self.solve_button.config(text="Nachbarn auflösen")
            elif target_phase == PHASE_GROUP and self.mode in (MODE_PHOTO, MODE_COMBINED):
                self.solve_button.config(text=f"{self._group_term()} auflösen")
            else:
                self.solve_button.config(text="Auflösen")

        self._show_action_button()


