from typing import cast, ClassVar, Optional, Dict, List, Set
from dataclasses import dataclass

from BaseClasses import ItemClassification, Location, Region
from .Items import SekiroItemCategory, item_dictionary

# Regions in approximate order of reward, mostly measured by how high-quality the upgrade items are
# in each region.
region_order = [
    "Cemetery of Ash",
    "Firelink Shrine",
    "High Wall of Lothric",
    "Greirat's Shop",
    "Undead Settlement",
    "Road of Sacrifices",
    "Farron Keep",
    "Cathedral of the Deep",
    "Catacombs of Carthus",
    "Smouldering Lake",
    "Irithyll of the Boreal Valley",
    "Irithyll Dungeon",
    "Karla's Shop",
    # The first half of Painted World has one Titanite Slab but mostly Large Titanite Shards,
    # much like Irithyll Dungeon.
    "Anor Londo",
    "Profaned Capital",
    # The second half of Painted World has two Titanite Chunks and two Titanite Slabs, which
    # puts it on the low end of the post-Lothric Castle areas in terms of rewards.
    "Lothric Castle",
    "Consumed King's Garden",
    "Untended Graves",
    # List this late because it contains a Titanite Slab in the base game
    "Firelink Shrine Bell Tower",
    "Grand Archives",
    "Archdragon Peak",
    "Kiln of the First Flame",
]


@dataclass
class SekiroLocationData:
    __location_id: ClassVar[int] = 100000
    """The next location ID to use when creating location data."""

    name: str
    """The name of this location according to Archipelago.

    This needs to be unique within this world."""

    default_item_name: Optional[str]
    """The name of the item that appears by default in this location.

    If this is None, that indicates that this location is an "event" that's
    automatically considered accessed as soon as it's available. Events are used
    to indicate major game transitions that aren't otherwise gated by items so
    that progression balancing and item smoothing is more accurate for DS3.
    """

    ap_code: Optional[int] = None
    """Archipelago's internal ID for this location (also known as its "address")."""

    region_value: int = 0
    """The relative value of items in this location's region.

    This is used to sort locations when placing items like the base game.
    """

    static: Optional[str] = None
    """The key in the static randomizer's Slots table that corresponds to this location.

    By default, the static randomizer chooses its location based on the region and the item name.
    If the item name is unique across the whole game, it can also look it up based on that alone. If
    there are multiple instances of the same item type in the same region, it will assume its order
    (in annotations.txt) matches Archipelago's order.

    In cases where this heuristic doesn't work, such as when Archipelago's region categorization or
    item name disagrees with the static randomizer's, this field is used to provide an explicit
    association instead.
    """

    missable: bool = False
    """Whether this item is possible to permanently lose access to.

    This is also used for items that are *technically* possible to get at any time, but are
    prohibitively difficult without blocking off other checks (items dropped by NPCs on death
    generally fall into this category).

    Missable locations are always marked as excluded, so they will never contain
    progression or useful items.
    """

    npc: bool = False
    """Whether this item is contingent on killing an NPC or following their quest."""

    prominent: bool = False
    """Whether this is one of few particularly prominent places for items to appear.

    This is a small number of locations (boss drops and progression locations)
    intended to be set as priority locations for players who don't want a lot of
    mandatory checks.

    For bosses with multiple drops, only one should be marked prominent.
    """

    progression: bool = False
    """Whether this location normally contains an item that blocks forward progress."""

    boss: bool = False
    """Whether this location is a reward for defeating a full boss."""

    miniboss: bool = False
    """Whether this location is a reward for defeating a miniboss.

    The classification of "miniboss" is a bit fuzzy, but we consider them to be enemies that are
    visually distinctive in their locations, usually bigger than normal enemies, with a guaranteed
    item drop. NPCs are never considered minibosses, and some normal-looking enemies with guaranteed
    drops aren't either (these are instead classified as hidden locations)."""

    drop: bool = False
    """Whether this is an item dropped by a (non-boss) enemy.

    This is automatically set to True if miniboss, mimic, lizard, or hostile_npc is True.
    """

    mimic: bool = False
    """Whether this location is dropped by a mimic."""

    hostile_npc: bool = False
    """Whether this location is dropped by a hostile NPC.

    An "NPC" is specifically a human (or rather, ash) is built like a player character rather than a
    monster. This includes both scripted invaders and NPCs who are always on the overworld. It does
    not include initially-friendly NPCs who become hostile as part of a quest or because you attack
    them.
    """

    lizard: bool = False
    """Whether this location is dropped by a (small) Crystal Lizard."""

    shop: bool = False
    """Whether this location can appear in an NPC's shop.

    Items like Lapp's Set which can appear both in the overworld and in a shop
    should still be tagged as shop.
    """

    conditional: bool = False
    """Whether this location is conditional on a progression item.

    This is used to track locations that won't become available until an unknown amount of time into
    the run, and as such shouldn't have "similar to the base game" items placed in them.
    """

    hidden: bool = False
    """Whether this location is particularly tricky to find.

    This is for players without an encyclopedic knowledge of DS3 who don't want to get stuck looking
    for an illusory wall or one random mob with a guaranteed drop.
    """

    @property
    def is_event(self) -> bool:
        """Whether this location represents an event rather than a specific item pickup."""
        return self.default_item_name is None

    def __post_init__(self):
        if not self.is_event:
            self.ap_code = self.ap_code or SekiroLocationData.__location_id
            SekiroLocationData.__location_id += 1
        if self.miniboss or self.mimic or self.lizard or self.hostile_npc: self.drop = True

    def location_groups(self) -> List[str]:
        """The names of location groups this location should appear in.

        This is computed from the properties assigned to this location."""
        names = []
        if self.prominent: names.append("Prominent")
        if self.progression: names.append("Progression")
        if self.boss: names.append("Boss Rewards")
        if self.miniboss: names.append("Miniboss Rewards")
        if self.mimic: names.append("Mimic Rewards")
        if self.hostile_npc: names.append("Hostile NPC Rewards")
        if self.npc: names.append("Friendly NPC Rewards")
        if self.lizard: names.append("Small Crystal Lizards")
        if self.hidden: names.append("Hidden")

        default_item = item_dictionary[cast(str, self.default_item_name)]
        names.append({
                         SekiroItemCategory.WEAPON_UPGRADE_5: "Weapons",
                         SekiroItemCategory.WEAPON_UPGRADE_10: "Weapons",
                         SekiroItemCategory.WEAPON_UPGRADE_10_INFUSIBLE: "Weapons",
                         SekiroItemCategory.SHIELD: "Shields",
                         SekiroItemCategory.SHIELD_INFUSIBLE: "Shields",
                         SekiroItemCategory.ARMOR: "Armor",
                         SekiroItemCategory.RING: "Rings",
                         SekiroItemCategory.SPELL: "Spells",
                         SekiroItemCategory.MISC: "Miscellaneous",
                         SekiroItemCategory.UNIQUE: "Unique",
                         SekiroItemCategory.BOSS: "Boss Souls",
                         SekiroItemCategory.SOUL: "Small Souls",
                         SekiroItemCategory.UPGRADE: "Upgrade",
                         SekiroItemCategory.HEALING: "Healing",
                     }[default_item.category])
        if default_item.classification == ItemClassification.progression:
            names.append("Progression")

        return names


class SekiroLocation(Location):
    game: str = "Sekiro"
    data: SekiroLocationData

    def __init__(
            self,
            player: int,
            data: SekiroLocationData,
            parent: Optional[Region] = None,
            event: bool = False):
        super().__init__(player, data.name, None if event else data.ap_code, parent)
        self.data = data


# Naming conventions:
#
# * The regions in item names should match the physical region where the item is
#   acquired, even if its logical region is different. For example, Irina's
#   inventory appears in the "Undead Settlement" region because she's not
#   accessible until there, but it begins with "FS:" because that's where her
#   items are purchased.
#
# * Avoid using vanilla enemy placements as landmarks, because these are
#   randomized by the enemizer by default. Instead, use generic terms like
#   "mob", "boss", and "miniboss".
#
# * Location descriptions don't need to direct the player to the precise spot.
#   You can assume the player is broadly familiar with Dark Souls III or willing
#   to look at a vanilla guide. Just give a general area to look in or an idea
#   of what quest a check is connected to. Terseness is valuable: try to keep
#   each location description short enough that the whole line doesn't exceed
#   100 characters.
#
# * Use "[name] drop" for items that require killing an NPC who becomes hostile
#   as part of their normal quest, "kill [name]" for items that require killing
#   them even when they aren't hostile, and just "[name]" for items that are
#   naturally available as part of their quest.
location_tables: Dict[str, List[SekiroLocationData]] = {
    "Cemetery of Ash": [
        SekiroLocationData("CA: Soul of a Deserted Corpse - right of spawn",
                        "Soul of a Deserted Corpse"),
        SekiroLocationData("CA: Firebomb - down the cliff edge", "Firebomb x5"),
        SekiroLocationData("CA: Titanite Shard - jump to coffin", "Titanite Shard"),
        SekiroLocationData("CA: Soul of an Unknown Traveler - by miniboss",
                        "Soul of an Unknown Traveler"),
        SekiroLocationData("CA: Speckled Stoneplate Ring+1 - by miniboss",
                        "Speckled Stoneplate Ring+1"),
        SekiroLocationData("CA: Titanite Scale - miniboss drop", "Titanite Scale", miniboss=True),
        SekiroLocationData("CA: Coiled Sword - boss drop", "Coiled Sword", prominent=True,
                           progression=True, boss=True),
    ],
    "Firelink Shrine": [
        # Ludleth drop, does not permanently die
        SekiroLocationData("FS: Skull Ring - kill Ludleth", "Skull Ring", hidden=True, drop=True,
                           npc=True),

        # Sword Master drops
        SekiroLocationData("FS: Uchigatana - NPC drop", "Uchigatana", hostile_npc=True),
        SekiroLocationData("FS: Master's Attire - NPC drop", "Master's Attire", hostile_npc=True),
        SekiroLocationData("FS: Master's Gloves - NPC drop", "Master's Gloves", hostile_npc=True),

        SekiroLocationData("FS: Broken Straight Sword - gravestone after boss",
                        "Broken Straight Sword"),
        SekiroLocationData("FS: Homeward Bone - cliff edge after boss", "Homeward Bone"),
        SekiroLocationData("FS: Ember - path right of Firelink entrance", "Ember"),
        SekiroLocationData("FS: Soul of a Deserted Corpse - bell tower door",
                        "Soul of a Deserted Corpse"),
        SekiroLocationData("FS: East-West Shield - tree by shrine entrance", "East-West Shield"),
        SekiroLocationData("FS: Homeward Bone - path above shrine entrance", "Homeward Bone"),
        SekiroLocationData("FS: Ember - above shrine entrance", "Ember"),
        SekiroLocationData("FS: Wolf Ring+2 - left of boss room exit", "Wolf Ring+2", ),
        # Leonhard (quest)
        SekiroLocationData("FS: Cracked Red Eye Orb - Leonhard", "Cracked Red Eye Orb x5",
                           missable=True, npc=True),
        # Leonhard (kill or quest), missable because he can disappear sometimes
        SekiroLocationData("FS: Lift Chamber Key - Leonhard", "Lift Chamber Key", missable=True,
                           npc=True, drop=True),

        # Shrine Handmaid shop
        SekiroLocationData("FS: White Sign Soapstone - shop", "White Sign Soapstone", shop=True),
        SekiroLocationData("FS: Dried Finger - shop", "Dried Finger", shop=True),
        SekiroLocationData("FS: Tower Key - shop", "Tower Key", progression=True, shop=True),
        SekiroLocationData("FS: Ember - shop", "Ember", static='99,0:-1:110000:', shop=True),
        SekiroLocationData("FS: Farron Dart - shop", "Farron Dart", static='99,0:-1:110000:',
                           shop=True),
        SekiroLocationData("FS: Soul Arrow - shop", "Soul Arrow", static='99,0:-1:110000:',
                           shop=True),
        SekiroLocationData("FS: Heal Aid - shop", "Heal Aid", shop=True),
        SekiroLocationData("FS: Alluring Skull - Mortician's Ashes", "Alluring Skull", shop=True,
                           conditional=True),
        SekiroLocationData("FS: Ember - Mortician's Ashes", "Ember",
                           static='99,0:-1:110000,70000100:', shop=True, conditional=True),
        SekiroLocationData("FS: Grave Key - Mortician's Ashes", "Grave Key", shop=True,
                           conditional=True),
        SekiroLocationData("FS: Life Ring - Dreamchaser's Ashes", "Life Ring", shop=True,
                           conditional=True),
        # Only if you say where the ashes were found
        SekiroLocationData("FS: Hidden Blessing - Dreamchaser's Ashes", "Hidden Blessing",
                           missable=True, shop=True),
        SekiroLocationData("FS: Lloyd's Shield Ring - Paladin's Ashes", "Lloyd's Shield Ring",
                           shop=True, conditional=True),
        SekiroLocationData("FS: Ember - Grave Warden's Ashes", "Ember",
                           static='99,0:-1:110000,70000103:', shop=True, conditional=True),
        # Prisoner Chief's Ashes
        SekiroLocationData("FS: Karla's Pointed Hat - Prisoner Chief's Ashes", "Karla's Pointed Hat",
                           static='99,0:-1:110000,70000105:', shop=True, conditional=True),
        SekiroLocationData("FS: Karla's Coat - Prisoner Chief's Ashes", "Karla's Coat",
                           static='99,0:-1:110000,70000105:', shop=True, conditional=True),
        SekiroLocationData("FS: Karla's Gloves - Prisoner Chief's Ashes", "Karla's Gloves",
                           static='99,0:-1:110000,70000105:', shop=True, conditional=True),
        SekiroLocationData("FS: Karla's Trousers - Prisoner Chief's Ashes", "Karla's Trousers",
                           static='99,0:-1:110000,70000105:', shop=True, conditional=True),
        SekiroLocationData("FS: Xanthous Overcoat - Xanthous Ashes", "Xanthous Overcoat", shop=True,
                           conditional=True),
        SekiroLocationData("FS: Xanthous Gloves - Xanthous Ashes", "Xanthous Gloves", shop=True,
                           conditional=True),
        SekiroLocationData("FS: Xanthous Trousers - Xanthous Ashes", "Xanthous Trousers", shop=True,
                           conditional=True),
        SekiroLocationData("FS: Ember - Dragon Chaser's Ashes", "Ember",
                           static='99,0:-1:110000,70000108:', shop=True, conditional=True),
        SekiroLocationData("FS: Washing Pole - Easterner's Ashes", "Washing Pole", shop=True,
                           conditional=True),
        SekiroLocationData("FS: Eastern Helm - Easterner's Ashes", "Eastern Helm", shop=True,
                           conditional=True),
        SekiroLocationData("FS: Eastern Armor - Easterner's Ashes", "Eastern Armor", shop=True,
                           conditional=True),
        SekiroLocationData("FS: Eastern Gauntlets - Easterner's Ashes", "Eastern Gauntlets",
                           shop=True, conditional=True),
        SekiroLocationData("FS: Eastern Leggings - Easterner's Ashes", "Eastern Leggings", shop=True,
                           conditional=True),
        SekiroLocationData("FS: Wood Grain Ring - Easterner's Ashes", "Wood Grain Ring", shop=True,
                           conditional=True),
        SekiroLocationData("FS: Millwood Knight Helm - Captain's Ashes", "Millwood Knight Helm",
                           shop=True, conditional=True),
        SekiroLocationData("FS: Millwood Knight Armor - Captain's Ashes", "Millwood Knight Armor",
                           shop=True, conditional=True),
        SekiroLocationData("FS: Millwood Knight Gauntlets - Captain's Ashes",
                        "Millwood Knight Gauntlets", shop=True, conditional=True),
        SekiroLocationData("FS: Millwood Knight Leggings - Captain's Ashes",
                        "Millwood Knight Leggings", shop=True, conditional=True),
        SekiroLocationData("FS: Refined Gem - Captain's Ashes", "Refined Gem", shop=True,
                           conditional=True),

        # Ludleth Shop
        SekiroLocationData("FS: Vordt's Great Hammer - Ludleth for Vordt", "Vordt's Great Hammer",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Pontiff's Left Eye - Ludleth for Vordt", "Pontiff's Left Eye",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Bountiful Sunlight - Ludleth for Rosaria", "Bountiful Sunlight",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Darkmoon Longbow - Ludleth for Aldrich", "Darkmoon Longbow",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Lifehunt Scythe - Ludleth for Aldrich", "Lifehunt Scythe",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Hollowslayer Greatsword - Ludleth for Greatwood",
                        "Hollowslayer Greatsword", missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Arstor's Spear - Ludleth for Greatwood", "Arstor's Spear",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Crystal Sage's Rapier - Ludleth for Sage", "Crystal Sage's Rapier",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Crystal Hail - Ludleth for Sage", "Crystal Hail", missable=True,
                           boss=True, shop=True),
        SekiroLocationData("FS: Cleric's Candlestick - Ludleth for Deacons", "Cleric's Candlestick",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Deep Soul - Ludleth for Deacons", "Deep Soul", missable=True,
                           boss=True, shop=True),
        SekiroLocationData("FS: Havel's Ring - Ludleth for Stray Demon", "Havel's Ring",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Boulder Heave - Ludleth for Stray Demon", "Boulder Heave",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Farron Greatsword - Ludleth for Abyss Watchers", "Farron Greatsword",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Wolf Knight's Greatsword - Ludleth for Abyss Watchers",
                        "Wolf Knight's Greatsword", missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Wolnir's Holy Sword - Ludleth for Wolnir", "Wolnir's Holy Sword",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Black Serpent - Ludleth for Wolnir", "Black Serpent", missable=True,
                           boss=True, shop=True),
        SekiroLocationData("FS: Demon's Greataxe - Ludleth for Fire Demon", "Demon's Greataxe",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Demon's Fist - Ludleth for Fire Demon", "Demon's Fist",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Old King's Great Hammer - Ludleth for Old Demon King",
                        "Old King's Great Hammer", missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Chaos Bed Vestiges - Ludleth for Old Demon King", "Chaos Bed Vestiges",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Greatsword of Judgment - Ludleth for Pontiff",
                        "Greatsword of Judgment", missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Profaned Greatsword - Ludleth for Pontiff", "Profaned Greatsword",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Yhorm's Great Machete - Ludleth for Yhorm", "Yhorm's Great Machete",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Yhorm's Greatshield - Ludleth for Yhorm", "Yhorm's Greatshield",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Dancer's Enchanted Swords - Ludleth for Dancer",
                        "Dancer's Enchanted Swords", missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Soothing Sunlight - Ludleth for Dancer", "Soothing Sunlight",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Dragonslayer Greataxe - Ludleth for Dragonslayer",
                        "Dragonslayer Greataxe", missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Dragonslayer Greatshield - Ludleth for Dragonslayer",
                        "Dragonslayer Greatshield", missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Moonlight Greatsword - Ludleth for Oceiros", "Moonlight Greatsword",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: White Dragon Breath - Ludleth for Oceiros", "White Dragon Breath",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Lorian's Greatsword - Ludleth for Princes", "Lorian's Greatsword",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Lothric's Holy Sword - Ludleth for Princes", "Lothric's Holy Sword",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Gundyr's Halberd - Ludleth for Champion", "Gundyr's Halberd",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Prisoner's Chain - Ludleth for Champion", "Prisoner's Chain",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Storm Curved Sword - Ludleth for Nameless", "Storm Curved Sword",
                           missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Dragonslayer Swordspear - Ludleth for Nameless",
                        "Dragonslayer Swordspear", missable=True, boss=True, shop=True),
        SekiroLocationData("FS: Lightning Storm - Ludleth for Nameless", "Lightning Storm",
                           missable=True, boss=True, shop=True),
    ],
    "Firelink Shrine Bell Tower": [
        # Guarded by Tower Key
        SekiroLocationData("FSBT: Homeward Bone - roof", "Homeward Bone x3"),
        SekiroLocationData("FSBT: Estus Ring - tower base", "Estus Ring"),
        SekiroLocationData("FSBT: Estus Shard - rafters", "Estus Shard"),
        SekiroLocationData("FSBT: Fire Keeper Soul - tower top", "Fire Keeper Soul"),
        SekiroLocationData("FSBT: Fire Keeper Robe - partway down tower", "Fire Keeper Robe"),
        SekiroLocationData("FSBT: Fire Keeper Gloves - partway down tower", "Fire Keeper Gloves"),
        SekiroLocationData("FSBT: Fire Keeper Skirt - partway down tower", "Fire Keeper Skirt"),
        SekiroLocationData("FSBT: Covetous Silver Serpent Ring - illusory wall past rafters",
                        "Covetous Silver Serpent Ring", hidden=True),
        SekiroLocationData("FSBT: Twinkling Titanite - lizard behind Firelink",
                        "Twinkling Titanite", lizard=True),

        # Mark all crow trades as missable since no one wants to have to try trading everything just
        # in case it gives a progression item.
        SekiroLocationData("FSBT: Iron Bracelets - crow for Homeward Bone", "Iron Bracelets",
                           missable=True),
        SekiroLocationData("FSBT: Ring of Sacrifice - crow for Loretta's Bone", "Ring of Sacrifice",
                           missable=True),
        SekiroLocationData("FSBT: Porcine Shield - crow for Undead Bone Shard", "Porcine Shield",
                           missable=True),
        SekiroLocationData("FSBT: Lucatiel's Mask - crow for Vertebra Shackle", "Lucatiel's Mask",
                           missable=True),
        SekiroLocationData("FSBT: Very good! Carving - crow for Divine Blessing",
                        "Very good! Carving", missable=True),
        SekiroLocationData("FSBT: Thank you Carving - crow for Hidden Blessing", "Thank you Carving",
                           missable=True),
        SekiroLocationData("FSBT: I'm sorry Carving - crow for Shriving Stone", "I'm sorry Carving",
                           missable=True),
        SekiroLocationData("FSBT: Sunlight Shield - crow for Mendicant's Staff", "Sunlight Shield",
                           missable=True),
        SekiroLocationData("FSBT: Hollow Gem - crow for Eleonora", "Hollow Gem",
                           missable=True),
        SekiroLocationData("FSBT: Titanite Scale - crow for Blacksmith Hammer", "Titanite Scale x3",
                           static='99,0:50004330::', missable=True),
        SekiroLocationData("FSBT: Help me! Carving - crow for any sacred chime", "Help me! Carving",
                           missable=True),
        SekiroLocationData("FSBT: Titanite Slab - crow for Coiled Sword Fragment", "Titanite Slab",
                           missable=True),
        SekiroLocationData("FSBT: Hello Carving - crow for Alluring Skull", "Hello Carving",
                           missable=True),
        SekiroLocationData("FSBT: Armor of the Sun - crow for Siegbräu", "Armor of the Sun",
                           missable=True),
        SekiroLocationData("FSBT: Large Titanite Shard - crow for Firebomb", "Large Titanite Shard",
                           missable=True),
        SekiroLocationData("FSBT: Titanite Chunk - crow for Black Firebomb", "Titanite Chunk",
                           missable=True),
        SekiroLocationData("FSBT: Iron Helm - crow for Lightning Urn", "Iron Helm", missable=True),
        SekiroLocationData("FSBT: Twinkling Titanite - crow for Prism Stone", "Twinkling Titanite",
                           missable=True),
        SekiroLocationData("FSBT: Iron Leggings - crow for Seed of a Giant Tree", "Iron Leggings",
                           missable=True),
        SekiroLocationData("FSBT: Lightning Gem - crow for Xanthous Crown", "Lightning Gem",
                           missable=True),
        SekiroLocationData("FSBT: Twinkling Titanite - crow for Large Leather Shield",
                        "Twinkling Titanite", missable=True),
        SekiroLocationData("FSBT: Blessed Gem - crow for Moaning Shield", "Blessed Gem",
                           missable=True),
    ],
    "High Wall of Lothric": [
        SekiroLocationData("HWL: Soul of Boreal Valley Vordt", "Soul of Boreal Valley Vordt",
                           prominent=True, boss=True),
        SekiroLocationData("HWL: Soul of the Dancer", "Soul of the Dancer", prominent=True,
                           boss=True),
        SekiroLocationData("HWL: Basin of Vows - Emma", "Basin of Vows", prominent=True,
                           progression=True, conditional=True),
        SekiroLocationData("HWL: Small Lothric Banner - Emma", "Small Lothric Banner",
                           prominent=True, progression=True),
        SekiroLocationData("HWL: Green Blossom - fort walkway, hall behind wheel", "Green Blossom x2",
                           hidden=True),
        SekiroLocationData("HWL: Gold Pine Resin - corpse tower, drop", "Gold Pine Resin x2",
                           hidden=True),
        SekiroLocationData("HWL: Large Soul of a Deserted Corpse - flame plaza",
                        "Large Soul of a Deserted Corpse"),
        SekiroLocationData("HWL: Soul of a Deserted Corpse - by wall tower door",
                        "Soul of a Deserted Corpse"),
        SekiroLocationData("HWL: Standard Arrow - back tower", "Standard Arrow x12"),
        SekiroLocationData("HWL: Longbow - back tower", "Longbow"),
        SekiroLocationData("HWL: Firebomb - wall tower, beam", "Firebomb x3"),
        SekiroLocationData("HWL: Throwing Knife - wall tower, path to Greirat", "Throwing Knife x8"),
        SekiroLocationData("HWL: Soul of a Deserted Corpse - corpse tower, bottom floor",
                        "Soul of a Deserted Corpse"),
        SekiroLocationData("HWL: Club - flame plaza", "Club"),
        SekiroLocationData("HWL: Claymore - flame plaza", "Claymore"),
        SekiroLocationData("HWL: Ember - flame plaza", "Ember"),
        SekiroLocationData("HWL: Firebomb - corpse tower, under table", "Firebomb x2"),
        SekiroLocationData("HWL: Titanite Shard - wall tower, corner by bonfire", "Titanite Shard",
                           hidden=True),
        SekiroLocationData("HWL: Undead Hunter Charm - fort, room off entry, in pot",
                        "Undead Hunter Charm x2", hidden=True),
        SekiroLocationData("HWL: Firebomb - top of ladder to fountain", "Firebomb x3"),
        SekiroLocationData("HWL: Cell Key - fort ground, down stairs", "Cell Key"),
        SekiroLocationData("HWL: Ember - fountain #1", "Ember"),
        SekiroLocationData("HWL: Soul of a Deserted Corpse - fort entry, corner",
                        "Soul of a Deserted Corpse"),
        SekiroLocationData("HWL: Lucerne - promenade, side path", "Lucerne"),
        SekiroLocationData("HWL: Mail Breaker - wall tower, path to Greirat", "Mail Breaker"),
        SekiroLocationData("HWL: Titanite Shard - fort ground behind crates", "Titanite Shard",
                           hidden=True),
        SekiroLocationData("HWL: Rapier - fountain, corner", "Rapier"),
        SekiroLocationData("HWL: Titanite Shard - fort, room off entry", "Titanite Shard"),
        SekiroLocationData("HWL: Large Soul of a Deserted Corpse - fort roof",
                        "Large Soul of a Deserted Corpse"),
        SekiroLocationData("HWL: Black Firebomb - small roof over fountain", "Black Firebomb x3"),
        SekiroLocationData("HWL: Soul of a Deserted Corpse - path to corpse tower",
                        "Soul of a Deserted Corpse"),
        SekiroLocationData("HWL: Ember - fountain #2", "Ember"),
        SekiroLocationData("HWL: Large Soul of a Deserted Corpse - platform by fountain",
                        "Large Soul of a Deserted Corpse", hidden=True),  # Easily missed turnoff
        SekiroLocationData("HWL: Binoculars - corpse tower, upper platform", "Binoculars"),
        SekiroLocationData("HWL: Ring of Sacrifice - awning by fountain",
                        "Ring of Sacrifice", hidden=True),  # Easily missed turnoff
        SekiroLocationData("HWL: Throwing Knife - shortcut, lift top", "Throwing Knife x6"),
        SekiroLocationData("HWL: Soul of a Deserted Corpse - path to back tower, by lift door",
                        "Soul of a Deserted Corpse"),
        SekiroLocationData("HWL: Green Blossom - shortcut, lower courtyard", "Green Blossom x3"),
        SekiroLocationData("HWL: Broadsword - fort, room off walkway", "Broadsword"),
        SekiroLocationData("HWL: Soul of a Deserted Corpse - fountain, path to promenade",
                        "Soul of a Deserted Corpse"),
        SekiroLocationData("HWL: Firebomb - fort roof", "Firebomb x3"),
        SekiroLocationData("HWL: Soul of a Deserted Corpse - wall tower, right of exit",
                        "Soul of a Deserted Corpse"),
        SekiroLocationData("HWL: Estus Shard - fort ground, on anvil", "Estus Shard"),
        SekiroLocationData("HWL: Fleshbite Ring+1 - fort roof, jump to other roof",
                        "Fleshbite Ring+1", hidden=True),  # Hidden jump
        SekiroLocationData("HWL: Ring of the Evil Eye+2 - fort ground, far wall",
                        "Ring of the Evil Eye+2", hidden=True),  # In barrels
        SekiroLocationData("HWL: Silver Eagle Kite Shield - fort mezzanine",
                        "Silver Eagle Kite Shield"),
        SekiroLocationData("HWL: Astora Straight Sword - fort walkway, drop down",
                        "Astora Straight Sword", hidden=True),  # Hidden fall
        SekiroLocationData("HWL: Battle Axe - flame tower, mimic", "Battle Axe",
                           static='01,0:53000960::', mimic=True),

        # Only dropped after transformation
        SekiroLocationData("HWL: Ember - fort roof, transforming hollow", "Ember", hidden=True),
        SekiroLocationData("HWL: Titanite Shard - fort roof, transforming hollow", "Titanite Shard",
                           hidden=True),
        SekiroLocationData("HWL: Ember - back tower, transforming hollow", "Ember", hidden=True),
        SekiroLocationData("HWL: Titanite Shard - back tower, transforming hollow", "Titanite Shard",
                           hidden=True),

        SekiroLocationData("HWL: Refined Gem - promenade miniboss", "Refined Gem", miniboss=True),
        SekiroLocationData("HWL: Way of Blue - Emma", "Way of Blue"),
        # Categorize this as an NPC item so that it doesn't get randomized if the Lift Chamber Key
        # isn't randomized, since in that case it's missable.
        SekiroLocationData("HWL: Red Eye Orb - wall tower, miniboss", "Red Eye Orb",
                           conditional=True, miniboss=True, npc=True),
        SekiroLocationData("HWL: Raw Gem - fort roof, lizard", "Raw Gem", lizard=True),
    ],
    "Karla's Shop": [
        SekiroLocationData("FS: Affinity - Karla", "Affinity", shop=True, npc=True),
        SekiroLocationData("FS: Dark Edge - Karla", "Dark Edge", shop=True, npc=True),

        # Quelana Pyromancy Tome
        SekiroLocationData("FS: Firestorm - Karla for Quelana Tome", "Firestorm", missable=True,
                           shop=True, npc=True),
        SekiroLocationData("FS: Rapport - Karla for Quelana Tome", "Rapport", missable=True,
                           shop=True, npc=True),
        SekiroLocationData("FS: Fire Whip - Karla for Quelana Tome", "Fire Whip", missable=True,
                           shop=True, npc=True),

        # Grave Warden Pyromancy Tome
        SekiroLocationData("FS: Black Flame - Karla for Grave Warden Tome", "Black Flame",
                           missable=True, shop=True, npc=True),
        SekiroLocationData("FS: Black Fire Orb - Karla for Grave Warden Tome", "Black Fire Orb",
                           missable=True, shop=True, npc=True),

        # Deep Braille Divine Tome. This can also be given to Irina, but it'll fail her quest
        SekiroLocationData("FS: Gnaw - Karla for Deep Braille Tome", "Gnaw", missable=True,
                           npc=True, shop=True),
        SekiroLocationData("FS: Deep Protection - Karla for Deep Braille Tome", "Deep Protection",
                           missable=True, npc=True, shop=True),

        # Londor Braille Divine Tome. This can also be given to Irina, but it'll fail her quest
        SekiroLocationData("FS: Vow of Silence - Karla for Londor Tome", "Vow of Silence",
                           missable=True, npc=True, shop=True),
        SekiroLocationData("FS: Dark Blade - Karla for Londor Tome", "Dark Blade", missable=True,
                           npc=True, shop=True),
        SekiroLocationData("FS: Dead Again - Karla for Londor Tome", "Dead Again", missable=True,
                           npc=True, shop=True),

        # Drops on death. Missable because the player would have to decide between killing her or
        # seeing everything she sells.
        SekiroLocationData("FS: Karla's Pointed Hat - kill Karla", "Karla's Pointed Hat",
                           static='07,0:50006150::', missable=True, drop=True, npc=True),
        SekiroLocationData("FS: Karla's Coat - kill Karla", "Karla's Coat",
                           static='07,0:50006150::', missable=True, drop=True, npc=True),
        SekiroLocationData("FS: Karla's Gloves - kill Karla", "Karla's Gloves",
                           static='07,0:50006150::', missable=True, drop=True, npc=True),
        SekiroLocationData("FS: Karla's Trousers - kill Karla", "Karla's Trousers",
                           static='07,0:50006150::', missable=True, drop=True, npc=True),
    ],
}

for i, region in enumerate(region_order):
    for location in location_tables[region]: location.region_value = i

for region in [
    "Firelink Shrine Bell Tower",
    "Greirat's Shop",
    "Karla's Shop"
]:
    for location in location_tables[region]:
        location.conditional = True

location_name_groups: Dict[str, Set[str]] = {
    # We could insert these locations automatically with setdefault(), but we set them up explicitly
    # instead so we can choose the ordering.
    "Prominent": set(),
    "Progression": set(),
    "Boss Rewards": set(),
    "Miniboss Rewards": set(),
    "Mimic Rewards": set(),
    "Hostile NPC Rewards": set(),
    "Friendly NPC Rewards": set(),
    "Small Crystal Lizards": set(),
    "Upgrade": set(),
    "Small Souls": set(),
    "Boss Souls": set(),
    "Unique": set(),
    "Healing": set(),
    "Miscellaneous": set(),
    "Hidden": set(),
    "Weapons": set(),
    "Shields": set(),
    "Armor": set(),
    "Rings": set(),
    "Spells": set(),
}

location_descriptions = {
    "Prominent": "A small number of locations that are in very obvious locations. Mostly boss " + \
                 "drops. Ideal for setting as priority locations.",
    "Progression": "Locations that contain items in vanilla which unlock other locations.",
    "Boss Rewards": "Boss drops. Does not include soul transfusions or shop items.",
    "Miniboss Rewards": "Miniboss drops. Only includes enemies considered minibosses by the " + \
                        "enemy randomizer.",
    "Mimic Rewards": "Drops from enemies that are mimics in vanilla.",
    "Hostile NPC Rewards": "Drops from NPCs that are hostile to you. This includes scripted " + \
                           "invaders and initially-friendly NPCs that must be fought as part of their quest.",
    "Friendly NPC Rewards": "Items given by friendly NPCs as part of their quests or from " + \
                            "non-violent interaction.",
    "Upgrade": "Locations that contain upgrade items in vanilla, including titanite, gems, and " + \
               "Shriving Stones.",
    "Small Souls": "Locations that contain soul items in vanilla, not including boss souls.",
    "Boss Souls": "Locations that contain boss souls in vanilla, as well as Soul of Rosaria.",
    "Unique": "Locations that contain items in vanilla that are unique per NG cycle, such as " + \
              "scrolls, keys, ashes, and so on. Doesn't cover equipment, spells, or souls.",
    "Healing": "Locations that contain Undead Bone Shards and Estus Shards in vanilla.",
    "Miscellaneous": "Locations that contain generic stackable items in vanilla, such as arrows, " +
                     "firebombs, buffs, and so on.",
    "Hidden": "Locations that are particularly difficult to find, such as behind illusory " + \
              "walls, down hidden drops, and so on. Does not include large locations like Untended " + \
              "Graves or Archdragon Peak.",
    "Weapons": "Locations that contain weapons in vanilla.",
    "Shields": "Locations that contain shields in vanilla.",
    "Armor": "Locations that contain armor in vanilla.",
    "Rings": "Locations that contain rings in vanilla.",
    "Spells": "Locations that contain spells in vanilla.",
}

location_dictionary: Dict[str, SekiroLocationData] = {}
for location_name, location_table in location_tables.items():
    location_dictionary.update({location_data.name: location_data for location_data in location_table})

    for location_data in location_table:
        if not location_data.is_event:
            for group_name in location_data.location_groups():
                location_name_groups[group_name].add(location_data.name)

    # Allow entire locations to be added to location sets.
    if not location_name.endswith(" Shop"):
        location_name_groups[location_name] = set([
            location_data.name for location_data in location_table
            if not location_data.is_event
        ])
