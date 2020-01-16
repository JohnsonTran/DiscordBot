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
    "BLUE": "\U0001F7E6"
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

# deals players 7 cards to setup the game
def start_game(deck, player_list):
    deck.shuffle()
    for num in range(7):
        for player in player_list:
            deck.deal(player)

# TODO: When the player has 19 cards, their turn is skipped unless they can play a card
# TODO: Get player choice from reaction
# asks the player what they want to do for their turn
async def get_player_action(ctx, curr_player, card_in_play, curr_color):
    player = curr_player.discord_info
    valid = False
    message = "Play a card by picking the emoji corresponding to the card or click the 'joker' to draw a card." \
              "\nThe current card is {}".format(card_in_play)

    embed = discord.Embed(title="It is your turn!",
                          description=message,
                          color=card_color_into_code(curr_color))
    for card in range(len(curr_player.hand)):
        embed.add_field(name="\u200b", value=str(card_index[card] + ": " + str(curr_player.hand[card])), inline=False)
    embed.add_field(name="\u200b", value=str(card_index[len(card_index) - 1]) + ": Draw", inline=False)
    msg = await player.send(embed=embed)
    for card in range(len(curr_player.hand)):
        await msg.add_reaction(card_index[card])
    await msg.add_reaction(card_index[len(card_index) - 1])
    res = await ctx.wait_for("reaction_add", check=check_for_reaction(message))


    # # keeps asking the player for input until they give a valid input: "DRAW" or an index of a card in their hand
    # while not valid:
    #     try:
    #         action = input("What card do you want to play? 0-" + str(len(curr_player.hand) - 1) +
    #                        "\nor type 'DRAW' to draw a card\n")
    #         valid = action.upper() == "DRAW" or 0 <= int(action) < len(curr_player.hand)
    #     except ValueError:  # when the player inputs anything that is not "DRAW" or a number
    #         print("Not a valid input")
    #         print("The current card is {} and the current color is {}".format(card_in_play, curr_color))
    #         curr_player.print_hand()
    return ""

def check_for_reaction(message):
    for reaction in message.reactions:
        if reaction.count > 1:
            return True

# gets the index of next player based on the current index and if a reverse has been played
def get_next_player(player_list, index, reverse):
    return (index - 1) % len(player_list) if reverse else (index + 1) % len(player_list)


# changes the color based on the player's choice (used for WILD card)
def color_change(curr_color, index):
    while True:
        curr_color = input("What color do you want to change it to?: RED, YELLOW, GREEN, or BLUE\n").upper()
        if curr_color == "RED" or curr_color == "YELLOW" or curr_color == "GREEN" or curr_color == "BLUE":
            break
    print("Player {} changed the color to {}".format(index + 1, curr_color))


# deals with action cards
def handle_action_card(card, deck, p_list, reverse, index, next_player_index, curr_color):
    if card.value == "REVERSE":
        # reverse the cycle
        reverse = not reverse
        next_player_index = get_next_player(p_list, index, reverse)
    elif card.value == "+2":
        for i in range(2):
            deck.deal(p_list[next_player_index])
        # skips the next player
        next_player_index = get_next_player(p_list, next_player_index, reverse)
    elif card.value == "+4":
        for i in range(4):
            deck.deal(p_list[next_player_index])
        # skips the next player
        next_player_index = get_next_player(p_list, next_player_index, reverse)
        color_change(curr_color, index)
    elif card.value == "SKIP":
        # skips the next player
        next_player_index = get_next_player(p_list, next_player_index, reverse)
    elif card.value == "WILD":
        color_change(curr_color, index)


# converts a given color (red, yellow, green, or blue) into unicode for display
def card_color_into_code(curr_color):
    if curr_color == "RED":
        return discord.Colour.red()
    elif curr_color == "YELLOW":
        return discord.Colour.from_rgb(255, 255, 0)
    elif curr_color == "GREEN":
        return discord.Colour.green()
    else:
        return discord.Colour.blue()


# determines if there is a winner
def winner(player_list):
    for player in player_list:
        if len(player.hand) == 0:
            return True
    return False


class UNO(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("UNO is ready to go")

    # command to play UNO
    @commands.command()
    async def play(self, ctx):
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
        if len(users) > 0:
            await ctx.send("The players of this game are:")
            for user in users:
                await ctx.send(user.mention)

            # TODO: handle case where no one wants to play
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
            shuffle(player_list)
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
                # await ctx.send("{} choose a card to play or draw".format(curr_player.discord_info.mention))
                # get input from the player
                while True:
                    next_player_index = get_next_player(player_list, index, reverse)
                    action = await get_player_action(ctx, curr_player, card_in_play, curr_color)
                    if action.upper() == "DRAW":
                        deck.deal(curr_player)
                        card = card_in_play  # used to fix bug for drawing on the first turn
                        break
                    elif 0 <= int(action) < len(curr_player.hand):
                        card = curr_player.hand[int(action)]
                        # check if the card is playable
                        if card.can_play(card_in_play) or card.can_play_color(curr_color):
                            # plays the card
                            curr_player.hand.remove(card)
                            deck.discard.append(card)
                            # do special card actions
                            handle_action_card(card, deck, player_list, reverse, index, next_player_index, curr_color)
                            break  # end of player's turn, got a valid move
                        else:  # the player chose a card that is not playable based on the current card
                            print("This is not a valid card")
                            print("The current card is {} and the current color is {}".format(card_in_play, curr_color))
                            curr_player.print_hand()
                index = next_player_index
                curr_player = player_list[next_player_index]
                # used to change the color when a WILD card is played
                curr_color = card.color if card.color != "BLACK" else curr_color

            # displays the winner
            winner_index = 0
            while len(player_list[winner_index].hand) != 0 and winner_index < len(player_list):
                winner_index += 1
            print("The winner is Player", winner_index + 1)



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
