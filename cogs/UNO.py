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

# converts a given color (red, yellow, green, or blue) into the color unicode for display
card_color_into_code = {
    "RED": discord.Colour.red(),
    "YELLOW": discord.Colour.from_rgb(255, 255, 0),
    "GREEN": discord.Colour.green(),
    "BLUE": discord.Colour.blue(),
    "BLACK": discord.Colour.from_rgb(0, 0, 0)
}

# TODO: make command to exit the current game
# TODO: game crashes when a player plays a special card that causes another player to have over 19 cards
class UNO(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("UNO is ready to go")

    # command to play UNO
    @commands.command()
    async def play(self, ctx):
        users = await self.game_prompt(ctx)
        if len(users) == 0:
            await ctx.send("I guess no one wants to play")
        else:
            await ctx.send("The players of this game are:")
            for user in users:
                await ctx.send(user.mention)
            # game setup
            deck = Deck()
            player_list = []
            for user in users:
                player_list.append(Player(user))
            shuffle(player_list)
            self.start_game(deck, player_list)
            deck.setup()
            curr_color = deck.get_top_card().color
            reverse = False
            index = 0
            curr_player = player_list[index]
            # plays the game
            while not await self.winner(player_list):
                card_in_play = deck.get_top_card()
                embed = discord.Embed(title="It is {}'s turn".format(curr_player.discord_info.name),
                                      description="The current card is {}".format(card_in_play),
                                      color=card_color_into_code[curr_color])
                await ctx.send(embed=embed)
                # get input from the player
                next_player_index = await self.get_next_player(player_list, index, reverse)
                action = await self.get_player_action(ctx, curr_player, card_in_play, curr_color, deck)
                if action is None:  # player drew
                    embed = discord.Embed(title="{} drew a card".format(curr_player.discord_info.name),
                                          description="The current card is {}".format(card_in_play),
                                          color=card_color_into_code[curr_color])
                    await ctx.send(embed=embed)
                else:  # player played a card
                    card = action
                    embed = discord.Embed(title="{} played {}".format(curr_player.discord_info.name, str(card)),
                                          color=card_color_into_code[card.color])
                    await ctx.send(embed=embed)
                    # get color change when a black card is played
                    if card.color == "BLACK":
                        color_choice = await self.get_color_change(ctx, curr_player, curr_color)
                        embed = discord.Embed(title="WILD CARD",
                                              description="{} changed the color to {}".format(curr_player.discord_info.name, str(color_change_emoji[color_choice])),
                                              color=card_color_into_code[color_choice])
                        await ctx.send(embed=embed)
                        curr_color = color_choice
                    if card.value == "REVERSE":
                        reverse = not reverse
                    curr_player.play_card(card)
                    deck.add_to_discard(card)
                    next_player_index = await self.handle_action_card(ctx, card, deck, player_list, reverse, index, next_player_index)
                index = next_player_index
                curr_player = player_list[next_player_index]
                # used to change the color when a WILD card is played
                curr_color = card.color if card.color != "BLACK" else curr_color
            # someone won the game
            await self.display_winner(ctx, player_list)

    # asks people to join and returns the list of people who are playing
    async def game_prompt(self, ctx):
        embed = discord.Embed(title="Want to play UNO?", description="React to the message to queue up!",
                              color=discord.Colour.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_image(
            url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/UNO_Logo.svg/550px-UNO_Logo.svg.png")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("\U0001F44D")  # thumbs-up emoji
        await asyncio.sleep(10)
        cache_msg = await ctx.channel.fetch_message(msg.id)
        reaction = cache_msg.reactions[0]
        users = await reaction.users().flatten()
        users.pop(0)  # removes the bot from the player list
        return users

    # deals players 7 cards for the start of the game
    def start_game(self, deck, player_list):
        deck.shuffle()
        for num in range(7):
            for player in player_list:
                player.take_card(deck.deal())

    # determines if there is a winner
    async def winner(self, player_list):
        for player in player_list:
            if len(player.get_hand()) == 0:
                return True
        return False

    # determines the winner and DMs everyone who played
    async def display_winner(self, ctx, player_list):
        player_index = 0
         # dms everyone if they won or lost
        while player_index < len(player_list):
            user = player_list[player_index].discord_info
            if len(player_list[player_index].get_hand()) == 0:
                winner_index = player_index
                await user.send("Congratulations! You won!")
                await ctx.send("Congratulations! " + player_list[winner_index].discord_info.mention + " won the game!")
            else:
                await user.send("Sorry, you lost. Better luck next time.")
            player_index += 1

    # gets the index of next player based on the current index and if a reverse has been played
    async def get_next_player(self, player_list, index, reverse):
        return (index - 1) % len(player_list) if reverse else (index + 1) % len(player_list)

    # asks the player what they want to do for their turn
    async def get_player_action(self, ctx, curr_player, card_in_play, curr_color, deck):
        player = curr_player.discord_info
        valid = False
        while not valid:
            message = "Play a card by picking the emoji corresponding to the card or click the 'joker' to draw a card." \
                      "\nThe current card is {}".format(card_in_play)

            embed = discord.Embed(title="It is your turn!",
                                  description=message,
                                  color=card_color_into_code[curr_color])
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
                if len(curr_player.get_hand()) >= 19:
                    await player.send("You have the max amount of cards, so your turn is skipped instead ")
                else:
                    curr_player.take_card(deck.deal())
                    await player.send("You drew {}".format(str(curr_player.hand[-1])))
                valid = True
            else:
                card_played = curr_player.card_at(index)
                await player.send("You played {}".format(str(card_played)))
                if card_played.can_play(card_in_play) or card_played.can_play_color(curr_color):
                    valid = True
                else:
                    await player.send("Invalid card choice. Pick again or draw")
        return card_played  # return the card played or None if drew a card

    # deals with action cards
    async def handle_action_card(self, ctx, card, deck, p_list, reverse, index, next_player_index):
        curr_user = p_list[index].discord_info
        next_player = p_list[next_player_index]
        next_user = next_player.discord_info
        if card.value == "REVERSE":
            # reverse the cycle
            await ctx.send("The tides have turned")
            next_player_index = await self.get_next_player(p_list, index, reverse)
        elif card.value == "+2":
            for i in range(2):
                p_list[next_player_index].take_card(deck.deal())
            await next_user.send("{} played a +2. You drew {} and {}. Your turn is skipped".format(curr_user.name,
                                                                                                   next_player.card_at(-2),
                                                                                                   next_player.card_at(-1)))
            await ctx.send("{} drew 2 cards and their turn is skipped".format(p_list[next_player_index].discord_info.name))
            next_player_index = await self.get_next_player(p_list, next_player_index, reverse)  # skips the next player
        elif card.value == "+4":
            for i in range(4):
                p_list[next_player_index].take_card(deck.deal())
            await next_user.send("{} played a +4. You drew {}, {}, {}, and {}. Your turn is skipped".format(curr_user.name,
                                                                                                            next_player.card_at(-4),
                                                                                                            next_player.card_at(-3),
                                                                                                            next_player.card_at(-2),
                                                                                                            next_player.card_at(-1)))
            await ctx.send("{} drew 4 cards and their turn is skipped".format(p_list[next_player_index].discord_info.name))
            next_player_index = await self.get_next_player(p_list, next_player_index, reverse)  # skips the next player
        elif card.value == "SKIP":
            await next_user.send("{} played a skip. Your turn is skipped".format(curr_user.name))
            await ctx.send("{}'s turn is skipped".format(p_list[next_player_index].discord_info.name))
            next_player_index = await self.get_next_player(p_list, next_player_index, reverse)  # skips the next player
        return next_player_index

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
    def deal(self):
        if len(self.deck) == 0:
            top_card = self.deck.discard.pop()
            self.deck = self.discard
            self.discard = []
            self.discard.append(top_card)  # keep the top card in play
            shuffle()
        return self.deck.pop()

    # adds a card to the discard pile
    def add_to_discard(self, card):
        self.discard.append(card)

    # returns the top card of the discard pile (card in play)
    def get_top_card(self):
        return self.discard[-1]

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

    # adds a card to the player's hand
    def take_card(self, card):
        self.hand.append(card)

    # returns a card from the player's hand at a specified index
    def card_at(self, index):
        return self.hand[index]

    def get_hand(self):
        return self.hand

    def play_card(self, card):
        self.hand.remove(card)

    # prints the cards in the player's hand
    def print_hand(self):
        result = ""
        for card in range(len(self.hand)):
            result += card_index[card] + ": " + str(self.hand[card]) + "\n"
        return result
