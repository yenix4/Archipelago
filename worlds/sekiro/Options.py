import json
from dataclasses import dataclass
from typing import Any

from Options import (
    Choice,
    DefaultOnToggle,
    ExcludeLocations,
    OptionDict,
    OptionGroup,
    PerGameCommonOptions,
    Toggle,
    Visibility,
)

## Game Options

class GoalOption(Choice):
    """
    Shura: Play until the first invasion and choose to obey the Iron Code when prompted by Owl.
    This is a shorter playthrough ideal for big syncs with time limits.

    Full Game: Play the entire game by breaking the Iron Code when prompted by Owl after the first invasion.
    Any of the 3 full endings will work for this.

    NOTE: The choice of ending must still be selected by you in the game. So no mashing through the dialogue!
    """
    display_name = "Goal"
    option_full_game = 0
    option_shura = 1
    default = 0

class QuickHirata(Choice):
    """Force the Young Lord's Bell Charm to be early in your local world or the multiworld

    If you wish to use this in a solo playthrough or with games that have a very limited sphere 1, please use
    early_local for best results. Otherwise, the generation may not be able to place this early and will put it anywhere
    in the multiworld.
    """
    display_name = "Quick Hirata"
    option_off = 0
    option_early_global = 1
    option_early_local = 2
    default = option_off

class VeryEarlyHirata(Toggle):
    """Make it possible to need to progress into Hirata Estate before Ashina Outskirts (no softlock)

    If this is selected, and you get the Young Lord's Bell Charm instead of the Prosthetic, the Prosthetic can end up
    being in the multiworld. Keep this in mind, as it may BK you for a good bit.
    """
    display_name = "Allow Very Early Hirata"

class AdditionalRegionLocks(DefaultOnToggle):
    """Add custom progression items and corresponding blockers to the entrances to Ashina Castle, Abandoned Dungeon,
    Senpou Temple, Ashina Depths (Poison Pool) and Sunken Valley to allow for more spheres and better balancing. The
    items in question are described in the item documentation found on the GitHub. This also removes Bull skip!

    This is recommended to be kept enabled.
    If you disable it, you will immediately have over half the game in logic once you have the prosthetic.
    """
    display_name = "Additional Progression Blockers"

class DeathLink(Choice):
    """When you die, everyone who enabled death link dies. Of course, the reverse is true too.

    - **Off:** Death link is disabled. (The default.)
    - **Full Death:** Death link triggers only for full deaths. (No resurrection available or falling death).
    - **Any Death:** Death link triggers anytime you hit 0 HP. (Warning: Usage can lead to angry cooperators!)
    """
    display_name = "Death Link"
    option_off = 0
    alias_false = 0
    option_full_death = 1
    alias_true = 1
    option_any_death = 2
    default = 0

class RemoveHeadlessSlowWalk(Toggle):
    """Remove the Headless-induced slow walk."""
    display_name = "Remove Headless slow walk"

## Skills

class RandomizeSkillsandProsthetics(Toggle):
    """Randomize Skills and Prosthetics in their respective upgrade trees."""
    display_name = "Randomize Skills and Prosthetics"


class ReplaceEsotericTextswithSkills(Toggle):
    """Randomize Skills as Item pickups, removing the Esoteric Texts.

    This will raise an error unless Skills and Prosthetics are also randomized.
    """
    display_name = "Replace Esoteric Texts with Skills as Items"

### Enemies

class RandomizeEnemiesOption(DefaultOnToggle):
    """Randomize enemy and boss placements."""
    display_name = "Randomize Enemies"


class RandomizeHeadlessOption(Toggle):
    """Include headless in the randomizer pool for minibosses (non-underwater)

    This is ignored unless enemies are randomized.
    """
    display_name = "Randomize Headless"


class SimilarBossPhases(DefaultOnToggle):
    """Prevent fights to be something like Sword Saint Isshin + Demon of Hatred.

     This setting will try to keep a similar number of phases compared to the replaced vanilla bosses.

     This is ignored unless enemies are randomized.
     """
    display_name = "Similar Number of Boss Phases"


class BalancedEndgameBossPhases(DefaultOnToggle):
    """Prevent early bosses to be seriously unfun by considering late game boss phases as longer than earlier ones.

    This is ignored unless enemies are randomized.
    """
    display_name = "Smoothed Boss Phases"


class SimpleEarlyMinibosses(DefaultOnToggle):
    """Prevent early minibosses from being unfun without scaling.

    Should you turn this off, you will be provided 2x Divine Confetti to be collected from the Offering Box (each
    costing 50 sen, because the Offering Box is weird like that and will not display it if it costs less than 50...)
    This is in case you get an early blocking Shichimen (or Headless if they are enabled).
    After using those, your fate is up to luck (or skill).

    This is ignored unless enemies are randomized.
    """
    display_name = "Simple Early Minibosses"


class ScaleEnemiesOption(DefaultOnToggle):
    """Scale randomized enemy stats to match the areas in which they appear.

    Disabling this will tend to make the early game much more difficult and the late game much
    easier.

    This is ignored unless enemies are randomized.
    """
    display_name = "Scale Enemies"


class RandomEnemyPresetOption(OptionDict):
    """The YAML preset for the static enemy randomizer.

    See the static randomizer documentation in `randomizerAP\\presets\\README.txt` for details.
    Include this as nested YAML. For example:

    .. code-block:: YAML

      random_enemy_preset:
        RemoveSource: Demon of Hatred; Corrupted monk
        DontRandomize: Shichimen Warrior

    Full presets such as Ashina Zoo or Nightmare Mode have been built into the client for ease of use. Simply use the
    `Randomizer options` to select your desired preset before first connecting to a multiworld.
    """
    display_name = "Random Enemy Preset"
    supports_weighting = False
    default = {}

    valid_keys = ["Description", "RecommendFullRandomization", "RecommendNoEnemyProgression",
                  "OopsAll", "Boss", "Miniboss", "Basic", "Add", "FoldingMonkey", "BuffBasicEnemiesAsBosses",
                  "DontRandomize", "RemoveSource", "Enemies"]

    @classmethod
    def get_option_name(cls, value: dict[str, Any]) -> str:
        return json.dumps(value)


## Item & Location

class Carpsanity(Toggle):
    """Add Treasure Carp drops into the item pool"""
    display_name = "Carpsanity"

class SekiroExcludeLocations(ExcludeLocations):
    """Prevent these locations from having an important item."""
    default = frozenset({"Hidden", "Headless"})


class ExcludedLocationBehaviorOption(Choice):
    """How to choose items for excluded locations in Sekiro.

    - **Allow Useful:** Excluded locations can't have progression items, but they can have useful
      items.
    - **Forbid Useful:** Neither progression items nor useful items can be placed in excluded
      locations.
    - **Do Not Randomize:** Excluded locations always contain the same item as in vanilla Sekiro.

    A "progression item" is anything that's required to unlock another location in some game. A
    "useful item" is something each game defines individually, usually items that are quite
    desirable but not strictly necessary.
    """
    display_name = "Excluded Locations Behavior"
    option_allow_useful = 1
    option_forbid_useful = 2
    option_do_not_randomize = 3
    default = 2


class MissableLocationBehaviorOption(Choice):
    """Which items can be placed in locations that can be permanently missed.

    - **Allow Useful:** Missable locations can't have progression items, but they can have useful
      items.
    - **Forbid Useful:** Neither progression items nor useful items can be placed in missable
      locations.
    - **Do Not Randomize:** Missable locations always contain the same item as in vanilla Sekiro.

    A "progression item" is anything that's required to unlock another location in some game. A
    "useful item" is something each game defines individually, usually items that are quite
    desirable but not strictly necessary.
    """
    display_name = "Missable Locations Behavior"
    option_allow_useful = 1
    option_forbid_useful = 2
    option_do_not_randomize = 3
    default = 2


@dataclass
class SekiroOptions(PerGameCommonOptions):
    # Game Options
    goal_option: GoalOption
    quick_hirata: QuickHirata
    very_early_hirata: VeryEarlyHirata
    additional_region_locks: AdditionalRegionLocks
    death_link: DeathLink
    remove_headless_slow_walk: RemoveHeadlessSlowWalk

    # Skills
    randomize_skills_and_prosthetics: RandomizeSkillsandProsthetics
    replace_esoteric_texts_with_skills: ReplaceEsotericTextswithSkills

    # Enemies
    randomize_enemies: RandomizeEnemiesOption
    randomize_headless: RandomizeHeadlessOption
    similar_boss_phases: SimilarBossPhases
    balanced_endgame_boss_phases: BalancedEndgameBossPhases
    simple_early_minibosses: SimpleEarlyMinibosses
    scale_enemies: ScaleEnemiesOption
    random_enemy_preset: RandomEnemyPresetOption

    # Item & Location
    carpsanity: Carpsanity
    exclude_locations: SekiroExcludeLocations
    excluded_location_behavior: ExcludedLocationBehaviorOption
    missable_location_behavior: MissableLocationBehaviorOption


option_groups = [
    OptionGroup("Skills", [
        RandomizeSkillsandProsthetics,
        ReplaceEsotericTextswithSkills,
    ]),
    OptionGroup("Enemies", [
        RandomizeEnemiesOption,
        RandomizeHeadlessOption,
        SimilarBossPhases,
        BalancedEndgameBossPhases,
        SimpleEarlyMinibosses,
        ScaleEnemiesOption,
        RandomEnemyPresetOption,
    ]),
    OptionGroup("Item & Location Options", [
        Carpsanity,
        SekiroExcludeLocations,
        ExcludedLocationBehaviorOption,
        MissableLocationBehaviorOption,
    ])
]
