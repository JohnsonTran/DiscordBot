import discord
import asyncio
from discord.ext import commands
from random import shuffle


# assign card index to emojis (1-10, A-I, joker for draw) [19 cards in hand and draw]
card_index = ["\U00000031\U000020E3",  # 1
              "\U00000032\U000020E3",
              "\U00000033\U000020E3",
              "\U00000034\U000020E3",
              "\U00000035\U000020E3",
              "\U00000036\U000020E3",
              "\U00000037\U000020E3",
              "\U00000038\U000020E3",
              "\U00000039\U000020E3",
              "\U0001F51F",  # 10
              "\U0001F1E6",  # A
              "\U0001F1E7",
              "\U0001F1E8",
              "\U0001F1E9",
              "\U0001F1EA",
              "\U0001F1EB",
              "\U0001F1EC",
              "\U0001F1ED",
              "\U0001F1EE",  # I
              "\U0001F0CF"]  # joker for draw

# assign colors to their emoji square unicode
card_emoji = {
    "RED": "\U0001F7E5",
    "YELLOW": "\U0001F7E8",
    "GREEN": "\U0001F7E9",
    "BLUE": "\U0001F7E6",
    "BLACK": "\U00002B1B"
}

# assign value to emoji unicode
value_emoji = {
    "0": "\U00000030\U000020E3",
    "1": "\U00000031\U000020E3",
    "2": "\U00000032\U000020E3",
    "3": "\U00000033\U000020E3",
    "4": "\U00000034\U000020E3",
    "5": "\U00000035\U000020E3",
    "6": "\U00000036\U000020E3",
    "7": "\U00000037\U000020E3",
    "8": "\U00000038\U000020E3",
    "9": "\U00000039\U000020E3",
    "SKIP": "\U000023E9",
    "REVERSE": "\U0001F503",
    "+2": "\U00002795\U00000032\U000020E3",
    "+4": "\U00002795\U00000034\U000020E3",
    "WILD": "\U0001F1FC\U0001F1EE\U0001F1F1\U0001F1E9"
}

# assign colors to emoji circle unicode for choosing color
color_change_emoji = {
    "RED": "\U0001F534",
    "YELLOW": "\U0001F7E1",
    "GREEN": "\U0001F7E2",
    "BLUE": "\U0001F535"
}

# deals players 7 cards for the start of the game
def start_game(deck, player_list):
    deck.shuffle()
    for num in range(7):
        for player in player_list:
            deck.deal(player)

# gets the index of next player based on the current index and if a reverse has been played
async def get_next_player(player_list, index, reverse):
    return (index - 1) % len(player_list) if reverse else (index + 1) % len(player_list)

# deals with action cards
# TODO: +4 and +2 and skip does not skip next player's turn (make a new method that returns the new nex_player_index or return it at the end and assign it)
async def handle_action_card(ctx, card, deck, p_list, reverse, index, next_player_index, curr_color):
    if card.value == "REVERSE":
        # reverse the cycle
        await ctx.send("The tides have turned")
        reverse = not reverse
        next_player_index = await get_next_player(p_list, index, reverse)
    elif card.value == "+2":
        for i in range(2):
            deck.deal(p_list[next_player_index])
        await ctx.send("{} drew 2 cards and their turn is skipped".format(p_list[next_player_index].discord_info.name))
        # skips the next player
        next_player_index = await get_next_player(p_list, next_player_index, reverse)
    elif card.value == "+4":
        for i in range(4):
            deck.deal(p_list[next_player_index])
        # skips the next player
        await ctx.send("{} drew 4 cards and their turn is skipped".format(p_list[next_player_index].discord_info.name))
        next_player_index = await get_next_player(p_list, next_player_index, reverse)
    elif card.value == "SKIP":
        # skips the next player
        await ctx.send("{}'s turn is skipped".format(p_list[next_player_index].discord_info.name))
        next_player_index = await get_next_player(p_list, next_player_index, reverse)


# converts a given color (red, yellow, green, or blue) into unicode for display
# TODO: convert into dictionary
def card_color_into_code(curr_color):
    if curr_color == "RED":
        return discord.Colour.red()
    elif curr_color == "YELLOW":
        return discord.Colour.from_rgb(255, 255, 0)
    elif curr_color == "GREEN":
        return discord.Colour.green()
    elif curr_color == "BLUE":
        return discord.Colour.blue()
    elif curr_color == "BLACK":
        return discord.Colour.from_rgb(0, 0, 0)


# determines if there is a winner
def winner(player_list):
    for player in player_list:
        if len(player.hand) == 0:
            return True
    return False


class UNO(commands.Cog):

    game_start = False

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("UNO is ready to go")

    # command to play UNO
    @commands.command()
    # TODO: make command to exit the current game
    async def play(self, ctx):
        if self.game_start:
            await ctx.send("There is already a game in progress. Wait until it is finished.")
        else:
            self.game_start = True
            embed = discord.Embed(title="Want to play UNO?", description="React to the message to queue up!",
                                  color=discord.Colour.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            embed.set_image(url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/UNO_Logo.svg/550px-UNO_Logo.svg.png")
            msg = await ctx.send(embed=embed)
            await msg.add_reaction("\U0001F44D")
            await asyncio.sleep(5)
            cache_msg = await ctx.channel.fetch_message(msg.id)
            reaction = cache_msg.reactions[0]
            users = await reaction.users().flatten()
            users.pop(0)  # gets rid of the bot that reacted to the message
            if len(users) == 0:
                await ctx.send("I guess no one wants to play")
                self.game_start = False
            else:
                await ctx.send("The players of this game are:")
                for user in users:
                    await ctx.send(user.mention)

                # ***uncomment if considering other reactions***
                # players = []
                # for reaction in cache_msg.reactions:
                #     async for user in reaction.users():
                #         players.append(user)
                # print(players)

                # game setup
                deck = Deck()
                player_list = []
                for user in users:
                    player_list.append(Player(user))
                # shuffle(player_list)
                start_game(deck, player_list)
                index = 0
                deck.setup()
                curr_color = deck.discard[0].color
                reverse = False
                curr_player = player_list[index]
                # plays the game
                while not winner(player_list):
                    card_in_play = deck.discard[len(deck.discard) - 1]
                    embed = discord.Embed(title="It is {}'s turn".format(curr_player.discord_info.name),
                                          description="The current card is {}".format(card_in_play),
                                          color=card_color_into_code(curr_color))
                    await ctx.send(embed=embed)
                    # get input from the player
                    while True:
                        next_player_index = await get_next_player(player_list, index, reverse)
                        action = await self.get_player_action(ctx, curr_player, card_in_play, curr_color, deck)
                        if action is None:  # player drew
                            embed = discord.Embed(title="{} drew a card".format(curr_player.discord_info.name),
                                                  description="The current card is {}".format(card_in_play),
                                                  color=card_color_into_code(curr_color))
                            await ctx.send(embed=embed)
                            card = card_in_play  # used to fix bug for drawing on the first turn (not sure if needed)
                            break
                        else:  # player played a card
                            card = action
                            embed = discord.Embed(title="{} played {}".format(curr_player.discord_info.name, str(card)),
                                                  color=card_color_into_code(card.color))
                            await ctx.send(embed=embed)
                            # get color change when a black card is played
                            if card.color == "BLACK":
                                color_choice = await self.get_color_change(ctx, curr_player, curr_color)
                                embed = discord.Embed(title="WILD CARD",
                                                      description="{} changed the color to {}".format(curr_player.discord_info.name, str(color_change_emoji[color_choice])),
                                                      color=card_color_into_code(color_choice))
                                await ctx.send(embed=embed)
                                curr_color = color_choice
                            curr_player.hand.remove(card)
                            deck.discard.append(card)
                            # TODO: work on special actions
                            await handle_action_card(ctx, card, deck, player_list, reverse, index, next_player_index, curr_color)
                            break  # end of player's turn, got a valid move

                        # if 0 <= int(action) < len(curr_player.hand):
                        #     card = curr_player.hand[int(action)]
                        #     # check if the card is playable
                        #     if card.can_play(card_in_play) or card.can_play_color(curr_color):
                        #         # plays the card
                        #         curr_player.hand.remove(card)
                        #         deck.discard.append(card)
                        #         # do special card actions
                        #         handle_action_card(card, deck, player_list, reverse, index, next_player_index, curr_color)
                        #         break  # end of player's turn, got a valid move
                    index = next_player_index
                    curr_player = player_list[next_player_index]
                    # used to change the color when a WILD card is played
                    curr_color = card.color if card.color != "BLACK" else curr_color

                # displays the winner
                # TODO: make winner message
                self.game_start = False
                winner_index = 0
                while len(player_list[winner_index].hand) != 0 and winner_index < len(player_list):
                    winner_index += 1
                print("The winner is Player", winner_index + 1)

    # TODO: When the player has 19 cards, their turn is skipped unless they can play a card
    # asks the player what they want to do for their turn
    async def get_player_action(self, ctx, curr_player, card_in_play, curr_color, deck):
        player = curr_player.discord_info
        valid = False
        while not valid:
            message = "Play a card by picking the emoji corresponding to the card or click the 'joker' to draw a card." \
                      "\nThe current card is {}".format(card_in_play)

            embed = discord.Embed(title="It is your turn!",
                                  description=message,
                                  color=card_color_into_code(curr_color))
            for card in range(len(curr_player.hand)):
                embed.add_field(name="\u200b", value=str(card_index[card] + ": " + str(curr_player.hand[card])),
                                inline=False)
            embed.add_field(name="\u200b", value=str(card_index[len(card_index) - 1]) + ": Draw", inline=False)
            msg = await player.send(embed=embed)
            for card in range(len(curr_player.hand)):
                await msg.add_reaction(card_index[card])
            await msg.add_reaction(card_index[len(card_index) - 1])  # add draw emoji

            def check(reaction, user):
                return str(reaction.emoji) in card_index and user == player
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=10000.0, check=check)
            except asyncio.TimeoutError:
                await player.send("You took too long")
            await player.send("You chose {}".format(str(reaction.emoji)))
            index = card_index.index(str(reaction.emoji))
            card_played = None
            if index == 19:
                deck.deal(curr_player)
                await player.send("You drew {}".format(str(curr_player.hand[-1])))
                valid = True
            else:
                card_played = curr_player.hand[index]
                await player.send("You played {}".format(str(card_played)))
                if card_played.can_play(card_in_play) or card_played.can_play_color(curr_color):
                    await player.send("Playing card")
                    valid = True
                else:
                    await player.send("Invalid card choice. Pick again or draw")
        return card_played  # return the card played or None if drew a card

    # asks the player what color they want to change to
    async def get_color_change(self, ctx, curr_player, curr_color):
        player = curr_player.discord_info
        embed = discord.Embed(title="Pick a color!",
                              description="What color do you want to change to? The current color is: {}".format(color_change_emoji[curr_color]),
                              color=discord.Colour.from_rgb(0, 0, 0))
        msg = await player.send(embed=embed)
        for color in color_change_emoji:
            await msg.add_reaction(color_change_emoji[color])

        def check(reaction, user):
            return str(reaction.emoji) in color_change_emoji.values() and user == player

        try:
            reaction, user = await self.client.wait_for("reaction_add", timeout=10000.0, check=check)
        except asyncio.TimeoutError:
            await player.send("You took too long")
        await player.send("You chose {}".format(str(reaction.emoji)))
        color_choice = None
        for color, unicode in color_change_emoji.items():
            if unicode == str(reaction.emoji):
                color_choice = color
        return color_choice


def setup(client):
    client.add_cog(UNO(client))


# UNO game classes
# Card class to represent the cards for the game
class Card:

    # initializer that creates card with value, color, and special ability
    def __init__ (self, value, color, special):
        self.value = value  # should be a string
        self.color = color
        self.special = special

    # getter methods
    def get_value(self):
        return self.value

    def get_color(self):
        return self.color

    def get_special(self):
        return self.special

    # determines if this card can be played based on another card (should be card in play)
    def can_play(self, card):
        # a card can get played if it shares the same value or color as the current card in play
        # a black card (WILD) can be played at all times
        return self.value == card.value or self.color == card.color or self.color == "BLACK"

    # determines if this card can be played based on a color (this is for WILD cards)
    def can_play_color(self, color):
        return self.color == color

    # representation of the card
    def __repr__(self):
        return card_emoji[self.color] + " " + value_emoji[self.value]


# Deck class that represents the deck and all the cards for the game
class Deck:

    def __init__(self):
        self.deck = []
        self.discard = []
        # makes the deck of cards
        color = ["RED", "YELLOW", "GREEN", "BLUE"]
        for i in range(4):
            # 1 0 for every color
            self.deck.append(Card("0", color[i], ""))
            for j in range(1, 10):
                # 2 1-9 for every color
                self.deck.append(Card(str(j), color[i], ""))
                self.deck.append(Card(str(j), color[i], ""))
            # 2 draw 2, skip, and reverses for every color
            for j in range(2):
                self.deck.append(Card("+2", color[i], "Draw 2 cards"))
                self.deck.append(Card("SKIP", color[i], "Skip next player's turn"))
                self.deck.append(Card("REVERSE", color[i], "Reverse the player order"))
        # 4 wild and draw 4 for the deck
        for i in range(4):
            self.deck.append(Card("WILD", "BLACK", "Choose any color"))
            self.deck.append(Card("+4", "BLACK", "Draw 4 cards and choose any color"))

    # shuffles the deck
    def shuffle(self):
        shuffle(self.deck)

    # gives a specified player a card
    def deal(self, player):
        if len(self.deck) == 0:
            top_card = self.deck.discard.pop()
            self.deck = self.discard
            self.discard = []
            self.discard.append(top_card)  # keep the top card in play
            shuffle()
        player.hand.append(self.deck.pop())

    # sets up the first card of the game, changes the card if the first card is WILD
    def setup(self):
        first_card = self.deck.pop()
        while first_card.color == "BLACK":
            self.deck.append(first_card)
            shuffle()
        self.discard.append(first_card)


# Player class to represent data for the player
class Player:

    def __init__(self, member):
        self.hand = []
        self.discord_info = member

    # gets a card from the deck
    def draw(self):
        Deck.deal(self)

    # plays the specified card
    def play(self, index):
        if self.hand[index].can_play(Deck.deck[len(Deck.deck)]):
            return self.hand[index]
        else:
            return None

    # prints the cards in the player's hand
    def print_hand(self):
        result = ""
        for card in range(len(self.hand)):
            result += card_index[card] + ": " + str(self.hand[card]) + "\n"
        return result
