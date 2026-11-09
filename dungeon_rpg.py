
"""
Two-Player Dungeon RPG

Run the game:
    python dungeon_rpg.py

Choose a difficulty:
    python dungeon_rpg.py --difficulty easy
    python dungeon_rpg.py --difficulty normal
    python dungeon_rpg.py --difficulty hard

Choose a save file:
    python dungeon_rpg.py --save campaign.json

Load a saved game:
    python dungeon_rpg.py --load --save campaign.json
"""

import argparse
import json
import random


# ==========================================
# 1. GAME INFORMATION
# ==========================================

CLASS_INFO = {
    "Moth Keeper": {
        "health": 25,
        "damage": 3,
        "mana": 35,
        "description": "A fragile character with high mana.",
        "ability": "Decaying Swarm"
    },
    "Bell Ringer": {
        "health": 30,
        "damage": 5,
        "mana": 30,
        "description": "A balanced character who can stun enemies.",
        "ability": "Discordant Toll"
    },
    "Chef": {
        "health": 40,
        "damage": 4,
        "mana": 25,
        "description": "A tough character with unpredictable abilities.",
        "ability": "Culinary Creation"
    },
    "Fisherman": {
        "health": 35,
        "damage": 7,
        "mana": 20,
        "description": "A hard-hitting character with lower mana.",
        "ability": "Bass Bludgeoning"
    },
    "Librarian": {
        "health": 25,
        "damage": 2,
        "mana": 40,
        "description": "A fragile character who can borrow other abilities.",
        "ability": "Forbidden Knowledge"
    }
}


ENEMY_TYPES = [
    {"name": "Crawler", "health": 12, "damage": 3, "type": "Beast"},
    {"name": "Stalker", "health": 20, "damage": 5, "type": "Creature"},
    {"name": "Goblin", "health": 25, "damage": 4, "type": "Humanoid"},
    {"name": "Suspicious Guy", "health": 30, "damage": 7, "type": "Undead"},
    {"name": "Soul Serpent", "health": 38, "damage": 8, "type": "Undead"},
    {"name": "Iron Revenant", "health": 35, "damage": 9, "type": "Spirit"}
]


DIFFICULTY_MULTIPLIERS = {
    "easy": 0.75,
    "normal": 1.0,
    "hard": 1.35
}


MANA_COST = 8


# ==========================================
# 2. PLAYER CLASS
# ==========================================

class Player:

    def __init__(self, name, player_class, health=None,
                 mana=None, inventory=None):

        stats = CLASS_INFO[player_class]

        self.name = name
        self.player_class = player_class

        self.max_health = stats["health"]
        self.damage = stats["damage"]
        self.max_mana = stats["mana"]

        if health is None:
            self.health = self.max_health
        else:
            self.health = health

        if mana is None:
            self.mana = self.max_mana
        else:
            self.mana = mana

        if inventory is None:
            self.inventory = {
                "Health Potion": 2,
                "Mana Potion": 1
            }
        else:
            self.inventory = inventory

    def is_alive(self):
        return self.health > 0

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def restore_mana(self, amount):
        self.mana = min(self.max_mana, self.mana + amount)

    def to_dict(self):
        return {
            "name": self.name,
            "player_class": self.player_class,
            "health": self.health,
            "mana": self.mana,
            "inventory": self.inventory
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["name"],
            data["player_class"],
            data["health"],
            data["mana"],
            data["inventory"]
        )


# ==========================================
# 3. ENEMY CLASS
# ==========================================

class Enemy:

    def __init__(self, name, enemy_type, health, damage):

        self.name = name
        self.enemy_type = enemy_type

        self.max_health = health
        self.health = health
        self.damage = damage

        # Temporary combat effects
        self.stun_turns = 0
        self.decay_turns = 0
        self.decay_damage = 3

    def is_alive(self):
        return self.health > 0

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)


# ==========================================
# 4. DUNGEON CLASS
# ==========================================

class Dungeon:

    def __init__(self, floor=1, difficulty="normal"):

        self.floor = floor
        self.difficulty = difficulty

    def create_encounter(self):

        # 25% chance of having no enemy
        if random.randint(1, 100) <= 25:
            return None

        # Choose which enemies can appear
        if self.floor <= 2:
            available_enemies = ENEMY_TYPES[:3]

        elif self.floor <= 4:
            available_enemies = ENEMY_TYPES[:5]

        else:
            available_enemies = ENEMY_TYPES

        chosen = random.choice(available_enemies)

        # Increase enemy strength as floors progress
        enemy_health = chosen["health"] + (self.floor - 1) * 2
        enemy_damage = chosen["damage"] + (self.floor - 1) // 2

        # Apply the selected difficulty
        multiplier = DIFFICULTY_MULTIPLIERS[self.difficulty]

        enemy_health = max(1, int(enemy_health * multiplier))
        enemy_damage = max(1, int(enemy_damage * multiplier))

        return Enemy(
            chosen["name"],
            chosen["type"],
            enemy_health,
            enemy_damage
        )

    def advance(self):
        self.floor += 1


# ==========================================
# 5. SAVE MANAGER CLASS
# ==========================================

class SaveManager:

    @staticmethod
    def save_game(game, filename):

        save_data = {
            "floor": game.dungeon.floor,
            "difficulty": game.dungeon.difficulty,
            "players": []
        }

        # Save both players
        for player in game.players:
            save_data["players"].append(player.to_dict())

        # Write information into a JSON file
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(save_data, file, indent=4)

        print("\nGame saved successfully!")

    @staticmethod
    def load_game(filename):

        # Read information from the JSON file
        with open(filename, "r", encoding="utf-8") as file:
            save_data = json.load(file)

        if len(save_data["players"]) != 2:
            raise ValueError("Save file must contain exactly two players.")

        difficulty = save_data["difficulty"]

        if difficulty not in DIFFICULTY_MULTIPLIERS:
            raise ValueError("Invalid difficulty in save file.")

        # Re-create both Player objects
        players = []

        for player_data in save_data["players"]:
            players.append(Player.from_dict(player_data))

        # Re-create the dungeon
        dungeon = Dungeon(save_data["floor"], difficulty)

        return Game(players, dungeon, filename)


# ==========================================
# 6. GAME CLASS
# ==========================================

class Game:

    def __init__(self, players, dungeon, save_filename="savegame.json"):

        self.players = players
        self.dungeon = dungeon
        self.save_filename = save_filename

    # --------------------------------------
    # CLASS INFORMATION
    # --------------------------------------

    def show_class_information(self):

        print("\n========== CLASS INFORMATION ==========")

        for name, info in CLASS_INFO.items():

            print(f"\n{name}")
            print(
                f"Health: {info['health']} | "
                f"Damage: {info['damage']} | "
                f"Mana: {info['mana']}"
            )

            print("Description:", info["description"])
            print("Ability:", info["ability"])

        print("=======================================")

    # --------------------------------------
    # PLAYER CREATION
    # --------------------------------------

    def create_players(self):

        players = []

        print("\nTwo travellers approach the dungeon...")

        # Create exactly two players
        for number in range(1, 3):

            name = input(
                f"\nPlayer {number}, enter your name: "
            ).strip()

            while not name:
                name = input("Please enter a name: ").strip()

            while True:

                print("\nAvailable classes:")

                for class_name in CLASS_INFO:
                    print("-", class_name)

                choice = input(
                    f"{name}, choose your class: "
                ).strip().title()

                if choice in CLASS_INFO:
                    break

                print("That class does not exist.")

            players.append(Player(name, choice))

        return players

    # --------------------------------------
    # MAIN MENU
    # --------------------------------------

    def main_menu(self):

        while True:

            print("\n========== DUNGEON RPG ==========")
            print("1. New Game")
            print("2. Load Game")
            print("3. Class Information")
            print("4. Exit")

            choice = input("\nChoose an option: ").strip()

            if choice == "1":

                self.players = self.create_players()

                self.dungeon = Dungeon(
                    1,
                    self.dungeon.difficulty
                )

                self.explore_dungeon()

            elif choice == "2":

                filename = input(
                    f"Save filename [{self.save_filename}]: "
                ).strip()

                if filename:
                    self.save_filename = filename

                try:

                    loaded_game = SaveManager.load_game(
                        self.save_filename
                    )

                    self.players = loaded_game.players
                    self.dungeon = loaded_game.dungeon

                    print("\nSave loaded successfully!")

                    self.explore_dungeon()

                except (OSError, json.JSONDecodeError,
                        KeyError, ValueError, TypeError) as error:

                    print("\nCould not load save:", error)

            elif choice == "3":

                self.show_class_information()

            elif choice == "4":

                print("\nThanks for playing!")
                return

            else:

                print("\nPlease choose a valid option.")

    # --------------------------------------
    # INVENTORY
    # --------------------------------------

    def use_item(self, player):

        items = list(player.inventory.keys())

        print("\n========== INVENTORY ==========")

        for number, item in enumerate(items, start=1):
            print(f"{number}. {item} x{player.inventory[item]}")

        print("0. Go back")

        choice = input("\nChoose an item: ").strip()

        if choice == "0":
            return False

        if not choice.isdigit():
            print("Invalid choice.")
            return False

        if not 1 <= int(choice) <= len(items):
            print("Invalid choice.")
            return False

        item = items[int(choice) - 1]

        if player.inventory[item] <= 0:
            print("You do not have any of those.")
            return False

        if item == "Health Potion":

            if player.health == player.max_health:
                print("Your health is already full.")
                return False

            player.heal(15)
            print(f"{player.name} restored 15 health.")

        elif item == "Mana Potion":

            if player.mana == player.max_mana:
                print("Your mana is already full.")
                return False

            player.restore_mana(12)
            print(f"{player.name} restored 12 mana.")

        player.inventory[item] -= 1

        return True

    # --------------------------------------
    # CLASS ABILITIES
    # --------------------------------------

    def class_ability(self, player, enemy):

        if player.mana < MANA_COST:
            print(f"You need {MANA_COST} mana to use an ability.")
            return False

        abilities = {
            "Moth Keeper": "Decaying Swarm",
            "Bell Ringer": "Discordant Toll",
            "Chef": "Culinary Creation",
            "Fisherman": "Bass Bludgeoning"
        }

        ability_class = player.player_class

        # Librarian chooses between two random abilities
        if ability_class == "Librarian":

            choices = random.sample(list(abilities.keys()), 2)

            print("\nForbidden Knowledge offers two abilities:")

            for number, class_name in enumerate(choices, start=1):
                print(f"{number}. {class_name}: {abilities[class_name]}")

            while True:

                choice = input("Choose one (1 or 2): ").strip()

                if choice in ("1", "2"):
                    ability_class = choices[int(choice) - 1]
                    break

                print("You must choose one of the two abilities.")

        # Pay the mana cost
        player.mana -= MANA_COST

        # MOTH KEEPER
        if ability_class == "Moth Keeper":

            enemy.decay_turns = random.randint(2, 3)
            enemy.decay_damage = 3

            print(
                "Moths surround the enemy and deal damage "
                "after its next few turns."
            )

        # BELL RINGER
        elif ability_class == "Bell Ringer":

            enemy.stun_turns = 1

            for teammate in self.players:

                if teammate.is_alive():
                    teammate.take_damage(3)

            print(
                "The enemy is stunned, but each living teammate "
                "takes 3 damage."
            )

        # CHEF
        elif ability_class == "Chef":

            living_players = [
                teammate for teammate in self.players
                if teammate.is_alive()
            ]

            print("\nChoose who receives the meal:")

            for number, teammate in enumerate(living_players, start=1):
                print(f"{number}. {teammate.name}")

            while True:

                choice = input("Choose a player: ").strip()

                if choice.isdigit() and 1 <= int(choice) <= len(living_players):
                    target = living_players[int(choice) - 1]
                    break

                print("Please choose a valid player.")

            result = random.randint(1, 100)

            if result <= 40:

                target.heal(12)

                print(
                    f"The meal works! {target.name} restores 12 health."
                )

            elif result <= 80:

                enemy.take_damage(10)

                print("The meal explodes! The enemy takes 10 damage.")

            else:

                target.take_damage(8)

                print(
                    f"The meal backfires! {target.name} takes 8 damage."
                )

        # FISHERMAN
        elif ability_class == "Fisherman":

            damage = player.damage * 3

            enemy.take_damage(damage)

            print(
                f"The giant bass deals {damage} damage!"
            )

        print(
            f"{player.name} used {abilities[ability_class]}!"
        )

        return True

    # --------------------------------------
    # PLAYER TURN
    # --------------------------------------

    def player_turn(self, player, enemy):

        if not player.is_alive() or not enemy.is_alive():
            return

        while True:

            print(f"\n========== {player.name}'S TURN ==========")

            print(
                f"Health: {player.health}/{player.max_health}"
            )

            print(
                f"Mana: {player.mana}/{player.max_mana}"
            )

            print(
                f"{enemy.name}: {enemy.health}/{enemy.max_health} HP"
            )

            print("\n1. Attack")
            print("2. Class Ability")
            print("3. Inventory")
            print("4. View Party Status")

            choice = input("\nChoose an action: ").strip()

            if choice == "1":

                enemy.take_damage(player.damage)

                print(
                    f"{player.name} deals {player.damage} damage!"
                )

                return

            elif choice == "2":

                if self.class_ability(player, enemy):
                    return

            elif choice == "3":

                if self.use_item(player):
                    return

            elif choice == "4":

                self.show_party()

            else:

                print("Please choose a valid option.")

    # --------------------------------------
    # ENEMY TURN
    # --------------------------------------

    def enemy_turn(self, enemy):

        if not enemy.is_alive():
            return

        if enemy.stun_turns > 0:

            enemy.stun_turns -= 1

            print(
                f"{enemy.name} is stunned and cannot attack!"
            )

        else:

            living_players = [
                player for player in self.players
                if player.is_alive()
            ]

            if living_players:

                target = random.choice(living_players)

                target.take_damage(enemy.damage)

                print(
                    f"{enemy.name} attacks {target.name} "
                    f"for {enemy.damage} damage!"
                )

        # Moth Keeper's decay effect
        if enemy.decay_turns > 0 and enemy.is_alive():

            enemy.take_damage(enemy.decay_damage)

            enemy.decay_turns -= 1

            print(
                f"The moths deal {enemy.decay_damage} decay damage!"
            )

            if enemy.decay_turns == 0:
                print("The moth swarm disappears.")

    # --------------------------------------
    # COMBAT
    # --------------------------------------

    def fight(self, enemy):

        print(f"\nA {enemy.name} ({enemy.enemy_type}) appears!")

        print(
            f"It has {enemy.health} health "
            f"and deals {enemy.damage} damage."
        )

        while (
            enemy.is_alive()
            and any(player.is_alive() for player in self.players)
        ):

            # Both players take their turns
            for player in self.players:

                if enemy.is_alive() and player.is_alive():
                    self.player_turn(player, enemy)

            # Enemy takes its turn
            if (
                enemy.is_alive()
                and any(player.is_alive() for player in self.players)
            ):

                self.enemy_turn(enemy)

            # Display updated health
            print(
                f"\n{enemy.name}: "
                f"{enemy.health}/{enemy.max_health} HP"
            )

            for player in self.players:

                print(
                    f"{player.name}: "
                    f"{player.health}/{player.max_health} HP"
                )

        if enemy.is_alive():

            print("\nBoth players have been defeated. GAME OVER.")

            return False

        print(f"\nThe {enemy.name} has been defeated!")

        self.victory_rewards()

        return True

    # --------------------------------------
    # VICTORY REWARDS
    # --------------------------------------

    def victory_rewards(self):

        print("\nYou search the area for supplies...")

        for player in self.players:
            player.restore_mana(4)

        reward = random.randint(1, 4)

        if reward <= 2:

            recipient = random.choice(self.players)

            recipient.inventory["Health Potion"] += 1

            print(f"{recipient.name} found a Health Potion!")

        elif reward == 3:

            recipient = random.choice(self.players)

            recipient.inventory["Mana Potion"] += 1

            print(f"{recipient.name} found a Mana Potion!")

        else:

            print("You did not find any items.")

        print("Both players recover 4 mana.")

    # --------------------------------------
    # PARTY STATUS
    # --------------------------------------

    def show_party(self):

        print("\n========== PARTY STATUS ==========")

        for player in self.players:

            print(f"\n{player.name} - {player.player_class}")

            print(
                f"Health: {player.health}/{player.max_health}"
            )

            print(
                f"Mana: {player.mana}/{player.max_mana}"
            )

            print("Inventory:", player.inventory)

        print("==================================")

    # --------------------------------------
    # DUNGEON EXPLORATION
    # --------------------------------------

    def explore_dungeon(self):

        while self.dungeon.floor <= 10:

            print("\n" + "=" * 40)

            print(
                f"              FLOOR {self.dungeon.floor}"
            )

            print("=" * 40)

            enemy = self.dungeon.create_encounter()

            if enemy is None:

                print("The floor is quiet. No enemies appear.")

            else:

                if not self.fight(enemy):
                    return

            self.show_party()

            # Check whether the final floor is complete
            if self.dungeon.floor == 10:
                break

            while True:

                print("\n1. Continue to next floor")
                print("2. Save and return to main menu")

                choice = input("\nChoose an option: ").strip()

                if choice == "1":

                    self.dungeon.advance()

                    break

                elif choice == "2":

                    filename = input(
                        f"Save filename [{self.save_filename}]: "
                    ).strip()

                    if filename:
                        self.save_filename = filename

                    try:

                        SaveManager.save_game(
                            self,
                            self.save_filename
                        )

                    except OSError as error:

                        print("Could not save game:", error)

                    return

                else:

                    print("Please choose 1 or 2.")

        print("\nCONGRATULATIONS!")

        print(
            "Both players have completed all 10 floors!"
        )


# ==========================================
# 7. ARGPARSE
# ==========================================

def parse_arguments():

    parser = argparse.ArgumentParser(
        description="A two-player, turn-based dungeon RPG."
    )

    parser.add_argument(
        "--difficulty",
        choices=["easy", "normal", "hard"],
        default="normal",
        help="Choose the enemy difficulty."
    )

    parser.add_argument(
        "--save",
        default="savegame.json",
        help="Choose the name of the save file."
    )

    parser.add_argument(
        "--load",
        action="store_true",
        help="Load the selected save file when starting."
    )

    return parser.parse_args()


# ==========================================
# 8. START THE PROGRAM
# ==========================================

def main():

    args = parse_arguments()

    # Try to load a save file if --load was used
    if args.load:

        try:

            game = SaveManager.load_game(args.save)

            game.save_filename = args.save

            print("\nSave loaded successfully!")

            game.explore_dungeon()

            game.main_menu()

            return

        except (OSError, json.JSONDecodeError,
                KeyError, ValueError, TypeError) as error:

            print("\nCould not load save:", error)

            print("Starting a new game instead.")

    # Start a new game
    game = Game(
        [],
        Dungeon(1, args.difficulty),
        args.save
    )

    game.main_menu()


if __name__ == "__main__":
    main()
