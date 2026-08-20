# world/sekiro/__init__.py
import json
import random
from collections.abc import Callable
from logging import warning
from typing import Any, Dict, List, Optional, Set, TextIO, Union, cast

from BaseClasses import (
    CollectionState,
    Entrance,
    ItemClassification,
    Location,
    LocationProgressType,
    MultiWorld,
    Region,
    Tutorial,
)
from worlds.AutoWorld import WebWorld, World
from worlds.generic.Rules import CollectionRule, ItemRule, add_item_rule, add_rule

from .Items import (
    SekiroItem,
    SekiroItemCategory,
    SekiroItemData,
    filler_item_names,
    item_descriptions,
    item_dictionary,
    item_name_groups,
    region_lock_dictionary,
    skill_pickup_dictionary,
)
from .Locations import (
    SekiroLocation,
    SekiroLocationData,
    location_descriptions,
    location_dictionary,
    location_name_groups,
    location_tables,
)
from .Options import SekiroOptions, option_groups
from Options import OptionError


class SekiroWeb(WebWorld):
    bug_report_page = "replace with Bug Report page"
    theme = "dirt"
    setup_en = Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up the Archipelago Sekiro randomizer on your computer.",
        "English",
        "setup_en.md",
        "setup/en",
        ["Yenix"]
    )

    tutorials = [setup_en]
    option_groups = option_groups
    item_descriptions = item_descriptions
    rich_text_options_doc = True


class SekiroWorld(World):
    """
    Sekiro: Shadows Die Twice is a third-person, action-adventure game set in a brutal,
    fictionalized Japan of the late 1500s (Sengoku period).
    Developed by FromSoftware, the game emphasizes precise, high-risk sword combat and stealth,
    moving away from the RPG elements of their previous Dark Souls series.
    """

    game = "Sekiro: Shadows Die Twice"
    options: SekiroOptions
    options_dataclass = SekiroOptions
    web = SekiroWeb()
    base_id = 100000
    item_name_to_id = {data.name: data.ap_code for data in item_dictionary.values() if data.ap_code is not None}
    location_name_to_id = {
        location.name: location.ap_code
        for locations in location_tables.values()
        for location in locations
        if location.ap_code is not None
    }
    location_name_groups = location_name_groups
    item_name_groups = item_name_groups
    location_descriptions = location_descriptions
    item_descriptions = item_descriptions

    all_excluded_locations: set[str] = set()
    """This is the same value as `self.options.exclude_locations.value` initially, but if
    `options.exclude_locations` gets cleared due to `excluded_locations: allow_useful` this still
    holds the old locations so we can ensure they don't get necessary items.
    """

    local_itempool: list[SekiroItem] = []
    """The pool of all items within this particular world. This is a subset of
    `self.multiworld.itempool`."""

    def __init__(self, multiworld: MultiWorld, player: int):
        super().__init__(multiworld, player)
        self.all_excluded_locations = set()

    def generate_early(self) -> None:
        # UT yamlless support
        # re_gen_passthrough = getattr(self.multiworld, "re_gen_passthrough", {})
        # if re_gen_passthrough and self.game in re_gen_passthrough:
        #     # Get the passed through slot data from the real generation
        #     slot_data: dict[str, Any] = re_gen_passthrough[self.game]
        #
        #     slot_options: dict[str, Any] = slot_data.get("options", {})
        #     # Set all your options here instead of getting them from the yaml
        #     for key, value in slot_options.items():
        #         opt: Optional[Option] = getattr(self.options, key, None)
        #         if opt is not None:
        #             # You can also set .value directly but that won't work if you have OptionSets
        #             setattr(self.options, key, opt.from_any(value))

        self.created_regions = set()
        self.all_excluded_locations.update(self.options.exclude_locations.value)

        if self.options.replace_esoteric_texts_with_skills and not self.options.randomize_skills_and_prosthetics:
            raise OptionError(
                f"Player {self.player_name} has enabled skills as items but not randomized skill trees. "
                f"Please fix your options by either enabling both or disabling the skills as item pickups.")

    def create_regions(self) -> None:
        # Create Game Regions
        regions: dict[str, Region] = {"Menu": self.create_region("Menu", {})}
        regions.update({region_name: self.create_region(region_name, location_tables[region_name]) for region_name in [
            "Tutorial",
            "Dilapidated Temple",
            "Ashina Outskirts",
            "Hirata Estate (Young Lord's Bell Charm)",
            "Ashina Castle",
            "Ashina Reservoir",
            "Abandoned Dungeon",
            "Senpou Temple, Mt. Kongo",
            "Sunken Valley",
            "Sunken Valley Passage",
            "Poison Pool",
            "Hidden Forest",
            "Mibu Village",
            "Ashina Castle (Interior Ministry)",
        ]})

        # Create Full game regions only if option is not Shura
        if self.options.goal_option == 0:
            regions.update({region_name: self.create_region(region_name, location_tables[region_name]) for region_name in [
                "Hirata Estate (Father's Bell Charm)",
                "Fountainhead Palace (before underwater progression)",
                "Fountainhead Palace (underwater progression)",
                "Ashina Castle (Central Forces)",
                "Ashina Outskirts (Central Forces)",
                "Ashina Reservoir (Central Forces)",
                ]})

        # Connect Regions
        def create_connection(from_region: str, to_region: str):
            connection = Entrance(self.player, f"Go To {to_region}", regions[from_region])
            regions[from_region].exits.append(connection)
            connection.connect(regions[to_region])

        regions["Menu"].exits.append(Entrance(self.player, "New Game", regions["Menu"]))
        self.multiworld.get_entrance("New Game", self.player).connect(regions["Tutorial"])

        create_connection("Tutorial", "Dilapidated Temple")

        create_connection("Dilapidated Temple", "Ashina Outskirts")
        create_connection("Dilapidated Temple", "Hirata Estate (Young Lord's Bell Charm)")

        create_connection("Ashina Outskirts", "Ashina Castle")

        create_connection("Ashina Castle", "Ashina Reservoir")
        create_connection("Ashina Castle", "Abandoned Dungeon")
        create_connection("Ashina Castle", "Sunken Valley")

        create_connection("Ashina Castle", "Ashina Castle (Interior Ministry)")

        create_connection("Abandoned Dungeon", "Senpou Temple, Mt. Kongo")
        create_connection("Abandoned Dungeon", "Poison Pool")

        create_connection("Sunken Valley", "Sunken Valley Passage")

        create_connection("Poison Pool", "Hidden Forest")

        create_connection("Hidden Forest", "Mibu Village")

        # Region connections for full game
        if self.options.goal_option == 0:
            create_connection("Hirata Estate (Young Lord's Bell Charm)",
                              "Hirata Estate (Father's Bell Charm)")

            create_connection("Ashina Castle (Interior Ministry)",
                              "Fountainhead Palace (before underwater progression)")

            create_connection("Fountainhead Palace (before underwater progression)",
                              "Fountainhead Palace (underwater progression)")

            create_connection("Fountainhead Palace (underwater progression)",
                              "Ashina Castle (Central Forces)")

            create_connection("Ashina Castle (Central Forces)", "Ashina Outskirts (Central Forces)")
            create_connection("Ashina Castle (Central Forces)", "Ashina Reservoir (Central Forces)")

    # For each region, add the associated locations retrieved from the corresponding location_table
    def create_region(self, region_name, location_table) -> Region:
        new_region = Region(region_name, self.player, self.multiworld)

        # Use this to un-exclude event locations so the fill doesn't complain about items behind
        # them being unreachable.
        excluded = self.options.exclude_locations.value

        for location in location_table:
            if self._is_location_available(location):
                new_location = SekiroLocation(self.player, location, new_region)
                if (
                    # Exclude missable locations that don't allow useful items
                    location.is_missable(self.options) and self.options.missable_location_behavior == "forbid_useful"
                    and not (
                        # Unless they are excluded to a higher degree already
                        location.name in self.all_excluded_locations
                        and self.options.missable_location_behavior < self.options.excluded_location_behavior
                    )
                ):
                    new_location.progress_type = LocationProgressType.EXCLUDED
            else:
                # Don't consider non-randomized locations to be AP-excluded
                if location.name in excluded:
                    excluded.remove(location.name)
                    # Only remove from all_excluded if excluded does not have priority over missable
                    if not (self.options.missable_location_behavior < self.options.excluded_location_behavior):
                        self.all_excluded_locations.remove(location.name)

                # Don't create ending-based unreachable locations in regions accessible in both endings.
                if location.shura and self.options.goal_option == 0: continue
                if location.full_game and self.options.goal_option == 1: continue

                # Don't create region entrance event locations if region locks are enabled.
                if location.name.__contains__("->") and self.options.additional_region_locks: continue

                # Replace non-randomized items with events that give the default item
                event_item = (
                    self.create_item(location.default_item_name) if location.default_item_name
                    else SekiroItem.event(location.name, self.player)
                )

                new_location = SekiroLocation(
                    self.player,
                    location,
                    parent = new_region,
                )
                new_location.place_locked_item(event_item)

            new_region.locations.append(new_location)

        self.multiworld.regions.append(new_region)
        self.created_regions.add(region_name)
        return new_region

    def create_items(self) -> None:
        # Just used to efficiently deduplicate items
        item_set: set[str] = set()

        # Gather all default items on randomized locations
        self.local_itempool = []
        num_required_extra_items = 0
        for location in cast(list[SekiroLocation], self.multiworld.get_unfilled_locations(self.player)):
            if not self._is_location_available(location.name):
                raise Exception("Sekiro generation bug: Added an unavailable location.")

            default_item_name = cast(str, location.data.default_item_name)
            item = item_dictionary[default_item_name]
            if item.skip:
                num_required_extra_items += 1
            elif not item.unique:
                self.local_itempool.append(self.create_item(default_item_name))
            else:
                # For unique items, make sure there aren't duplicates in the item set even if there
                # are multiple in-game locations that provide them.
                if default_item_name in item_set:
                    num_required_extra_items += 1
                # Remove Esoteric Texts from the itempool if the option is enabled to turn Skills into items.
                elif self.options.replace_esoteric_texts_with_skills and "Esoteric Text" in item.name:
                    num_required_extra_items += 1
                else:
                    item_set.add(default_item_name)
                    self.local_itempool.append(self.create_item(default_item_name))
        injectables = self._create_injectable_items(num_required_extra_items)
        num_required_extra_items -= len(injectables)
        self.local_itempool.extend(injectables)

        # Extra filler items for locations containing skip items
        self.local_itempool.extend(self.create_item(self.get_filler_item_name()) for _ in range(num_required_extra_items))

        # Potentially fill some items locally and remove them from the itempool
        self._fill_local_items()

        # Add items to itempool
        self.multiworld.itempool += self.local_itempool

    def _create_injectable_items(self, num_required_extra_items: int) -> list[SekiroItem]:
        """Returns a list of items to inject into the multiworld instead of skipped items.

        If there isn't enough room to inject all the necessary progression items
        that are in missable locations by default, this adds them to the
        player's starting inventory.
        """

        all_injectable_items = [
            item for item
            in item_dictionary.values()
            if item.inject
        ]

        # Add region lock items to the item pool if the option is selected.
        if self.options.additional_region_locks:
            for item in region_lock_dictionary.values():
                all_injectable_items.append(item)

        # Add skills as actual items if option is selected. Remove comments when implemented!
        if self.options.replace_esoteric_texts_with_skills:
            for item in skill_pickup_dictionary.values():
                all_injectable_items.append(item)

        # Make skills mandatory as injection.
        injectable_mandatory = [
            item for item in all_injectable_items
            if item.classification & ItemClassification.progression or item.category == 1
        ]
        injectable_optional = [
            item for item in all_injectable_items
            if item.classification != ItemClassification.progression or not item.category == 1
        ]
        number_to_inject = min(num_required_extra_items, len(all_injectable_items))
        items = (
            self.random.sample(
                injectable_mandatory,
                k=min(len(injectable_mandatory), number_to_inject)
            )
            + self.random.sample(
                injectable_optional,
                k=max(0, number_to_inject - len(injectable_mandatory))
            )
        )
        if number_to_inject < len(injectable_mandatory):
            # It's worth considering the possibility of _removing_ unimportant
            # items from the pool to inject these instead rather than just
            # making them part of the starting health back
            pool_items = self.local_itempool
            removable_filler = [
                item for item
                in pool_items
                if item_dictionary[item.name].filler
            ]
            for item in injectable_mandatory:
                if item in items:
                    continue
                if not removable_filler:
                    raise OptionError(
                        f"Player {self.player_name} has disabled randomization of excluded locations while enabling the"
                        f" option for skills being item pickups and / or additional region locks. "
                        f"Please fix your options by either randomizing or reducing excluded locations. "
                        f"Alternatively please disable the skills as item pickups / additional region locks options."
                    )
                filler_choice = self.random.choice(removable_filler)
                self.local_itempool.remove(filler_choice)
                removable_filler.remove(filler_choice)
                items.append(item)

        return [self.create_item(item) for item in items]

    def create_item(self, item: str | SekiroItemData) -> SekiroItem:
        data = item if isinstance(item, SekiroItemData) else item_dictionary[item]
        classification = None

        return SekiroItem(self.player, data, classification=classification)

    def _fill_local_items(self) -> None:
        """Removes certain items from the item pool and manually places them in the local world.

        We can't do this in pre_fill because the itempool may not be modified after create_items.
        """
        # If using very early Hirata setting with Prosthetic and Bell Charm randomized, place one of the items early.
        # Don't place this item in the multiworld because it is necessary almost immediately.
        if (self.options.very_early_hirata
                and self._is_location_available("DT: Shinobi Prosthetic - complete Tutorial")
                and self._is_location_available("AO: Young Lord's Bell Charm - Inosuke's Mother")):
                itemlist = ["Shinobi Prosthetic", "Young Lord's Bell Charm"]
                randomitem = self.random.choice(itemlist)
                self._fill_local_item(randomitem, ["Dilapidated Temple"],
                                      lambda location: location.name == "DT: Shinobi Prosthetic - complete Tutorial")

        # If no very early Hirata is selected, place the Prosthetic early.
        # Don't place this in the multiworld because it's necessary almost immediately.
        if (not self.options.very_early_hirata
                and self._is_location_available("DT: Shinobi Prosthetic - complete Tutorial")):
                self._fill_local_item("Shinobi Prosthetic", ["Dilapidated Temple"],
                                      lambda location: location.name == "DT: Shinobi Prosthetic - complete Tutorial")

        # Local quick hirata option only if very_early_hirata did not already place the item.
        if self.options.quick_hirata == 'early_local' and "Young Lord's Bell Charm" not in self.multiworld.get_items():
            self._fill_local_item("Young Lord's Bell Charm", ["Ashina Outskirts"])

        # Keep Mushin location unrandomized unless the item is disabled due to the skills being pickups.
        if not self.options.replace_esoteric_texts_with_skills:
            self._fill_local_item("Mushin Esoteric Text", ["Ashina Castle"], lambda location:
                                  location.name == "AC: Mushin Esoteric Text - Tengu after unlocking special technique")

    def _fill_local_item(
        self, name: str,
        regions: list[str],
        additional_condition: Callable[[SekiroLocationData], bool] | None = None,
    ) -> None:
        """Chooses a valid location for the item with the given name and places it there.

        This always chooses a local location among the given regions. If additional_condition is
        passed, only locations meeting that condition will be considered.

        If the item could not be placed, it will be added to starting inventory.
        """
        item = next((item for item in self.local_itempool if item.name == name), None)
        if not item: return

        candidate_locations = [
            location for location in (
                self.multiworld.get_location(location.name, self.player)
                for region in regions
                for location in location_tables[region]
                if self._is_location_available(location)
                and not location.is_missable(self.options)
                and not location.conditional
                and (not additional_condition or additional_condition(location))
            )
            # We can't use location.progress_type here because it's not set
            # until after `set_rules()` runs.
            if not location.item and location.name not in self.all_excluded_locations
            and location.item_rule(item)
        ]

        self.local_itempool.remove(item)

        if not candidate_locations:
            warning(f"Couldn't place \"{name}\" in a valid location for {self.player_name}. Adding it to starting inventory instead.")
            location = next(
                (location for location in self._get_our_locations() if location.data.default_item_name == item.name),
                None
            )
            if location: self._replace_with_filler(location)
            self.multiworld.push_precollected(self.create_item(name))
            return

        location = self.random.choice(candidate_locations)
        location.place_locked_item(item)

    def _replace_with_filler(self, location: SekiroLocation) -> None:
        """If possible, choose a filler item to replace location's current contents with."""
        if location.locked: return

        # Try 10 filler items. If none of them work, give up and leave it as-is.
        for _ in range(0, 10):
            candidate = self.create_filler()
            if location.item_rule(candidate):
                location.item = candidate
                return

    def get_filler_item_name(self) -> str:
        return self.random.choice(filler_item_names)

    def set_rules(self) -> None:
        randomized_items = {item.name for item in self.local_itempool}

        self._add_npc_rules()
        self._add_prosthetic_rules()
        self._add_mibu_rules()
        self._add_allow_useful_location_rules()
        self._add_early_item_rules(randomized_items)

        self._add_entrance_rule("Ashina Outskirts", "Shinobi Prosthetic")
        self._add_entrance_rule("Hirata Estate (Young Lord's Bell Charm)", "Young Lord's Bell Charm")

        # Add rules for custom keys if option is enabled
        if self.options.additional_region_locks:
            self._add_entrance_rule("Ashina Castle", "Ashina Requisitions Whistle")
            self._add_entrance_rule("Abandoned Dungeon", "Abandoned Dungeon Key")
            self._add_entrance_rule("Senpou Temple, Mt. Kongo", "Senpou Temple Key")
            self._add_entrance_rule("Sunken Valley", "Bell of Dispelling")
            self._add_entrance_rule("Poison Pool", "Ashina Depths Key")
        else:
            self._add_entrance_rule("Ashina Castle", lambda state: (
                self._can_get(state, "AO: Memory: Gyoubu Oniwa")
            ))
            self._add_entrance_rule("Senpou Temple, Mt. Kongo", "AD -> ST")
            self._add_entrance_rule("Sunken Valley", "AC -> SV")
            self._add_entrance_rule("Poison Pool", "AD -> PP")

        self._add_entrance_rule("Sunken Valley Passage", lambda state: (
                state.has("Gun Fort Shrine Key", self.player)
                and self._can_get(state, "SV: Prayer Bead - Gun Fort shrine, miniboss drop")
        ))
        # Since you can skip Headless if you early, we assume this is in logic.
        self._add_entrance_rule("Hidden Forest", lambda state: (
            self._can_get(state, "PP: Prayer Bead - miniboss drop")
        ))
        self._add_entrance_rule("Mibu Village", lambda state: (
            self._can_get(state, "HF: Lump of Grave Wax - temple, miniboss drop")
        ))

        self._add_entrance_rule("Ashina Castle (Interior Ministry)", lambda state: (
                state.has("Shelter Stone", self.player)
                and state.has("Lotus of the Palace", self.player)
                and state.has("Mortal Blade", self.player)
                and self._can_get(state, "AC: Immortal Severance Text - Kuro")
                and ( self._can_go_to(state, "Poison Pool") or
                      self._can_go_to(state, "Senpou Temple, Mt. Kongo") or
                      self._can_go_to(state, "Sunken Valley") or
                      self._can_go_to(state, "Hirata Estate (Young Lord's Bell Charm)"))
        ))

        # Indirect conditions for Interior ministry invasion trigger.
        self.multiworld.register_indirect_condition(self.get_region("Poison Pool"),
                                                    self.get_entrance("Go To Ashina Castle (Interior Ministry)"))
        self.multiworld.register_indirect_condition(self.get_region("Senpou Temple, Mt. Kongo"),
                                                    self.get_entrance("Go To Ashina Castle (Interior Ministry)"))
        self.multiworld.register_indirect_condition(self.get_region("Sunken Valley"),
                                                    self.get_entrance("Go To Ashina Castle (Interior Ministry)"))
        self.multiworld.register_indirect_condition(self.get_region("Hirata Estate (Young Lord's Bell Charm)"),
                                                    self.get_entrance("Go To Ashina Castle (Interior Ministry)"))


        # Only if full game is selected
        if self.options.goal_option == 0:
            # Make HE2 dependent on HE1 boss to avoid these locations being missable
            self._add_entrance_rule("Hirata Estate (Father's Bell Charm)", lambda state: (
                    state.has("Father's Bell Charm", self.player)
                    and self._can_get(state, "HE1: Memory: Lady Butterfly")
            ))
            self._add_entrance_rule("Fountainhead Palace (before underwater progression)", lambda state: (
                    state.has("Aromatic Branch", self.player)
                    and self._can_get(state, "AC/I: Memory: Great Shinobi")
                    and self._can_get(state, "MV: Memory: Corrupted Monk")
            ))

            # Indirect condition to check if Mibu village is accessible at the time of needing to enter Fountainhead
            self.multiworld.register_indirect_condition(self.get_region("Mibu Village"),
                self.get_entrance("Go To Fountainhead Palace (before underwater progression)"))

            self._add_entrance_rule("Fountainhead Palace (underwater progression)", lambda state: (
                state.has("Mibu Breathing Technique", self.player)
            ))
            self._add_entrance_rule("Ashina Castle (Central Forces)", lambda state: (
                self._can_get(state, "FP2: Divine Dragon's Tears - Sanctuary, boss drop")
            ))

        # Define the access rules to some specific locations
        self._add_location_rule("DT: Hidden Tooth - complete Hanbei's quest", "Mortal Blade")
        self._add_location_rule("DT: Ashina Sake - Emma after healing Sculptor's dragonrot",
                                lambda state: (
                                    self._can_get(state, "AC: Memory: Genichiro")
                                ))

        # Have 3 Prosthetic materials for this check to become reachable
        prosthetics = ["Shuriken Wheel", "Robert's Firecrackers", "Flame Barrel", "Shinobi Axe of the Monkey",
                       "Mist Raven's Feathers", "Sabimaru", "Iron Fortress", "Large Fan", "Gyoubu's Broken Horn",
                       "Slender Finger"]
        self._add_location_rule("DT: Prosthetic Esoteric Text - talk to Sculptor with 3 prosthetic tools"
                                , lambda state: (state.has_from_list(prosthetics, self.player, 3)
                                                 and state.has("Shinobi Prosthetic", self.player)))

        # Similar to above, but much simpler. Making sure this does not BK Prosthetic/Bell
        # Since the option makes XP more scarce, make sure you can access Ashina Castle to guarantee there is enough XP.
        if self.options.replace_esoteric_texts_with_skills:
            self._add_location_rule("DT: Shinobi Esoteric Text - talk to Sculptor with 1 skill point"
                                    , lambda state: (
                    self._can_get(state, "AC: Memory: Genichiro")
            ))
        else:
            self._add_location_rule("DT: Shinobi Esoteric Text - talk to Sculptor with 1 skill point"
                                    , lambda state: (
                    self._can_get(state, "AO: Prayer Bead - before lookout building, miniboss drop")
            ))
        # Make the Headless location require AC access, just to make sure this doesn't lock early with no confetti.
        if not self.options.randomize_headless or not self.options.enemy_randomizer:
            self._add_location_rule([
                "AO: Ako's Spiritfall - headless cave, miniboss drop",
            ], lambda state: self._can_get(state, "AC: Memory: Genichiro"))

        self._add_location_rule([
            "HE1: Memory: Lady Butterfly",
            "HE1: Sakura Droplet - boss drop",
        ], lambda state: state.has("Hidden Temple Key", self.player))

        self._add_location_rule([
            "AC: Scrap Magnetite - Kuro's room, behind statue"
        ], lambda state: (
            self._can_get(state, "AC: Memory: Genichiro")
        ))

        self._add_location_rule([
            "AC: Gun Fort Shrine Key - Kuro's library"
        ], lambda state: (
            self._can_get(state, "AC: Unrefined Sake - Isshin")
        ))

        if self.options.replace_esoteric_texts_with_skills:
            self._add_location_rule([
                "AC: Mushin Esoteric Text - Tengu after unlocking special technique"
            ], lambda state: (
                self._can_get(state, "AC: Memory: Genichiro")
                and state.has_any(["Shadowrush", "Living Force", "Ashina Cross", "High Monk"], self.player)
            ))
        else:
            # Make this only accessible in mid-game due to skill requirements. (This will contain Mushin anyway..)
            # Dependent on having Ashina Esoteric Text because Isshin can get stuck on dialogue without it.
            self._add_location_rule([
                "AC: Mushin Esoteric Text - Tengu after unlocking special technique"
            ], lambda state: (
                self._can_go_to(state, "Ashina Castle (Interior Ministry)")
                and state.has("Ashina Esoteric Text", self.player)
            ))

        # Add access rule for region lock as this is behind the fog wall
        if self.options.additional_region_locks:
            self._add_location_rule([
                "AC: Eel Liver - shrine across from serpent shrine"
            ], lambda state: (
                state.has("Bell of Dispelling", self.player)
            ))

        self._add_location_rule([
            "AR: Gyoubu's Broken Horn - gatehouse, chest",
            "AR: Heavy Coin Purse - gatehouse, next to chest"
        ], lambda state: state.has("Gatehouse Key", self.player))

        self._add_location_rule([
            "ST: Mortal Blade - Divine Child",
            "ST: Pellet - behind Inner Sanctum building"
        ], lambda state: self._can_get(state, "ST: Puppeteer Ninjutsu - Halls of Illusion, boss drop"))

        self._add_location_rule([
            "ST: Holy Chapter: Infested - underwater, carp pond"
        ], lambda state: self._can_get(state, "AC: Scrap Magnetite - Kuro's room, behind statue"))

        self._add_location_rule([
            "ST: Rice for Kuro - Divine Child for Persimmon"
        ], lambda state: (
                state.has("Persimmon", self.player)
                and self._can_get(state, "ST: Mortal Blade - Divine Child")
        ))

        self._add_location_rule([
            "ST: Holy Chapter: Dragon's Return - cave, blue-robed corpse after Holy Chapter: Infested"
        ], lambda state: (
                state.has("Holy Chapter: Infested", self.player)
                and self._can_get(state, "ST: Rice for Kuro - Divine Child for Persimmon")
        ))

        self._add_location_rule([
            "ST: Frozen Tears - Divine Child for both Serpent Viscera after first invasion"
        ], lambda state: (
                state.has("Dried Serpent Viscera", self.player)
                and state.has("Fresh Serpent Viscera", self.player)
                and self._can_get(state, "ST: Holy Chapter: Dragon's Return - "
                                         "cave, blue-robed corpse after Holy Chapter: Infested")
                and self._can_get(state, "AC/I: Memory: Great Shinobi")
        ))

        self._add_location_rule([
            "ST: Mibu Balloon of Spirit - after Sunken Valley Cavern idol",
            "ST: Scrap Magnetite - before Sunken Valley Cavern idol",
            "ST: Snap Seed - after kite jump"
        ], lambda state: (
            state.has("Puppeteer Ninjutsu", self.player)
        ))

        self._add_location_rule([
            "SVP: Bundled Jizo Statue - Sunken Valley Cavern, after killing serpent",
            "SVP: Dragon's Blood Droplet - Sunken Valley Cavern, after killing serpent",
            "SVP: Fresh Serpent Viscera - Sunken Valley Cavern, plunge kill serpent, enemy drop",
            "SVP: Mibu Balloon of Soul - Sunken Valley Cavern, lake overlook after killing serpent"
        ], lambda state: (
            self._can_get(state, "ST: Snap Seed - after kite jump")
        ))

        self._add_location_rule([
            "SVP: Divine Confetti - underground shrine, ledge above",
            "SVP: Dried Serpent Viscera - underground shrine, statue",
            "SVP: Mibu Balloon of Soul - underground shrine, back porch"
        ], lambda state: (
                state.has("Puppeteer Ninjutsu", self.player)
                or state.has("Mist Raven's Feathers", self.player)
        ))

        self._add_location_rule([
            "SVP: Great White Whisker - Guardian Ape's Watering Hole, after killing Giant Carp"
        ], lambda state: (
                self.has_any_truly_precious_bait(state)
                and self._can_get(state, "FP2: Treasure Carp Scale - Feeding Grounds, feed Great Carp twice")
        ))

        self._add_location_rule([
            "PP: Memory: Headless Ape",
            "PP: Prayer Bead - Guardian Ape's Burrow, boss drop #1",
            "PP: Prayer Bead - Guardian Ape's Burrow, boss drop #2",
        ], lambda state: (
            self._can_get(state, "SVP: Memory: Guardian Ape")
        ))

        self._add_location_rule([
            "PP: Bestowal Ninjutsu - Guardian Ape's Burrow, boss drop"
        ], lambda state: (
                self._can_get(state, "SVP: Memory: Guardian Ape")
                and state.has("Mortal Blade", self.player)
        ))

        self._add_location_rule([
            "PP: Malcontent's Ring - Guardian Ape's Burrow, miniboss drop"
        ], lambda state: (
                self._can_get(state, "PP: Bestowal Ninjutsu - Guardian Ape's Burrow, boss drop")
                and state.has("Slender Finger", self.player)
                and self._can_go_to(state, "Hidden Forest")
        ))

        self._add_location_rule([
            "MV: Dragonspring Sake - Head Priest for Water of the Palace"
        ], lambda state: (
            state.has("Water of the Palace", self.player)
        ))

        self._add_location_rule([
            "MV: Treasure Carp Scale - Head Priest's house, enemy drop"
        ], lambda state: (
            self._can_get(state, "MV: Dragonspring Sake - Head Priest for Water of the Palace")
        ))

        self._add_location_rule([
            "MV: Shelter Stone - Wedding Cave"
        ], lambda state: (
            self._can_get(state, "MV: Memory: Corrupted Monk")
        ))

        self._add_location_rule("FP2: Treasure Carp Scale - Feeding Grounds, feed Great Carp once",
                                lambda state: state.has("Precious Bait", self.player))

        self._add_location_rule(
            "FP2: Treasure Carp Scale - Feeding Grounds, feed Great Carp twice",
            lambda state: (
                    self._can_get(state, "FP2: Treasure Carp Scale - Feeding Grounds, feed Great Carp once")
                    and state.has("Precious Bait", self.player)
            ))

        self._add_location_rule(
            "FP2: Divine Grass - Feeding Grounds, Attendant for Great White Whisker",
            lambda state: (
                state.has("Great White Whisker", self.player)
                and self._can_get(state,
                                  "SVP: Great White Whisker - Guardian Ape's Watering Hole, after killing Giant Carp")
            ))

        self._add_location_rule([
            "AR/C: Dragon Flash - final boss drop",
            "AR/C: Memory: Saint Isshin"
        ], lambda state: state.has("Secret Passage Key", self.player))


        # Forbid shops from carrying items with multiple counts (the static randomizer has its own
        # logic for choosing how many shop items to sell).
        for location in location_dictionary.values():
            if location.shop:
                self._add_item_rule(
                    location.name,
                    lambda item: (
                            item.player != self.player or
                            (item.data.count == 1)
                    )
                )

        # Completion condition depending on selected ending
        if self.options.goal_option == 0:
            self.multiworld.completion_condition[self.player] = lambda state: (
                self._can_get(state, "AR/C: Memory: Saint Isshin")
                and state.has("Divine Dragon's Tears", self.player)
            )
        else:
            self.multiworld.completion_condition[self.player] = lambda state: (
                self._can_get(state, "AC/I: Memory: Isshin Ashina")
            )

    def _add_prosthetic_rules(self) -> None:
        """Adds rules for items that need the prosthetic in case of early Hirata setting.

        These Hirata locations cannot be reached without the Shinobi Prosthetic, therefore we implement
        logic to eliminate a BK if the prosthetic is in the multiworld."""

        grapple_locations = {
            "HE1: Bulging Coin Purse - side path before cave, enemy drop",
            "HE1: Ceramic Shard - Main Hall, island in the marsh",
            "HE1: Contact Medicine - by tunnel to three-story pagoda",
            "HE1: Divine Confetti - Audience Chamber, shinobi door",
            "HE1: Divine Confetti - Main Hall, large building before marsh",
            "HE1: Dousing Powder - Audience Chamber, left room",
            "HE1: Dousing Powder - Bamboo Thicket Slope, grapple from first ledge",
            "HE1: Dousing Powder - Main Hall, large building before marsh",
            "HE1: Light Coin Purse - Audience Chamber, shinobi door",
            "HE1: Light Coin Purse - Main Hall, left building after marsh",
            "HE1: Memory: Lady Butterfly",
            "HE1: Mibu Balloon of Soul - Audience Chamber, room left of idol",
            "HE1: Mibu Balloon of Soul - side path before cave",
            "HE1: Mibu Balloon of Wealth - Audience Chamber, shinobi door",
            "HE1: Mibu Possession Balloon - side path before cave, crouch opening",
            "HE1: Mist Raven's Feathers - three-story pagoda",
            "HE1: Oil - Audience Chamber, left hallway before shinobi door",
            "HE1: Oil - Main Hall, between well and idol",
            "HE1: Pellet - Audience Chamber, left room",
            "HE1: Pellet - side path before cave",
            "HE1: Prayer Bead - Audience Chamber, shinobi door chest",
            "HE1: Prayer Bead - Main Hall, miniboss drop",
            "HE1: Sakura Droplet - boss drop",
            "HE1: Scrap Iron - three-story pagoda, enemy drop",
            "HE1: Snap Seed - Audience Chamber, Inosuke",
            "HE1: Unrefined Sake - Main Hall, miniboss drop",
        }

        for location in sorted(grapple_locations):
            self._add_location_rule(location, lambda state: state.has("Shinobi Prosthetic", self.player))

    def _add_npc_rules(self) -> None:
        """Adds rules for items accessible via NPC quests.

        We list missable locations here even though they never contain progression items so that the
        game knows what sphere they're in.

        Generally, for locations that can be accessed early by killing NPCs, we set up requirements
        assuming the player _doesn't_ so they aren't forced to start killing allies to advance the
        quest.
        """

        ## Fujioka

        # Gate this behind Geni, because that is when Fujioka is force moved to DT,
        # if for whatever reason someone doesn't unlock him before
        self._add_location_rule([
            "DT: Gourd Seed - Fujioka the Info Broker",
            "DT: Sabimaru Memo - Fujioka the Info Broker",
            "DT: Three-story Pagoda Memo - Fujioka the Info Broker"
        ], lambda state: (
            self._can_get(state, "AC: Memory: Genichiro")
        ))

        self._add_location_rule([
            "DT: Valley Apparitions Memo - Fujioka after boss killed in Guardian Ape's Burrow"
        ], lambda state: (
            self._can_get(state, "PP: Bestowal Ninjutsu - Guardian Ape's Burrow, boss drop")
            and self._can_go_to(state, "Hidden Forest")
        ))

        ## Anayama
        self._add_location_rule("AO: Oil - Anayama with Flame Barrel", "Flame Barrel")

        self._add_location_rule("AO/C: Promissory Note - Anayama the Peddler", "Red and White Pinwheel")

        ## Tengu
        self._add_location_rule([
            "AO: Ashina Esoteric Text - Tengu after killing rats"
        ], lambda state: (
            self._can_get(state, "AO: Black Gunpowder - Tengu rat quest, enemy drop")
        ))

        ## Kuro
        self._add_location_rule([
            "AC: Immortal Severance Text - Kuro"
        ], lambda state: (
            self._can_get(state, "AC: Memory: Genichiro")
        ))

        self._add_location_rule([
            "AC: Fragrant Flower Note - Kuro"
        ], lambda state: (
            self._can_get(state, "AC: Unrefined Sake - Isshin")
        ))

        self._add_location_rule([
            "AC: Page's Diary - Kuro",
        ], lambda state: (
            ( state.has("Shelter Stone", self.player) or state.has("Lotus of the Palace", self.player) )
            and self._can_get(state, "AC: Immortal Severance Text - Kuro")
        ))

        self._add_location_rule([
            "AC: Okami's Ancient Text - Kuro",
        ], lambda state: (
            state.has("Shelter Stone", self.player)
            and self._can_get(state, "AC: Immortal Severance Text - Kuro")
        ))

        self._add_location_rule([
            "AC: Sweet Rice Ball - Kuro for Rice for Kuro"
        ], lambda state:
        state.has("Rice for Kuro", self.player)
        and self._can_get(state, "AC: Memory: Genichiro"))

        self._add_location_rule([
            "AC/I: Sweet Rice Ball - Kuro after incense and Rice for Kuro"
        ], lambda state: (
                self._can_get(state, "AC: Sweet Rice Ball - Kuro for Rice for Kuro")
                and self._can_go_to(state, "Fountainhead Palace (before underwater progression)")
        ))

        self._add_location_rule([
            "AC/I: Divine Grass - Kuro after entering Fountainhead Palace"
        ], lambda state: (
            self._can_go_to(state, "Fountainhead Palace (before underwater progression)")
        ))

        ## Emma
        self._add_location_rule([
            "AC: Immortal Severance Scrap - Emma"
        ], lambda state: (
            self._can_get(state, "AC: Page's Diary - Kuro")
        ))

        self._add_location_rule([
            "AC/I: Tomoe's Note - Emma after eavesdropping on Kuro"
        ], lambda state: (
            self._can_get(state, "AC/I: Memory: Great Shinobi")
        ))

        self._add_location_rule([
            "AC/I: Father's Bell Charm - Emma after eavesdropping on her"
        ], lambda state: (
            self._can_get(state, "AC/I: Tomoe's Note - Emma after eavesdropping on Kuro")
        ))

        ## Isshin
        self._add_location_rule([
            "AC: Unrefined Sake - Isshin"
        ], lambda state: (
            self._can_get(state, "AC: Immortal Severance Text - Kuro")
        ))

        ## Doujun
        self._add_location_rule([
            "AD: Lump of Fat Wax - Doujun after sending subject"
        ], lambda state: (
            self._can_get(state, "AD: Surgeon's Bloody Letter - start Doujun's quest")
            and self._can_get(state, "AR: Prayer Bead - starting well, miniboss drop")
        ))

        self._add_location_rule([
            "AD: Surgeon's Stained Letter - Doujun requests Red Carp Eyes"
        ], lambda state: (
            self._can_get(state, "AD: Lump of Fat Wax - Doujun after sending subject")
        ))

        self._add_location_rule([
            "AD: Lump of Grave Wax - Doujun for Red Carp Eyes"
        ], lambda state: (
            state.has("Red Carp Eyes", self.player)
            and self._can_get(state, "AD: Surgeon's Stained Letter - Doujun requests Red Carp Eyes")
        ))

        self._add_location_rule([
            "AD: Red Lump - Underground Waterway island, red-eyed Jinzaemon, enemy drop",
            "AD: Red Lump - Underground Waterway island, red-eyed Kotaro, enemy drop",
            "AD: Academics' Red Lump - Underground Waterway island, red-eyed Doujun, enemy drop"
        ], lambda state: (
            self._can_get(state, "AD: Lump of Grave Wax - Doujun for Red Carp Eyes")
        ))

        ## Kotaro
        self._add_location_rule([
            "ST: Taro Persimmon - Halls of Illusion, Kotaro quest"
        ], lambda state: (
            state.has("White Pinwheel", self.player)
            and state.has("Large Fan", self.player)
            and self._can_get(state, "ST: Puppeteer Ninjutsu - Halls of Illusion, boss drop")
        ))

        ## Jinzaemon
        self._add_location_rule([
            "MV: Jinza's Jizo Statue - Jinzaemon reward after killing miniboss"
        ], lambda state: (
            self._can_get(state, "MV: Prayer Bead - miniboss drop")
        ))

        ## Pot Noble Harunaga
        # Add Carp Scale logic for the shop inventory as we do not randomize prices here.
        # Make these progressive to make sure they do not place carp scales here blocking the location.
        self._add_location_rule([
            "HE1: Floating Passage Text - Pot Noble Harunaga",
        ], lambda state: state.has("Treasure Carp Scale", self.player, 8))

        self._add_location_rule([
            "HE1: Divine Grass - Pot Noble Harunaga"
        ], lambda state: state.has("Treasure Carp Scale", self.player, 1))

        self._add_location_rule([
            "HE1: Withered Red Gourd - Pot Noble Harunaga",
        ], lambda state: state.has("Treasure Carp Scale", self.player, 3))

        self._add_location_rule([
            "HE1: Mask Fragment: Right - Pot Noble Harunaga",
        ], lambda state: state.has("Treasure Carp Scale", self.player, 15))

        self._add_location_rule([
            "HE1: Truly Precious Bait - Pot Noble Harunaga after trading 6 scales",
        ], lambda state: (
            self._can_go_to(state, "Fountainhead Palace (before underwater progression)")
            and state.has("Treasure Carp Scale", self.player, 6)
        ))

        self._add_location_rule([
            "HE1: Lapis Lazuli - Pot Noble Harunaga after Truly Precious Bait",
        ], lambda state: (
                self._can_go_to(state, "Fountainhead Palace (underwater progression)")
                and self._can_get(state, "SVP: Great White Whisker - "
                                         "Guardian Ape's Watering Hole, after killing Giant Carp")
                and self._can_get(state, "HE1: Truly Precious Bait - Pot Noble Harunaga after trading 6 scales")
        ))

        ## Pot Noble Koremori
        # Add Carp Scale logic for the shop inventory as we do not randomize prices here. Progressive with Harunaga.
        self._add_location_rule([
            "FP1: Mask Fragment: Left - Pot Noble Koremori",
        ], lambda state: state.has("Treasure Carp Scale", self.player, 28))

        self._add_location_rule([
            "FP1: Dragon's Blood Droplet - Pot Noble Koremori"
        ], lambda state: state.has("Treasure Carp Scale", self.player, 16))

        self._add_location_rule(
            "FP1: Truly Precious Bait - Pot Noble Koremori after 9 scales",
            lambda state: self._can_get(state, "FP1: Mask Fragment: Left - Pot Noble Koremori"))

        self._add_location_rule(
            "FP2: Lapis Lazuli - Koremori's pot after Truly Precious Bait",
            lambda state: (
                    self._can_go_to(state, "Fountainhead Palace (underwater progression)")
                    and self._can_get(state, "SVP: Great White Whisker - "
                                             "Guardian Ape's Watering Hole, after killing Giant Carp")))

        ## Blackhat Badger
        self._add_location_rule([
            "AC/C: Mibu Pilgrimage Balloon - complete Blackhat Badger quest"
        ], lambda state: (
                state.has("Puppeteer Ninjutsu", self.player)
                and self._can_get(state, "ST: Mibu Balloon of Spirit - after Sunken Valley Cavern idol")
        ))

    def _add_mibu_rules(self) -> None:
        """Adds rules for items obtainable only after obtaining Mibu Breathing Technique."""

        diving = {
            "AC: Heavy Coin Purse - underwater, lake, near headless #1",
            "AC: Heavy Coin Purse - underwater, lake, near headless #2",
            "AC: Heavy Coin Purse - underwater, lake, near headless #3",
            "AC: Mibu Possession Balloon - underwater, lake, near bridge",
            "AC: Treasure Carp Scale - underwater, by Ashina Castle idol",
            "AC: Ungo's Spiritfall - underwater, lake, headless drop",
            "AC: Yashariku's Sugar - underwater, lake, against castle wall",
            "AD: Academics' Red Lump - Underground Waterway island, red-eyed Doujun, enemy drop",
            "AD: Ceramic Shard - underwater, Underground Waterway",
            "AD: Dosaku's Note - underwater, Doujun's cell",
            "AD: Light Coin Purse - underwater, Underground Waterway #1, 3-item group",
            "AD: Light Coin Purse - underwater, Underground Waterway #2, 3-item group",
            "AD: Light Coin Purse - underwater, Underground Waterway #3, 3-item group",
            "AD: Mibu Balloon of Soul - underwater, grapple after path to Doujun's cell",
            "AD: Pacifying Agent - underwater, Doujun's cell",
            "AD: Red Lump - Underground Waterway island, red-eyed Jinzaemon, enemy drop",
            "AD: Red Lump - Underground Waterway island, red-eyed Kotaro, enemy drop",
            "AR: Mibu Balloon of Soul - underwater, starting well",
            "MV: Light Coin Purse - underwater, pond village side #1",
            "MV: Light Coin Purse - underwater, pond village side #2",
            "MV: Prayer Bead - underwater, pond chest",
            "MV: Precious Bait - underwater, river upstream from Head Priest's house",
            "MV: Red Carp Eyes - underwater, near the end of the pond, Carp drop",
            "ST: Prayer Bead - underwater, carp pond",
            "ST: Holy Chapter: Infested - underwater, carp pond",
            "SV: Divine Grass - pond cave, behind giant pillar",
            "SV: Gokan's Spiritfall - pond cave, miniboss drop",
            "SV: Lump of Grave Wax - pond cave, behind miniboss",
            "SVP: Adamantite Scrap - underwater, lake opposite from Riven Cave entrance",
            "SVP: Bulging Coin Purse - underwater, log in middle of lake",
            "SVP: Gachiin's Sugar - underwater, lake opposite from Riven Cave entrance",
            "SVP: Precious Bait - underwater, Guardian Ape's Watering Hole",
            "SVP: Treasure Carp Scale - underwater, lake at Riven Cave entrance",
            "SVP: Yashariku's Sugar - underwater, lake between rocks",
            # Carp drop locations
            "AC/I: Treasure Carp Scale - underwater, by Ashina Castle idol, Carp drop",
            "HE1: Treasure Carp Scale - underwater, Dragonspring Lake, Carp drop #1",
            "HE1: Treasure Carp Scale - underwater, Dragonspring Lake, Carp drop #2",
            "HE1: Treasure Carp Scale - underwater, under Bamboo Thicket Slope bridge, Carp drop",
            "MV: Treasure Carp Scale - underwater, near Water Mill idol, Carp drop",
            "SVP: Treasure Carp Scale - underwater, lake close to Riven Cave entrance, Carp drop",
            "SVP: Treasure Carp Scale - underwater, lake far from Riven Cave entrance, Carp drop",
        }

        # Add Full_game locations if that option is selected.
        if self.options.goal_option == 0:
            diving.update({
            "FP1: Treasure Carp Scale - Mibu Manor, dive in left corner before exit #1",
            "FP1: Treasure Carp Scale - Mibu Manor, dive in left corner before exit #2",
            "FP1: Treasure Carp Scale - Mibu Manor, dive in left corner before exit #3",
            "FP1: Water of the Palace - Mibu Manor, dive in left corner before exit, chest",
            "SVP: Great White Whisker - Guardian Ape's Watering Hole, after killing Giant Carp",
            })
        for location in sorted(diving):
            self._add_location_rule(location, lambda state: state.has("Mibu Breathing Technique", self.player))

    def _add_allow_useful_location_rules(self) -> None:
        """Adds rules for locations that can contain useful but not necessary items.

        If we allow useful items in the excluded locations, we don't want Archipelago's fill
        algorithm to consider them excluded because it never allows useful items there. Instead, we
        manually add item rules to exclude important items.
        """

        all_locations = self._get_our_locations()

        allow_useful_locations = (
            (
                {
                    location.name
                    for location in all_locations
                    if location.name in self.all_excluded_locations
                    and not location.data.is_missable(self.options)
                }
                if self.options.excluded_location_behavior < self.options.missable_location_behavior
                else self.all_excluded_locations
            )
            if self.options.excluded_location_behavior == "allow_useful"
            else set()
        ).union(
            {
                location.name
                for location in all_locations
                if location.data.is_missable(self.options)
                and not (
                    location.name in self.all_excluded_locations
                    and self.options.missable_location_behavior <
                        self.options.excluded_location_behavior
                )
            }
            if self.options.missable_location_behavior == "allow_useful"
            else set()
        )
        for location in allow_useful_locations:
            self._add_item_rule(
                location,
                lambda item: not item.advancement
            )

        # Prevent the player from prioritizing and "excluding" the same location
        self.options.priority_locations.value -= allow_useful_locations

        if self.options.excluded_location_behavior == "allow_useful":
            self.options.exclude_locations.value.clear()

    def _add_early_item_rules(self, randomized_items: set[str]) -> None:
        """Adds rules to make sure specific items are available early."""
        if "Young Lord's Bell Charm" in randomized_items:
             # Make this available pretty early for the option.
             if self.options.quick_hirata == "early_global":
                 self.multiworld.early_items[self.player]["Young Lord's Bell Charm"] = 1

    def has_any_truly_precious_bait(self, state: CollectionState) -> bool:
        return (
                state.has("Truly Precious Bait (Harunaga)", self.player)
                or state.has("Truly Precious Bait (Koremori)", self.player)
        )

    def _add_location_rule(self, location: str | list[str], rule: CollectionRule | str) -> None:
        """Sets a rule for the given location if it that location is randomized.

        The rule can just be a single item/event name as well as an explicit rule lambda.
        """
        locations = location if isinstance(location, list) else [location]
        for location in locations:
            data = location_dictionary[location]
            if data.carp and not self.options.carpsanity: continue
            if data.shura and self.options.goal_option == 0: continue
            if data.full_game and self.options.goal_option == 1: continue
            if isinstance(rule, str):
                assert item_dictionary[rule].classification & ItemClassification.progression
                rule = lambda state, item=rule: state.has(item, self.player)
            add_rule(self.multiworld.get_location(location, self.player), rule)

    def _add_entrance_rule(self, region: str, rule: CollectionRule | str) -> None:
        """Sets a rule for the entrance to the given region."""
        assert region in location_tables
        if region not in self.created_regions: return
        all_items = { **item_dictionary, **region_lock_dictionary, **skill_pickup_dictionary}
        if isinstance(rule, str):
            if " -> " not in rule:
                assert all_items[rule].classification == ItemClassification.progression
            rule = lambda state, item=rule: state.has(item, self.player)
        add_rule(self.multiworld.get_entrance("Go To " + region, self.player), rule)

    def _add_item_rule(self, location: str, rule: ItemRule) -> None:
        """Sets a rule for what items are allowed in a given location."""
        if not self._is_location_available(location): return
        add_item_rule(self.multiworld.get_location(location, self.player), rule)

    def _can_go_to(self, state, region) -> bool:
        """Returns whether state can access the given region name."""
        return state.can_reach_entrance(f"Go To {region}", self.player)

    def _can_get(self, state, location) -> bool:
        """Returns whether state can access the given location name."""
        return state.can_reach_location(location, self.player)

    def _is_location_available(
        self,
        location: str | SekiroLocationData | SekiroLocation
    ) -> bool:
        """Returns whether the given location is being randomized."""
        if isinstance(location, SekiroLocationData):
            data = location
        elif isinstance(location, SekiroLocation):
            data = location.data
        else:
            data = location_dictionary[location]
        return (
            not data.is_event
            and (not data.carp or bool(self.options.carpsanity))
            and (not data.shura or self.options.goal_option == 1)
            and (not data.full_game or self.options.goal_option == 0)
            and not (
                self.options.excluded_location_behavior == "do_not_randomize"
                and data.name in self.all_excluded_locations
            )
            and not (
                self.options.missable_location_behavior == "do_not_randomize"
                and data.is_missable(self.options)
            )
        )

    def write_spoiler(self, spoiler_handle: TextIO) -> None:
        text = ""

        if self.options.excluded_location_behavior != "forbid_useful":
            text += f"\n{self.player_name}'s world excluded: {sorted(self.all_excluded_locations)}\n"

        if text:
            text = "\n" + text + "\n"
            spoiler_handle.write(text)

    def _get_our_locations(self) -> list[SekiroLocation]:
        return cast(list[SekiroLocation], self.multiworld.get_locations(self.player))

    def fill_slot_data(self) -> dict[str, object]:

        # Once all clients support overlapping item IDs, adjust the Sekiro AP item IDs to encode the
        # in-game ID as well as the count so that we don't need to send this information at all.
        #
        # We include all the items the game knows about so that users can manually request items
        # that aren't randomized, and then we _also_ include all the items that are placed in practice
        items_by_name = {
            location.item.name: cast(SekiroItem, location.item).data
            for location in self.multiworld.get_filled_locations()
            # item.code None is used for events, which we want to skip
            if location.item.code is not None and location.item.player == self.player
        }
        for item in item_dictionary.values():
            if item.name not in items_by_name:
                items_by_name[item.name] = item

        ap_ids_to_sekiro_ids: dict[str, int] = {}
        item_counts: dict[str, int] = {}
        for item in items_by_name.values():
            if item.ap_code is None: continue
            if item.sekiro_code: ap_ids_to_sekiro_ids[str(item.ap_code)] = item.sekiro_code
            if item.count != 1: item_counts[str(item.ap_code)] = item.count

        # A map from Archipelago's location IDs to the keys the static randomizer uses to identify
        # locations.
        location_ids_to_keys: dict[int, str] = {}
        for location in cast(list[SekiroLocation], self.multiworld.get_filled_locations(self.player)):
            # Skip events and only look at this world's locations
            if (location.address is not None and location.item.code is not None
                    and location.data.static):
                location_ids_to_keys[location.address] = location.data.static

        slot_data = {
            "options": {
                "goal_option": self.options.goal_option.value,
                "additional_region_locks": self.options.additional_region_locks.value,
                "death_link": self.options.death_link.value,
                "remove_headless_slow_walk": self.options.remove_headless_slow_walk.value,
                "randomize_skills_and_prosthetics": self.options.randomize_skills_and_prosthetics.value,
                "replace_esoteric_texts_with_skills": self.options.replace_esoteric_texts_with_skills.value,
                "enemy_randomizer": self.options.enemy_randomizer.value,
                "randomize_bosses": self.options.randomize_bosses.value,
                "randomize_minibosses": self.options.randomize_minibosses.value,
                "randomize_headless": self.options.randomize_headless.value,
                "randomize_regular_enemies": self.options.randomize_regular_enemies.value,
                "similar_boss_phases": self.options.similar_boss_phases.value,
                "balanced_endgame_boss_phases": self.options.balanced_endgame_boss_phases.value,
                "simple_early_minibosses": self.options.simple_early_minibosses.value,
                "scale_enemies": self.options.scale_enemies.value,
                "carpsanity": self.options.carpsanity.value,
                # These would be needed to get UT yamlless, but do_not_randomize is still bad either way..
                #"exclude_locations": self.options.exclude_locations.value,
                #"excluded_location_behavior": self.options.excluded_location_behavior.value,
                #"missable_location_behavior": self.options.missable_location_behavior.value,
            },
            "seed": self.multiworld.seed_name,  # to verify the server's multiworld
            "slot": self.multiworld.player_name[self.player],  # to connect to server
            # Reserializing here is silly, but it's easier for the static randomizer.
            "random_enemy_preset": json.dumps(self.options.random_enemy_preset.value),
            "apIdsToItemIds": ap_ids_to_sekiro_ids,
            "itemCounts": item_counts,
            "locationIdsToKeys": location_ids_to_keys,
            # The range of versions of the static randomizer that are compatible
            # with this slot data. Incompatible versions should have at least a
            # minor version bump. Pre-release versions should generally only be
            # compatible with a single version, except very close to a stable
            # release when no changes are expected.
            #
            # This is checked by the static randomizer, which will surface an
            # error to the user if its version doesn't fall into the allowed
            # range.
            "versions": ">=1.0.1 <1.1.0",
        }

        return slot_data

    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        return slot_data
